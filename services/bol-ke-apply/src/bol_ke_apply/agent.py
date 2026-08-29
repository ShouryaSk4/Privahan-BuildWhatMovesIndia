"""Conversational Agent for Bol Ke Apply (Module 6) powered by Google Gemini & RTO Knowledge Base.

Interprets citizen voice/text queries in English, Hindi, or Hinglish,
grounds responses in statutory MoRTH / RTO guidelines (Rule 32 CMVR, ADTT track rules, Zero-Form e-KYC),
and executes MCP platform tools:
- fetch_identity
- check_mismatch
- match_video
- whats_next
"""

import json
import logging
import os
import re

from bol_ke_apply.llm_client import get_llm_provider
from bol_ke_apply.server import check_mismatch, fetch_identity, match_video, whats_next

logger = logging.getLogger("bol_ke_apply_agent")

RTO_KNOWLEDGE_BASE = """
=== OFFICIAL MINISTRY OF ROAD TRANSPORT & HIGHWAYS (MoRTH) & RTO KNOWLEDGE BASE ===

1. STATUTORY FEES & TARIFF (RULE 32 OF CMVR - CENTRAL MOTOR VEHICLES RULES):
- Learner's Licence (LL) Application: Rs. 150
- LL Computerized Knowledge Test (STALL): Rs. 50
- Driving Licence (DL) Application: Rs. 200
- DL Automated Driving Test Track (ADTT) Fee: Rs. 300
- Form 7 Polycarbonate Smart Card Fee: Rs. 200
- Total Statutory Official Fee: Exactly Rs. 1,350 (No tout or extra middleman charges).

2. JOURNEY TIMELINES & RULES:
- Zero-Form Application: Demographic data is pulled directly from UIDAI Aadhaar e-KYC / DigiLocker. Fields typed: 0.
- Learner's Licence (LL) Validity: Valid for 6 months across India.
- Mandatory Practice Window: Minimum 30-day practice period required before citizen can book practical driving test slot.
- Processing Window: Approx 21 days from online submission to permanent digital licence.
- Physical Visit Guarantee: Only 1 physical visit required in the entire journey (to the automated driving test track).

3. AUTOMATED DRIVING TEST TRACK (ADTT) STANDARDS & MANEUVERS:
- Track 1 (8-Shape Track): Evaluates forward steering coordination, turn radius control, continuous lane keeping. Do not stop or touch boundary kerbs.
- Track 2 (Reverse S / Parallel Parking): Evaluates spatial estimation and reverse maneuvering into a standard bay within 3 minutes without touching side kerbs.
- Track 3 (Gradient / Hill Start): Tests clutch bite-point control on an 18-degree incline. Vehicle must stop at marker and accelerate forward without rolling back more than 6 inches (15 cm).
- Track 4 (Emergency Braking & Overtaking): Accelerate to 30 km/h and stop smoothly within marked sensor lines.

4. JURISDICTION & REJECTION PREVENTION:
- Aadhaar registered permanent address determines statutory RTO jurisdiction.
- Current device GPS location suggests convenience RTO. When they differ (e.g. students, recent movers), the citizen has the statutory right to choose either jurisdiction.
- Rejection Prevention: Cross-checks Aadhaar vs PAN records (name spelling, DOB) before submission to avoid RTO document rejection.

5. ELIGIBILITY:
- Age 18+ for Light Motor Vehicle (LMV - Cars).
- Age 16+ for Gearless 2-wheelers up to 50cc with parental consent.
"""

SYSTEM_PROMPT = f"""You are the official MoRTH AI Citizen Officer for 'बोल के अप्लाई' (Parivahan Seva).
Your role is to assist Indian citizens applying for their first-time driving licence or learning to drive.

Guidelines:
1. Speak warmly, respectfully, and clearly in the citizen's preferred language (Hindi, English, or Hinglish).
2. Answer queries accurately using the official RTO Knowledge Base provided below.
3. If the citizen asks to see their profile/Aadhaar/identity, check document rejection risk, find driving video lessons, or check application status, indicate the corresponding tool in your response.
4. Keep answers concise, helpful, and free of bureaucratic jargon.

{RTO_KNOWLEDGE_BASE}
"""


def _detect_language(text: str) -> str:
    """Detect whether input is Hindi (Devanagari), Hinglish, or English."""
    for ch in text:
        if "\u0900" <= ch <= "\u097f":
            return "hindi"

    hinglish_markers = [
        "kaise", "karo", "mera", "meri", "gadi", "gaadi", "peeche",
        "chadhai", "dhalan", "nahi", "hogi", "kya", "batao", "dikhao",
        "chhodna", "aath", "lagana", "swagat", "jana", "hai", "paise", "kitna"
    ]
    words = text.lower().split()
    if any(w in hinglish_markers for w in words):
        return "hinglish"

    return "english"


class BolKeApplyAgent:
    """Autonomous conversational driver for Bol Ke Apply powered by Google Gemini."""

    def __init__(self, provider_name: str | None = None):
        self.provider = get_llm_provider(provider_name or os.getenv("BOL_KE_APPLY_LLM_PROVIDER", "gemini"))

    def interact(
        self,
        message: str,
        applicant_id: str = "applicant_clean",
        journey_stage: str | None = None,
    ) -> dict:
        """Process a citizen voice utterance / message and trigger MCP tools as needed."""
        msg_lower = message.lower().strip()
        lang = _detect_language(message)

        tool_called = None
        tool_result = None
        tool_context = ""

        # 1. Intent: Journey status / what's next
        journey_keywords = [
            "status", "application", "stage", "journey", "next", "aage",
            "kahan", "kab tak", "progress", "स्टेटस", "आवेदन", "स्थिति", "कहां", "आगे"
        ]
        if any(kw in msg_lower for kw in journey_keywords):
            tool_called = "whats_next"
            tool_result = whats_next(applicant_id=applicant_id)
            tool_context = f"\n[Executed Tool whats_next]: Current Stage = {tool_result.get('current_stage')}, Next Step = {tool_result.get('next_action', {}).get('label')}, Certainty = {tool_result.get('certainty')}"

        # 2. Intent: Driving Academy / Video Match
        elif any(kw in msg_lower for kw in [
            "track", "turn", "parking", "hill", "clutch", "steering", "lane",
            "brake", "mirror", "slope", "dhalan", "chadhai", "stalling", "video",
            "lesson", "gaadi", "gadi", "रिवर्स", "क्लच", "स्टीयरिंग", "चढ़ाई", "ढलान", "आठ", "पार्किंग"
        ]):
            tool_called = "match_video"
            tool_result = match_video(
                applicant_id=applicant_id,
                query=message,
                journey_stage=journey_stage,
            )
            tool_context = f"\n[Executed Tool match_video]: Topic = {tool_result.get('topic')}, Confidence = {tool_result.get('confidence')}, Video ID = {tool_result.get('video_id')}"

        # 3. Intent: Rejection-Prevention Mismatch Check
        elif any(kw in msg_lower for kw in [
            "mismatch", "reject", "rejection", "pan", "discrepancy", "error",
            "check", "sahi hai", "गलती", "खारिज", "रिजेक्ट", "दस्तावेज"
        ]):
            tool_called = "check_mismatch"
            tool_result = check_mismatch(applicant_id=applicant_id)
            tool_context = f"\n[Executed Tool check_mismatch]: Clear to Submit = {tool_result.get('clear_to_submit')}, Mismatches = {tool_result.get('mismatches')}"

        # 4. Intent: Identity / Profile Fetch
        elif any(kw in msg_lower for kw in [
            "identity", "profile", "aadhaar", "digilocker", "who am i", "mera naam",
            "address", "pehchan", "आधार", "पहचान", "प्रोफाइल", "पता"
        ]) or "fetch" in msg_lower:
            tool_called = "fetch_identity"
            tool_result = fetch_identity(applicant_id=applicant_id)
            tool_context = f"\n[Executed Tool fetch_identity]: Name = {tool_result.get('name')}, DOB = {tool_result.get('dob')}, Address = {tool_result.get('address')}, Suggested RTO = {tool_result.get('gps_suggested_rto')}, Address Match = {tool_result.get('addresses_match')}"

        # Construct prompt for Gemini LLM
        prompt = f"""Citizen query ({lang}): "{message}"
Active Applicant ID: {applicant_id}
Current Journey Stage: {journey_stage or 'no_licence'}
{tool_context}

Respond directly to the citizen in natural {lang} using the RTO knowledge base and any tool results provided above. Keep your tone polite, formal yet approachable, and helpful."""

        reply = self.provider.generate_response(prompt, system_instruction=SYSTEM_PROMPT)

        # Clean markdown formatting if any excessive asterisks
        reply = reply.replace("**", "").strip()

        return {
            "reply": reply,
            "tool_called": tool_called,
            "tool_result": tool_result,
            "language": lang,
            "audio_url": self.provider.synthesize_speech(reply),
        }
