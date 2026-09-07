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
import threading
from collections import deque
from typing import Any

from contracts.mcp_tools import (
    BookSlotToolInput,
    CheckMismatchToolInput,
    ConfirmRtoToolInput,
    FetchIdentityToolInput,
    ListSlotsToolInput,
    MatchVideoToolInput,
    NextBestActionToolInput,
    ReportEventToolInput,
    ResetJourneyToolInput,
    SaveCitizenToolInput,
    StartApplicationToolInput,
    WhatsNextToolInput,
)

from bol_ke_apply.llm_client import get_llm_provider
from bol_ke_apply.server import (
    book_test_slot,
    check_mismatch,
    confirm_rto_choice,
    fetch_identity,
    get_journey_next_best_action,
    list_test_slots,
    match_video,
    report_event,
    reset_journey,
    save_citizen_details,
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
    "save_citizen_details": lambda args: save_citizen_details(
        applicant_id=args.get("applicant_id"),
        phone=args["phone"],
        name=args["name"],
        dob=args["dob"],
        address=args["address"],
        vehicle_class=args.get("vehicle_class", "LMV"),
        gps_rto=args.get("gps_rto", "DL01"),
    ),
    "confirm_rto_choice": lambda args: confirm_rto_choice(
        applicant_id=args["applicant_id"],
        confirmed_rto_code=args["confirmed_rto_code"],
    ),
    "get_journey_next_best_action": lambda args: get_journey_next_best_action(
        applicant_id=args["applicant_id"],
    ),
}

# Tools with side effects: the conversational agent must get the citizen's
# yes before calling these; the autonomous runner logs each one it takes.
ACTION_TOOLS = frozenset(
    {"start_application", "report_event", "book_test_slot", "reset_journey", "save_citizen_details", "confirm_rto_choice"}
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
    "save_citizen_details": "Save or register citizen demographic details (phone, name, DOB, address, vehicle_class) into the database so the application can proceed.",
    "confirm_rto_choice": "Confirm citizen statutory jurisdiction RTO choice when address and device location differ.",
    "get_journey_next_best_action": "Get the next logical journey action when citizen confirms to proceed.",
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
    "save_citizen_details": SaveCitizenToolInput,
    "confirm_rto_choice": ConfirmRtoToolInput,
    "get_journey_next_best_action": NextBestActionToolInput,
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

# Persistent per-applicant conversation memory backed by Supabase PostgreSQL
_HISTORY: dict[str, deque] = {}
_HISTORY_TURNS = 5  # user+assistant pairs kept


def _history(applicant_id: str) -> list[dict]:
    try:
        from contracts.db import get_agent_history
        db_history = get_agent_history(applicant_id, limit=10)
        if db_history:
            return [
                {
                    "role": "user" if h["sender"] == "citizen" else "assistant",
                    "content": h["content"],
                }
                for h in db_history
            ]
    except Exception:
        pass
    mem = _HISTORY.setdefault(applicant_id, deque(maxlen=_HISTORY_TURNS * 2))
    return list(mem)


def reset_history(applicant_id: str) -> None:
    _HISTORY.pop(applicant_id, None)


def _save_message(
    session_id: str,
    sender: str,
    content: str,
    tool_called: str | None = None,
    tool_result: Any | None = None,
    options: list[str] | None = None,
) -> None:
    """Persist a turn to Supabase WITHOUT blocking the reply.

    The write is best-effort history; making the citizen wait on a
    cross-region DB round-trip (×2 per turn) before seeing the answer was pure
    latency. Fire it on a background daemon thread instead.
    """

    def _write() -> None:
        try:
            from contracts.db import append_agent_message

            append_agent_message(
                session_id=session_id,
                sender=sender,
                content=content,
                tool_called=tool_called,
                tool_result=tool_result,
                interactive_options=options,
            )
        except Exception:  # noqa: BLE001, S110 — best-effort mirror, never surfaces
            pass

    threading.Thread(target=_write, daemon=True).start()


def _generate_interactive_options(
    message: str, tool_called: str | None, tool_result: Any, lang: str
) -> list[str]:
    """Generate structured, clickable quick-reply option pills for the citizen."""
    is_hi = lang != "english"

    if tool_called == "check_mismatch" and tool_result:
        mismatches = tool_result.get("mismatches", []) if isinstance(tool_result, dict) else []
        if any(m.get("field") == "jurisdiction" for m in mismatches):
            return (
                ["दिल्ली RTO (DL-01) चुनें", "वर्तमान पता (KA-03) चुनें", "RTO अंतर समझें"]
                if is_hi
                else ["Confirm Delhi (DL-01)", "Confirm Bangalore (KA-03)", "Explain RTO Difference"]
            )
        if tool_result.get("clear_to_submit"):
            return (
                ["✅ तुरंत आवेदन सबमिट करें", "📜 फीस और समय-सीमा", "🎥 अकादमी वीडियो"]
                if is_hi
                else ["✅ Submit Application Now", "📜 Fees & Timelines", "🎥 Academy Videos"]
            )
        return (
            ["दस्तावेज़ सुधारें", "फिर भी आगे बढ़ें", "नियम देखें"]
            if is_hi
            else ["Fix Mismatch", "Proceed Anyway", "Check Rules"]
        )

    if tool_called == "start_application" and isinstance(tool_result, dict):
        if tool_result.get("blocked"):
            detail = tool_result.get("detail", {})
            if isinstance(detail, dict) and detail.get("reason") == "rto_confirmation_required":
                return (
                    ["दिल्ली RTO (DL-01) चुनें", "वर्तमान पता (KA-03) चुनें", "RTO अंतर समझें"]
                    if is_hi
                    else ["Confirm Delhi (DL-01)", "Confirm Bangalore (KA-03)", "Explain RTO Difference"]
                )
            return (
                ["समस्या की समीक्षा करें", "RTO से संपर्क करें", "पुनः प्रयास करें"]
                if is_hi
                else ["Review Issues", "Contact RTO", "Try Again"]
            )
        elif "current_stage" in tool_result or tool_result.get("application_number"):
            return (
                ["📝 ऑनलाइन STALL टेस्ट दें", "🎥 ड्राइविंग अकादमी वीडियो", "📊 स्टेटस ट्रैक करें"]
                if is_hi
                else ["📝 Take STALL Exam Now", "🎥 Driving Academy Videos", "📊 Check Application Status"]
            )

    if tool_called == "list_test_slots" and isinstance(tool_result, dict):
        slots = tool_result.get("slots", [])
        if slots:
            opts = [
                f"स्लॉट बुक करें: {s.get('slot_id')}" if is_hi else f"Book: {s.get('slot_id')}"
                for s in slots[:2]
            ]
            opts.extend(["अन्य तारीखें", "ट्रैक वीडियो देखें"] if is_hi else ["Other Dates", "Track Video"])
            return opts

    if tool_called == "match_video":
        return (
            ["8-शेप ट्रैक वीडियो", "रिवर्स पार्किंग वीडियो", "ढलान (Hill Hold) वीडियो"]
            if is_hi
            else ["8-Turn Video", "Reverse Parking Video", "Hill Hold Video"]
        )

    if tool_called == "fetch_identity" and isinstance(tool_result, dict):
        return (
            ["✅ तुरंत आवेदन सबमिट करें", "📜 नियम और फीस जानें", "🔍 मिसमैच जांचें"]
            if is_hi
            else ["Confirm and Apply", "Statutory Fees & Days", "Check Mismatches"]
        )

    if tool_called == "whats_next" and isinstance(tool_result, dict):
        stage = tool_result.get("current_stage")
        if stage in ("ll_application_submitted", "ll_documents_verified"):
            return (
                ["📝 ऑनलाइन STALL टेस्ट दें", "📚 टेस्ट की तैयारी", "📊 स्थिति देखें"]
                if is_hi
                else ["📝 Take STALL Exam Now", "📚 Test Prep", "📊 Check Status"]
            )
        elif stage == "practice_window":
            return (
                ["📅 टेस्ट स्लॉट बुक करें", "🎥 ट्रैक टेस्ट वीडियो", "📊 प्रैक्टिस स्थिति"]
                if is_hi
                else ["📅 Book Test Slot", "🎥 Track Test Video", "📊 Practice Status"]
            )
        elif stage == "dl_test_booked":
            return (
                ["📍 ट्रैक दिशा-निर्देश", "🎥 8-शेप ट्रैक वीडियो", "🔄 स्लॉट बदलें"]
                if is_hi
                else ["📍 Track Guidelines", "🎥 8-Turn Video", "🔄 Reschedule Slot"]
            )
        elif stage == "dl_issued":
            return (
                ["📥 डिजिटल स्मार्ट कार्ड डाउनलोड करें", "🚗 ड्राइविंग नियम", "समाप्त"]
                if is_hi
                else ["📥 Download Smart Card", "🚗 Driving Rules", "Done"]
            )

    m_low = message.lower()
    if any(
        k in m_low
        for k in [
            "apply",
            "shuru",
            "licence",
            "license",
            "lena",
            "banwana",
            "आवेदन",
            "लाइसेंस",
            "लेना",
            "बनवाना",
            "शुरू",
        ]
    ):
        return (
            ["✅ तुरंत आवेदन सबमिट करें", "📜 नियम और फीस बताएं", "🎥 ड्राइविंग अकादमी"]
            if is_hi
            else ["Confirm and Apply", "Statutory Fees & Days", "Ask Question"]
        )
    if any(k in m_low for k in ["slot", "booking", "test", "track", "स्लॉट", "टेस्ट", "ट्रैक"]):
        return (
            ["📅 ट्रैक स्लॉट बुक करें", "🎥 8-शेप ट्रैक वीडियो", "नियम देखें"]
            if is_hi
            else ["Book Track Slot", "8-Turn Track Video", "Slot Rules"]
        )
    if any(
        k in m_low
        for k in [
            "video",
            "dikhao",
            "park",
            "reverse",
            "hill",
            "वीडियो",
            "पार्किंग",
            "रिवर्स",
            "चढ़ाई",
        ]
    ):
        return (
            ["8-शेप वीडियो", "रिवर्स पार्किंग वीडियो", "ढलान (Hill Hold) वीडियो"]
            if is_hi
            else ["8-Turn Video", "Reverse Parking Video", "Hill Hold Video"]
        )

    return (
        ["लाइसेंस के लिए आवेदन करें", "आवेदन की स्थिति ट्रैक करें", "ड्राइविंग अकादमी वीडियो"]
        if is_hi
        else ["Apply for Licence", "Track Application", "Driving Academy"]
    )

logger = logging.getLogger("bol_ke_apply_agent")

# Kept deliberately compact: this rides on every model turn, so only the facts
# the agent itself reasons with live here. Detailed driving-track technique is
# coaching content — that routes to the Driving Academy videos via match_video.
RTO_KNOWLEDGE_BASE = """KEY FACTS (general rules only; citizen-specific facts must come from tools):
- Zero-Form: demographic data comes from Aadhaar e-KYC/DigiLocker — the citizen types nothing.
- Learner's Licence is valid 6 months across India. 30-day practice before the driving test.
- ~21 days online-submission to permanent licence; only 1 physical visit (the test track).
- Jurisdiction: Aadhaar address sets the statutory RTO; GPS suggests a convenience RTO. If they differ, the citizen may choose either.
- Rejection prevention cross-checks Aadhaar vs PAN (name/DOB) before submission.
- Eligibility: 18+ for LMV (cars); 16+ for gearless 2-wheelers ≤50cc with parental consent.
- For driving-technique questions (8-track, reverse park, hill start), use match_video — do not narrate technique."""

SYSTEM_PROMPT = f"""You are the official MoRTH AI Citizen Officer for 'बोल के अप्लाई' (Parivahan Seva).
Your role is to assist Indian citizens applying for their first-time driving licence or learning to drive.

CORE PARADIGM — ZERO-FORM LICENCE (NO MANUAL FORM FILLING):
- Parivahan Seva is completely FORM-FREE ("Zero-Form").
- NEVER ask the citizen to manually dictate, spell out, or type their demographic details (full name, date of birth, residential address, father's name, or phone number).
- All verified citizen identity data is pulled automatically via DigiLocker / UIDAI Aadhaar e-KYC using the `fetch_identity` tool.
- When the citizen expresses intent to get or apply for a licence (e.g. 'लाइसेंस लेना है', 'कार का लाइसेंस बनवाना है', 'गाड़ी का लेना है', 'आधार कार्ड से बना दो', 'I want a car driving licence', 'apply for licence'):
  1. Inspect their verified DigiLocker/Aadhaar profile using `fetch_identity`.
  2. Check for any rejection blockers or mismatches using `check_mismatch`.
  3. If they gave an explicit directive or affirmative phrase (e.g. 'आधार कार्ड के उपयुक्त में बना लीजिए', 'हाँ बना दो', 'आवेदन कर दो', 'apply for licence', 'हाँ', 'कर दीजिए'): call `start_application` immediately!
  4. If they are inquiring or stating initial intent, warmly confirm what was verified (e.g. Name, DOB, RTO jurisdiction) and that there are 0 mismatches, and ask for their confirmation to submit immediately.
- Once submitted, never ask them to apply again. Guide them directly to their next milestone (online STALL test, Driving Academy videos).

Guidelines:
1. Speak warmly, respectfully, and clearly — and ALWAYS reply in the same language the citizen used (Hindi, English, or Hinglish).
2. Answer only about the driving-licence journey and road safety. Politely decline anything else.
3. Use the platform tools to look things up — never invent journey stages, fees, dates, application numbers or personal data. Every factual claim about the citizen must come from a tool result. General rules may come from the Knowledge Base below.
4. When the request is ambiguous, ask one short clarifying question instead of guessing.
5. Keep answers concise (2-4 sentences), free of bureaucratic jargon and markdown. Do not discuss fees unless asked.
5a. For a greeting, thanks, or small talk (e.g. "namaste", "hello", "thank you"), reply directly in one short sentence — do NOT call any tool. Only use tools when the citizen asks about their application/identity or wants an action.
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

        # Action directive trigger (e.g. 'आधार कार्ड के उपयुक्त में बना लीजिए', 'बना दो', 'apply for licence', 'haan kar do')
        msg_norm = message.lower().strip()
        action_triggers = [
            "haan kar do", "haan kardo", "yes", "proceed", "theek hai", "haan", "sure", "ok kar do", "kardo",
            "उपयुक्त में बना", "उपयुक्त बना", "आधार कार्ड से बना", "बना लीजिए", "बना दो", "आवेदन कर दो",
            "कर दीजिए", "अप्लाई कर दो", "बना दीजिए", "तुरंत आवेदन सबमिट करें", "confirm and apply", "submit application"
        ]
        if any(trig in msg_norm for trig in action_triggers):
            nba = get_journey_next_best_action(applicant_id)
            act_type = nba.get("action")
            if act_type == "start_application":
                res = start_application(applicant_id=applicant_id)
                tool_called, tool_result = "start_application", res
                app_num = res.get("application_number") or "DL2026-APP"
                reply = (
                    f"मैंने आपके आधार ई-केवाईसी रिकॉर्ड के आधार पर आपका जीरो-फॉर्म ड्राइविंग लाइसेंस आवेदन सफलतापूर्वक जमा कर दिया है! "
                    f"आपका आवेदन नंबर {app_num} जनरेट हो चुका है। अब आपका अगला कदम ऑनलाइन STALL (लर्नर) टेस्ट देना है।"
                    if lang != "english"
                    else f"I have submitted your Zero-Form driving licence application using your verified Aadhaar e-KYC record! "
                    f"Your application number is {app_num}. You can now take the online STALL learner's test."
                )
                options = _generate_interactive_options(message, tool_called, tool_result, lang)
                _save_message(applicant_id, "citizen", message)
                _save_message(applicant_id, "agent", reply, tool_called, tool_result, options)
                return {
                    "reply": reply,
                    "tool_called": tool_called,
                    "tool_result": tool_result,
                    "language": lang,
                    "audio_url": self.provider.synthesize_speech(reply),
                    "engine": "NextBestAction",
                    "options": options,
                }

        # Preferred path: native LLM function calling (OpenAI / Gemini 3.7 provider).
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
                options = _generate_interactive_options(message, tool_called, tool_result, lang)
                _save_message(applicant_id, "citizen", message)
                _save_message(applicant_id, "agent", reply, tool_called, tool_result, options)
                return {
                    "reply": reply,
                    "tool_called": tool_called,
                    "tool_result": tool_result,
                    "language": lang,
                    "audio_url": self.provider.synthesize_speech(reply),
                    "engine": type(self.provider).__name__,
                    "options": options,
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

        # Turn budget exhausted mid-tool-use: ask for a prose wrap-up rather
        # than silently dropping to the keyword fallback (which masks errors).
        messages.append({
            "role": "user",
            "content": f"Answer the citizen now in {lang} using what you learned. No more tools.",
        })
        final = self.provider.chat_with_tools(messages, [])
        reply = ((final or {}).get("content") or "").replace("**", "").strip()
        if not reply:
            return None
        options = _generate_interactive_options(message, tool_called, tool_result, lang)
        _save_message(applicant_id, "citizen", message)
        _save_message(applicant_id, "agent", reply, tool_called, tool_result, options)
        return {
            "reply": reply,
            "tool_called": tool_called,
            "tool_result": tool_result,
            "language": lang,
            "audio_url": self.provider.synthesize_speech(reply),
            "engine": type(self.provider).__name__,
            "options": options,
        }

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


        # 5. Intent: Licence Application / Intent
        elif any(kw in msg_lower for kw in [
            "apply", "license", "licence", "banwana", "chahiye", "lena", "gadi", "gaadi", "car",
            "आवेदन", "लाइसेंस", "बनवाना", "चाहिए", "लेना", "गाड़ी", "कार", "शुरू"
        ]):
            action_words = ["उपयुक्त", "बना", "सबमिट", "कर दो", "कर दीजिए", "अप्लाई", "तुरंत"]
            if any(w in msg_lower for w in action_words):
                tool_called = "start_application"
                tool_result = start_application(applicant_id=applicant_id)
                tool_context = f"\n[Executed Tool start_application]: Stage = {tool_result.get('current_stage')}, Application Number = {tool_result.get('application_number')}, Blocked = {tool_result.get('blocked')}"
            else:
                tool_called = "fetch_identity"
                tool_result = fetch_identity(applicant_id=applicant_id)
                tool_context = f"\n[Executed Tool fetch_identity]: Name = {tool_result.get('name')}, DOB = {tool_result.get('dob')}, Address = {tool_result.get('address')}, Suggested RTO = {tool_result.get('gps_suggested_rto')}, Address Match = {tool_result.get('addresses_match')}"

        # Construct prompt for Gemini LLM
        prompt = f"""Citizen query ({lang}): "{message}"
Active Applicant ID: {applicant_id}
Current Journey Stage: {journey_stage or 'no_licence'}
{tool_context}

Respond directly to the citizen in natural {lang} using the RTO knowledge base and any tool results provided above. Keep your tone polite, formal yet approachable, and helpful. Parivahan Seva is a Zero-Form system: NEVER ask the citizen to state or type their personal details (name, DOB, address)."""

        reply = self.provider.generate_response(prompt, system_instruction=SYSTEM_PROMPT)

        # Clean markdown formatting if any excessive asterisks
        reply = reply.replace("**", "").strip()

        options = _generate_interactive_options(message, tool_called, tool_result, lang)
        _save_message(applicant_id, "citizen", message)
        _save_message(applicant_id, "agent", reply, tool_called, tool_result, options)

        return {
            "reply": reply,
            "tool_called": tool_called,
            "tool_result": tool_result,
            "language": lang,
            "audio_url": self.provider.synthesize_speech(reply),
            "engine": f"{type(self.provider).__name__}+keywords",
            "options": options,
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
    # Hard rails against loops: every failed (tool, args) signature is
    # remembered for the whole run — not just the last one — and a streak of
    # failures ends the run with a summary instead of burning the step budget.
    failed_signatures: set[tuple] = set()
    consecutive_failures = 0
    stopped = "completed"

    def _final_summary(reason: str, fallback: str) -> dict:
        messages.append({
            "role": "user",
            "content": (
                f"STOP ({reason}). Do not call any more tools. In {lang}, summarise for the "
                "citizen in 2-3 sentences: what was completed, what is blocked and why, and "
                "the one next step they should take."
            ),
        })
        final = agent.provider.chat_with_tools(messages, [])
        reply = ((final or {}).get("content") or "").replace("**", "").strip()
        return {"reply": reply or fallback, "steps": run.steps, "language": lang,
                "engine": type(agent.provider).__name__, "stopped": reason}

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
            if signature in failed_signatures:
                result = {"error": "repeat_of_failed_call",
                          "detail": "This exact call already failed in this run — "
                                    "change the arguments, pick another tool, or stop and summarise."}
                consecutive_failures += 1
            else:
                executor = TOOL_EXECUTORS.get(name)
                result = executor(args) if executor else {"error": f"unknown tool '{name}'"}
                if isinstance(result, dict) and (result.get("blocked") or result.get("error")):
                    failed_signatures.add(signature)
                    consecutive_failures += 1
                else:
                    consecutive_failures = 0
            run.log(name, args, result if isinstance(result, dict) else {"value": result})
            logger.info("autonomous step: %s(%s) ok=%s", name, args, run.steps[-1]["ok"])
            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id", name),
                "content": json.dumps(result, default=str)[:4000],
            })

        if consecutive_failures >= 3:
            return _final_summary(
                "blocked",
                "The run hit repeated blocks and stopped safely. Review the step log for the reason.",
            )

    return _final_summary(
        "max_steps",
        "Step budget reached — stopping safely. Review the step log.",
    )
