"""Conversational Agent for Bol Ke Apply (Module 6).

Drives the voice/conversational front door by interpreting citizen utterances
(in English, Hindi, or Hinglish) and delegating to the official MCP tools:
- fetch_identity
- check_mismatch
- match_video

Does NOT stub Module 2 journey-state tools.
"""

import logging
import os

from bol_ke_apply.llm_client import get_llm_provider
from bol_ke_apply.server import check_mismatch, fetch_identity, match_video

logger = logging.getLogger("bol_ke_apply_agent")


def _detect_language(text: str) -> str:
    """Detect whether input is Hindi (Devanagari), Hinglish, or English."""
    # Check for Devanagari Unicode range
    for ch in text:
        if "\u0900" <= ch <= "\u097f":
            return "hindi"

    hinglish_markers = [
        "kaise",
        "karo",
        "mera",
        "meri",
        "gadi",
        "gaadi",
        "peeche",
        "chadhai",
        "dhalan",
        "nahi",
        "hogi",
        "kya",
        "batao",
        "dikhao",
        "chhodna",
        "aath",
        "lagana",
        "swagat",
    ]
    words = text.lower().split()
    if any(w in hinglish_markers for w in words):
        return "hinglish"

    return "english"


class BolKeApplyAgent:
    """Autonomous conversational driver for Bol Ke Apply."""

    def __init__(self, provider_name: str | None = None):
        self.provider = get_llm_provider(provider_name or os.getenv("BOL_KE_APPLY_LLM_PROVIDER", "mock"))

    def interact(
        self,
        message: str,
        applicant_id: str = "applicant_clean",
        journey_stage: str | None = None,
    ) -> dict:
        """Process a citizen voice utterance / message and trigger MCP tools as needed."""
        msg_lower = message.lower()
        lang = _detect_language(message)

        # 1. Intent: Driving Academy / Video Match
        driving_academy_keywords = [
            "track",
            "turn",
            "parking",
            "hill",
            "clutch",
            "steering",
            "lane",
            "brake",
            "mirror",
            "slope",
            "dhalan",
            "chadhai",
            "stalling",
            "video",
            "lesson",
            "gaadi",
            "gadi",
            "रिवर्स",
            "क्लच",
            "स्टीयरिंग",
            "चढ़ाई",
            "ढलान",
            "आठ",
            "पार्किंग",
        ]
        if any(kw in msg_lower for kw in driving_academy_keywords):
            result = match_video(
                applicant_id=applicant_id,
                query=message,
                journey_stage=journey_stage,
            )
            if lang == "hindi":
                reply = (
                    f"ड्राइविंग अकैडमी में आपके लिए वीडियो मिला है: '{result.get('topic')}'। "
                    f"कॉन्फिडेंस: {int(result.get('confidence', 0) * 100)}%। यह वीडियो आपको सही तकनीक सिखाएगा।"
                )
            elif lang == "hinglish":
                reply = (
                    f"Aapke sawaal ke liye Driving Academy ka lesson mila: '{result.get('topic')}'. "
                    f"Confidence: {int(result.get('confidence', 0) * 100)}%. Yeh video aapko practical test clear karne me help karega."
                )
            else:
                reply = (
                    f"I found a Driving Academy lesson for you on '{result.get('topic')}'. "
                    f"Confidence score: {result.get('confidence')}. Check out the video clip for technique details."
                )
            return {
                "reply": reply,
                "tool_called": "match_video",
                "tool_result": result,
                "language": lang,
                "audio_url": self.provider.synthesize_speech(reply),
            }

        # 2. Intent: Rejection-Prevention Mismatch Check
        mismatch_keywords = [
            "mismatch",
            "reject",
            "rejection",
            "pan",
            "discrepancy",
            "document",
            "error",
            "check",
            "sahi hai",
            "गलती",
            "खारिज",
            "रिजेक्ट",
            "चेक",
            "दस्तावेज",
        ]
        if any(kw in msg_lower for kw in mismatch_keywords):
            result = check_mismatch(applicant_id=applicant_id)
            clear = result.get("clear_to_submit", False)
            mismatches = result.get("mismatches", [])

            if clear:
                if lang == "hindi":
                    reply = "बधाई हो! आपके सभी पहचान दस्तावेज पूरी तरह सही हैं और कोई मिसमैच नहीं मिला। आप आवेदन जमा कर सकते हैं।"
                elif lang == "hinglish":
                    reply = "Good news! Aapke saare documents verified hain aur koi rejection risk nahi hai. Aap form submit kar sakte hain."
                else:
                    reply = "All clear! No document mismatches detected. Your profile is ready for licence application submission."
            else:
                issues_summary = "; ".join(f"{m.get('field')}: {m.get('issue')}" for m in mismatches)
                if lang == "hindi":
                    reply = f"सावधान: आपके दस्तावेजों में विसंगतियां हैं: {issues_summary}। कृपया इन्हें ठीक करें।"
                elif lang == "hinglish":
                    reply = f"Attention: Aapke documents me discrepancies mili hain: {issues_summary}. Form reject hone se bachane ke liye inhe pehle update karein."
                else:
                    reply = f"Attention: Discrepancies detected that could risk RTO rejection: {issues_summary}."

            return {
                "reply": reply,
                "tool_called": "check_mismatch",
                "tool_result": result,
                "language": lang,
                "audio_url": self.provider.synthesize_speech(reply),
            }

        # 3. Intent: Identity / Profile Fetch
        identity_keywords = [
            "identity",
            "profile",
            "aadhaar",
            "digilocker",
            "who am i",
            "mera naam",
            "address",
            "pehchan",
            "आधार",
            "पहचान",
            "प्रोफाइल",
            "पता",
        ]
        if any(kw in msg_lower for kw in identity_keywords) or "fetch" in msg_lower:
            result = fetch_identity(applicant_id=applicant_id)
            name = result.get("name", "Citizen")
            rto = result.get("gps_suggested_rto", "Local RTO")
            match_status = result.get("addresses_match", True)

            if lang == "hindi":
                loc_note = (
                    f" आपका निकटतम आरटीओ {rto} है।"
                    if match_status
                    else f" ध्यान दें: आपका आधार पता और वर्तमान स्थान ({rto}) अलग-अलग राज्यों में हैं।"
                )
                reply = f"नमस्ते {name}! आपका डिजिलॉकर आधार प्रोफाइल प्राप्त हो गया है।{loc_note}"
            elif lang == "hinglish":
                loc_note = (
                    f" Aapka nearest suggested RTO {rto} hai."
                    if match_status
                    else f" Note: Aapka Aadhaar jurisdiction aur current device location ({rto}) alag hain."
                )
                reply = f"Namaste {name}! Aapka DigiLocker verified profile fetch ho gaya hai.{loc_note}"
            else:
                loc_note = (
                    f" Your suggested RTO is {rto}."
                    if match_status
                    else f" Note: Your legal Aadhaar jurisdiction and device location ({rto}) disagree."
                )
                reply = f"Hello {name}, your DigiLocker verified profile has been pulled successfully.{loc_note}"

            return {
                "reply": reply,
                "tool_called": "fetch_identity",
                "tool_result": result,
                "language": lang,
                "audio_url": self.provider.synthesize_speech(reply),
            }

        # 4. Default Greeting / General Assistance
        if lang == "hindi":
            reply = "नमस्ते! मैं 'बोल के अप्लाई' सहायक हूँ। आप बोलकर अपनी पहचान जांच सकते हैं, दस्तावेजों का मिसमैच चेक कर सकते हैं या ड्राइविंग टेस्ट के वीडियो देख सकते हैं।"
        elif lang == "hinglish":
            reply = "Namaste! Mai 'Bol Ke Apply' voice assistant hoon. Aap bol kar apna Aadhaar profile fetch kar sakte hain, document rejection check kar sakte hain, ya driving test ke tips pooch sakte hain."
        else:
            reply = "Hello! Welcome to Bol Ke Apply. You can speak with me to verify your identity, perform rejection-prevention checks, or ask for driving test technique videos."

        return {
            "reply": reply,
            "tool_called": None,
            "tool_result": None,
            "language": lang,
            "audio_url": self.provider.synthesize_speech(reply),
        }
