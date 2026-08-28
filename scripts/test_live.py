"""Live end-to-end demonstration script querying all running Parivahan MVP services.

Verifies Module 3 (Port 8003), Module 4 (Port 8004), and Module 6 (Port 8006).
"""

import sys

import httpx

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


def banner(text: str):
    print("\n" + "=" * 65)
    print(f" {text}")
    print("=" * 65)


def run_demo():
    print("\n[STARTING LIVE INTEGRATION DEMONSTRATION]")

    # 1. Module 3 — Identity & Document Service
    banner("1. MODULE 3 (PORT 8003) — ZERO-FORM IDENTITY & REJECTION PREVENTION")
    with httpx.Client(base_url="http://127.0.0.1:8003", timeout=5.0) as client:
        personas = client.get("/identity/personas").json()
        print(f"[*] Available Test Personas: {personas}\n")

        clean = client.get("/identity/fetch/applicant_clean").json()
        print("[*] Clean Applicant Fetch (applicant_clean):")
        print(f"    Name: {clean['name']}")
        print(f"    DOB: {clean['dob']} (Age: {clean['age']}y - Eligible: {clean['age_eligible']})")
        print(f"    Address: {clean['address']}")
        print(f"    Jurisdiction RTO: {clean['aadhaar_registered_address']}")
        print(f"    GPS Suggested RTO: {clean['gps_suggested_rto']}")
        print(f"    Addresses Match: {clean['addresses_match']}\n")

        student = client.get("/identity/fetch/applicant_student_mover?gps_suggested_rto=KA-51%20Electronic%20City").json()
        print("[*] Student Mover Scenario (applicant_student_mover):")
        print(f"    Current GPS Location Suggests: {student['gps_suggested_rto']}")
        print(f"    Legal Aadhaar Jurisdiction: {student['aadhaar_registered_address']}")
        print(f"    Disagreement Surfaced: Addresses Match = {student['addresses_match']}\n")

        pan_mis = client.get("/identity/mismatch-check/applicant_pan_name_mismatch").json()
        print("[*] Rejection Prevention Check (applicant_pan_name_mismatch):")
        print(f"    Clear to Submit: {pan_mis['clear_to_submit']}")
        for m in pan_mis["mismatches"]:
            print(f"    - [{m['severity'].upper()}] Field '{m['field']}': {m['issue']}")
            print(f"      Suggested Fix: {m['suggested_fix']}\n")

        minor = client.get("/identity/mismatch-check/applicant_minor").json()
        print("[*] Underage Citizen Check (applicant_minor - 17y):")
        print(f"    Clear to Submit: {minor['clear_to_submit']}")
        for m in minor["mismatches"]:
            print(f"    - [{m['severity'].upper()}] {m['issue']}\n")

    # 2. Module 4 — Driving Academy Assistant
    banner("2. MODULE 4 (PORT 8004) — DRIVING ACADEMY MULTILINGUAL MATCHING")
    with httpx.Client(base_url="http://127.0.0.1:8004", timeout=5.0) as client:
        videos = client.get("/academy/videos").json()
        print(f"[*] Curriculum Library: {len(videos)} pre-generated lesson videos")
        print(f"    Topics: {', '.join(v['topic'] for v in videos[:5])}...")

        # English
        res_en = client.post("/academy/match-video", json={
            "applicant_id": "app_1",
            "query": "Figure 8 test track steering technique",
        }).json()
        print("\n[*] Query (English): 'Figure 8 test track steering technique'")
        print(f"    -> Matched: {res_en['topic']} ({res_en['video_id']}) | Confidence: {res_en['confidence']}")

        # Hinglish
        res_hi = client.post("/academy/match-video", json={
            "applicant_id": "app_1",
            "query": "clutch kaise chhodna hai gadi band ho jaati hai",
        }).json()
        print("\n[*] Query (Hinglish): 'clutch kaise chhodna hai gadi band ho jaati hai'")
        print(f"    -> Matched: {res_hi['topic']} ({res_hi['video_id']}) | Confidence: {res_hi['confidence']}")

        # Hindi (Devanagari)
        res_dev = client.post("/academy/match-video", json={
            "applicant_id": "app_1",
            "query": "चढ़ाई पर गाड़ी पीछे खिसक रही है हैंडब्रेक कैसे लगाएं",
        }).json()
        print("\n[*] Query (Hindi): 'चढ़ाई पर गाड़ी पीछे खिसक रही है हैंडब्रेक कैसे लगाएं'")
        print(f"    -> Matched: {res_dev['topic']} ({res_dev['video_id']}) | Confidence: {res_dev['confidence']}")

    # 3. Module 6 — Bol Ke Apply Conversational Front Door
    banner("3. MODULE 6 (PORT 8006) — BOL KE APPLY (VOICE FRONT DOOR & MCP TOOLS)")
    with httpx.Client(base_url="http://127.0.0.1:8006", timeout=5.0) as client:
        tools = client.get("/tools").json()
        print(f"[*] Registered MCP Tools: {[t['name'] for t in tools]}\n")

        # Turn 1: Profile Fetch
        c1 = client.post("/chat", json={
            "message": "Mera verified profile dikhao",
            "applicant_id": "applicant_clean",
        }).json()
        print("[*] Utterance (Hinglish): 'Mera verified profile dikhao'")
        print(f"    Language: {c1['language']} | Executed Tool: {c1['tool_called']}")
        print(f"    Assistant Reply: {c1['reply']}\n")

        # Turn 2: Mismatch rejection check
        c2 = client.post("/chat", json={
            "message": "Check karo documents me koi rejection risk to nahi hai?",
            "applicant_id": "applicant_pan_name_mismatch",
        }).json()
        print("[*] Utterance (Hinglish): 'Check karo documents me koi rejection risk to nahi hai?'")
        print(f"    Language: {c2['language']} | Executed Tool: {c2['tool_called']}")
        print(f"    Assistant Reply: {c2['reply']}\n")

        # Turn 3: Academy Question in Hindi
        c3 = client.post("/chat", json={
            "message": "रिवर्स पार्किंग का सही तरीका बताओ",
            "applicant_id": "applicant_clean",
        }).json()
        print("[*] Utterance (Hindi): 'रिवर्स पार्किंग का सही तरीका बताओ'")
        print(f"    Language: {c3['language']} | Executed Tool: {c3['tool_called']}")
        print(f"    Assistant Reply: {c3['reply']}\n")

    banner("DEMONSTRATION COMPLETED SUCCESSFULLY — ALL SERVICES OPERATIONAL")


if __name__ == "__main__":
    run_demo()
