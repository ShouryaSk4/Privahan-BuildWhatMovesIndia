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
from collections import deque

from contracts.mcp_tools import (
    BookSlotToolInput,
    CheckMismatchToolInput,
    FetchIdentityToolInput,
    ListSlotsToolInput,
    MatchVideoToolInput,
    ReportEventToolInput,
    ResetJourneyToolInput,
    StartApplicationToolInput,
    WhatsNextToolInput,
)

from bol_ke_apply.llm_client import get_llm_provider
from bol_ke_apply.server import (
    book_test_slot,
    check_mismatch,
    fetch_identity,
    list_test_slots,
    match_video,
    report_event,
    reset_journey,
    start_application,
    sync_status,
    whats_next,
)

# Native function-calling tool specs, generated from the shared Pydantic
# contracts (packages/contracts/contracts/mcp_tools.py) — the single source of
# truth now also feeds the LLM, so tool schemas cannot drift from the platform.
TOOL_EXECUTORS = {
    "fetch_identity": lambda args: fetch_identity(applicant_id=args["applicant_id"]),
    "check_mismatch": lambda args: check_mismatch(applicant_id=args["applicant_id"]),
    "match_video": lambda args: match_video(
        applicant_id=args["applicant_id"],
        query=args["query"],
        journey_stage=args.get("journey_stage"),
    ),
    "whats_next": lambda args: whats_next(applicant_id=args["applicant_id"]),
    # -- action tools (the autonomous half) --
    "start_application": lambda args: start_application(
        applicant_id=args["applicant_id"],
        confirmed_rto_code=args.get("confirmed_rto_code"),
    ),
    "report_event": lambda args: report_event(
        applicant_id=args["applicant_id"], event=args["event"]
    ),
    "list_test_slots": lambda args: list_test_slots(
        applicant_id=args["applicant_id"], rto_code=args.get("rto_code")
    ),
    "book_test_slot": lambda args: book_test_slot(
        applicant_id=args["applicant_id"], slot_id=args["slot_id"]
    ),
    "sync_status": lambda args: sync_status(applicant_id=args["applicant_id"]),
    "reset_journey": lambda args: reset_journey(applicant_id=args["applicant_id"]),
}

# Tools with side effects: the conversational agent must get the citizen's
# yes before calling these; the autonomous runner logs each one it takes.
ACTION_TOOLS = frozenset(
    {"start_application", "report_event", "book_test_slot", "reset_journey"}
)

_TOOL_DESCRIPTIONS = {
    "fetch_identity": "Fetch the citizen's verified DigiLocker/Aadhaar e-KYC profile (Module 3).",
    "check_mismatch": "Rejection-prevention cross-check of Aadhaar vs PAN records; severity 'error' blocks, 'warning' advises (Module 3).",
    "match_video": "Match a driving difficulty or manoeuvre question to a Driving Academy lesson video (Module 4).",
    "whats_next": "Get the citizen's current journey stage, next action and certainty (cost/days/visits) (Module 2).",
    "start_application": "Submit the Zero-Form LL application. If blocked with rto_confirmation_required, ask the citizen to choose and retry with confirmed_rto_code ('aadhaar_jurisdiction' or the GPS RTO code). If blocked with rejection_prevention, relay the mismatches and fixes — do not retry.",
    "report_event": "Advance the journey (e.g. event='begin_practice' after the LL is issued).",
    "list_test_slots": "List available automated driving-test slots so the citizen can pick one.",
    "book_test_slot": "Book a specific driving-test slot AFTER the citizen confirmed it.",
    "sync_status": "Refresh the journey from the government registry and return the updated state.",
    "reset_journey": "DEMO ONLY, destructive: forget this journey. Only on explicit citizen request.",
}

_TOOL_INPUTS = {
    "fetch_identity": FetchIdentityToolInput,
    "check_mismatch": CheckMismatchToolInput,
    "match_video": MatchVideoToolInput,
    "whats_next": WhatsNextToolInput,
    "start_application": StartApplicationToolInput,
    "report_event": ReportEventToolInput,
    "list_test_slots": ListSlotsToolInput,
    "book_test_slot": BookSlotToolInput,
    "sync_status": ResetJourneyToolInput,
    "reset_journey": ResetJourneyToolInput,
}


def build_tool_specs() -> list[dict]:
    specs = []
    for name, model in _TOOL_INPUTS.items():
        schema = model.model_json_schema()
        schema.pop("title", None)
        for prop in schema.get("properties", {}).values():
            prop.pop("title", None)
        specs.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": _TOOL_DESCRIPTIONS[name],
                    "parameters": schema,
                },
            }
        )
    return specs


TOOL_SPECS = build_tool_specs()

# Short per-applicant conversation memory (in-process, mirrors the service's
# demo scope; a durable store can replace this without changing the interface).
_HISTORY: dict[str, deque] = {}
_HISTORY_TURNS = 5  # user+assistant pairs kept


def _history(applicant_id: str) -> deque:
    return _HISTORY.setdefault(applicant_id, deque(maxlen=_HISTORY_TURNS * 2))


def reset_history(applicant_id: str) -> None:
    _HISTORY.pop(applicant_id, None)

logger = logging.getLogger("bol_ke_apply_agent")

RTO_KNOWLEDGE_BASE = """
=== OFFICIAL MINISTRY OF ROAD TRANSPORT & HIGHWAYS (MoRTH) & RTO KNOWLEDGE BASE ===

1. JOURNEY TIMELINES & RULES:
- Zero-Form Application: Demographic data is pulled directly from UIDAI Aadhaar e-KYC / DigiLocker. Fields typed: 0.
- Learner's Licence (LL) Validity: Valid for 6 months across India.
- Mandatory Practice Window: Minimum 30-day practice period required before citizen can book practical driving test slot.
- Processing Window: Approx 21 days from online submission to permanent digital licence.
- Physical Visit Guarantee: Only 1 physical visit required in the entire journey (to the automated driving test track).

2. AUTOMATED DRIVING TEST TRACK (ADTT) STANDARDS & MANEUVERS:
- Track 1 (8-Shape Track): Evaluates forward steering coordination, turn radius control, continuous lane keeping. Do not stop or touch boundary kerbs.
- Track 2 (Reverse S / Parallel Parking): Evaluates spatial estimation and reverse maneuvering into a standard bay within 3 minutes without touching side kerbs.
- Track 3 (Gradient / Hill Start): Tests clutch bite-point control on an 18-degree incline. Vehicle must stop at marker and accelerate forward without rolling back more than 6 inches (15 cm).
- Track 4 (Emergency Braking & Overtaking): Accelerate to 30 km/h and stop smoothly within marked sensor lines.

3. JURISDICTION & REJECTION PREVENTION:
- Aadhaar registered permanent address determines statutory RTO jurisdiction.
- Current device GPS location suggests convenience RTO. When they differ (e.g. students, recent movers), the citizen has the statutory right to choose either jurisdiction.
- Rejection Prevention: Cross-checks Aadhaar vs PAN records (name spelling, DOB) before submission to avoid RTO document rejection.

4. ELIGIBILITY:
- Age 18+ for Light Motor Vehicle (LMV - Cars).
- Age 16+ for Gearless 2-wheelers up to 50cc with parental consent.
"""

SYSTEM_PROMPT = f"""You are the official MoRTH AI Citizen Officer for 'बोल के अप्लाई' (Parivahan Seva).
Your role is to assist Indian citizens applying for their first-time driving licence or learning to drive.

Guidelines:
1. Speak warmly, respectfully, and clearly — and ALWAYS reply in the same language the citizen used (Hindi, English, or Hinglish).
2. Answer only about the driving-licence journey and road safety. Politely decline anything else.
3. Use the platform tools to look things up — never invent journey stages, fees, dates, application numbers or personal data. Every factual claim about the citizen must come from a tool result. General rules may come from the Knowledge Base below.
4. When the request is ambiguous, ask one short clarifying question instead of guessing.
5. Keep answers concise (2-4 sentences), free of bureaucratic jargon and markdown. Do not discuss fees unless asked.
6. You can ACT, not just answer: submitting the application, advancing stages, listing and
   booking test slots, syncing the registry. Policy for actions:
   - Before any consequential action (start_application, book_test_slot, report_event,
     reset_journey), state what you are about to do and get the citizen's clear "yes" in
     THIS conversation first. A confirmation earlier in the history counts.
   - If a tool returns blocked with rto_confirmation_required, present both RTO options and
     ask the citizen to choose; retry only with their chosen confirmed_rto_code.
   - If blocked with rejection_prevention, relay each mismatch and its fix. Never retry past it.
   - After an action, confirm what happened using the tool result (stage, application number).
   - reset_journey only when the citizen explicitly asks to start over.

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
        self.provider = get_llm_provider(provider_name)

    def interact(
        self,
        message: str,
        applicant_id: str = "applicant_clean",
        journey_stage: str | None = None,
    ) -> dict:
        """Process a citizen voice utterance / message and trigger MCP tools as needed."""
        lang = _detect_language(message)

        # Safety gate (free moderation endpoint; no-op for providers without it).
        if self.provider.moderate(message):
            refusal = {
                "hindi": "क्षमा करें, मैं इस विषय पर सहायता नहीं कर सकता। कृपया ड्राइविंग लाइसेंस संबंधित प्रश्न पूछें।",
                "hinglish": "Maaf kijiye, main is vishay par madad nahi kar sakta. Kripya driving licence se juda sawaal poochhein.",
            }.get(lang, "Sorry, I can't help with that. Please ask about your driving licence journey.")
            return {
                "reply": refusal,
                "tool_called": None,
                "tool_result": None,
                "language": lang,
                "audio_url": None,
                "engine": "moderation",
            }

        # Preferred path: native LLM function calling (OpenAI provider).
        llm_turn = self._interact_with_tools(message, applicant_id, journey_stage, lang)
        if llm_turn is not None:
            return llm_turn

        return self._interact_keyword(message, applicant_id, journey_stage, lang)

    def _interact_with_tools(
        self, message: str, applicant_id: str, journey_stage: str | None, lang: str
    ) -> dict | None:
        """Multi-turn tool-calling loop. Returns None when the provider can't do it."""
        history = _history(applicant_id)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *list(history),
            {
                "role": "user",
                "content": (
                    f"[applicant_id={applicant_id} · journey_stage={journey_stage or 'no_licence'} "
                    f"· language={lang}]\n{message}"
                ),
            },
        ]
        tool_called = None
        tool_result = None

        for _ in range(6):  # up to 6 model turns: plan -> act -> observe -> reply
            assistant = self.provider.chat_with_tools(messages, TOOL_SPECS)
            if assistant is None:
                return None  # provider unsupported / no key / API error → fallback

            tool_calls = assistant.get("tool_calls") or []
            if not tool_calls:
                reply = (assistant.get("content") or "").replace("**", "").strip()
                if not reply:
                    return None
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": reply})
                return {
                    "reply": reply,
                    "tool_called": tool_called,
                    "tool_result": tool_result,
                    "language": lang,
                    "audio_url": self.provider.synthesize_speech(reply),
                    "engine": type(self.provider).__name__,
                }

            messages.append(assistant)
            for call in tool_calls:
                fn = call.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                args.setdefault("applicant_id", applicant_id)
                if name == "match_video":
                    args.setdefault("query", message)
                    args.setdefault("journey_stage", journey_stage)
                executor = TOOL_EXECUTORS.get(name)
                result = executor(args) if executor else {"error": f"unknown tool '{name}'"}
                if executor:
                    tool_called, tool_result = name, result
                logger.info("bol-ke-apply tool call: %s(%s)", name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id", name),
                        "content": json.dumps(result, default=str)[:4000],
                    }
                )
        return None  # model kept calling tools without answering → fallback

    def _interact_keyword(
        self, message: str, applicant_id: str, journey_stage: str | None, lang: str
    ) -> dict:
        """Keyword-routed fallback: works offline and with providers lacking tool support."""
        msg_lower = message.lower().strip()

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
            "engine": f"{type(self.provider).__name__}+keywords",
        }


AUTONOMY_PROMPT = SYSTEM_PROMPT + """

AUTONOMOUS RUN MODE:
You are executing a goal on the citizen's behalf; they have already consented to this run.
Work step by step with tools: check state first (whats_next), act, observe, continue.
Rules:
- Move the journey forward only as far as the tools allow. When a step needs something only
  the citizen or the RTO can do (a choice you were not given, a physical test, a blocked
  mismatch), STOP and summarise instead of guessing.
- rto_confirmation_required: if the goal names a jurisdiction preference use it, otherwise stop
  and report both options.
- rejection_prevention: stop and report the fixes. Never work around a block.
- Never call reset_journey unless the goal explicitly says to reset/start over.
- Do not repeat a tool call that just failed with the same arguments.
When done (or stopped), reply with a short summary of what you did and what comes next.
"""


class AutonomousRun:
    """Result of a goal-directed run: every step is logged for audit."""

    def __init__(self):
        self.steps: list[dict] = []

    def log(self, name: str, args: dict, result: dict) -> None:
        self.steps.append({
            "tool": name,
            "args": args,
            "ok": not (isinstance(result, dict) and (result.get("blocked") or result.get("error"))),
            "result": result,
        })


def run_goal(
    agent: "BolKeApplyAgent",
    goal: str,
    applicant_id: str,
    max_steps: int = 12,
) -> dict:
    """Plan/act/observe loop: the agent pursues a goal with the full tool belt.

    Server-side autonomy with hard rails: a step budget, no verbatim retries of
    failing calls, and an auditable step log in the response.
    """
    lang = _detect_language(goal)
    if agent.provider.moderate(goal):
        return {"reply": "This goal cannot be processed.", "steps": [], "language": lang,
                "engine": "moderation", "stopped": "moderated"}

    run = AutonomousRun()
    messages = [
        {"role": "system", "content": AUTONOMY_PROMPT},
        {"role": "user", "content": f"[applicant_id={applicant_id} · language={lang}]\nGOAL: {goal}"},
    ]
    last_failed: tuple | None = None
    stopped = "completed"

    for _ in range(max_steps):
        assistant = agent.provider.chat_with_tools(messages, TOOL_SPECS)
        if assistant is None:
            return {"reply": "Autonomous mode needs a tool-calling provider — set OPENAI_API_KEY.",
                    "steps": run.steps, "language": lang, "engine": "unavailable",
                    "stopped": "no_provider"}

        tool_calls = assistant.get("tool_calls") or []
        if not tool_calls:
            reply = (assistant.get("content") or "").replace("**", "").strip()
            return {"reply": reply or "Run finished.", "steps": run.steps, "language": lang,
                    "engine": type(agent.provider).__name__, "stopped": stopped}

        messages.append(assistant)
        for call in tool_calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            args.setdefault("applicant_id", applicant_id)

            signature = (name, json.dumps(args, sort_keys=True))
            if signature == last_failed:
                result = {"error": "repeat_of_failed_call",
                          "detail": "Same call just failed — change approach or stop."}
            else:
                executor = TOOL_EXECUTORS.get(name)
                result = executor(args) if executor else {"error": f"unknown tool '{name}'"}
                if isinstance(result, dict) and (result.get("blocked") or result.get("error")):
                    last_failed = signature
                else:
                    last_failed = None
            run.log(name, args, result if isinstance(result, dict) else {"value": result})
            logger.info("autonomous step: %s(%s) ok=%s", name, args, run.steps[-1]["ok"])
            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id", name),
                "content": json.dumps(result, default=str)[:4000],
            })

    return {"reply": "Step budget reached — stopping safely. Review the step log.",
            "steps": run.steps, "language": lang,
            "engine": type(agent.provider).__name__, "stopped": "max_steps"}
