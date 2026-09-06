"""Supabase PostgreSQL Database Client & Connection Manager.

Provides persistent relational storage for Parivahan Seva:
- Master & Dimension Tables (dim_rto, dim_vehicle_class, dim_journey_stages, dim_exam_questions)
- Core Entities (tbl_citizens, tbl_applications, tbl_identity_verifications)
- Test & Booking Operations (tbl_exam_sessions, tbl_track_bookings, tbl_licences)
- Autonomous Agent Memory (tbl_agent_sessions, tbl_agent_messages)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("parivahan_db")

# Default Supabase configuration
SUPABASE_HOST = os.getenv("SUPABASE_HOST", "aws-0-ap-southeast-1.pooler.supabase.com")
SUPABASE_PORT = int(os.getenv("SUPABASE_PORT", "5432"))
SUPABASE_USER = os.getenv("SUPABASE_USER", "postgres.wouolwjzjwazlfflfikk")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD", "BWMISKPD@2026")
SUPABASE_DBNAME = os.getenv("SUPABASE_DBNAME", "postgres")

# Schema DDL Path
SCHEMA_FILE = Path(__file__).parent / "db_schema.sql"


_db_down_until = 0.0  # circuit breaker: after a failure, skip attempts for a while


def get_db_connection():
    """Create a new direct connection to Supabase PostgreSQL.

    A failed connect opens a 5-minute circuit breaker — every caller is a
    best-effort mirror wrapped in try/except, and without the breaker each
    journey save would stall up to the connect timeout when the DB is
    unreachable (tests went 1s -> 30s; a blocked network would feel like a
    frozen portal).
    """
    global _db_down_until
    import time as _time

    if _time.time() < _db_down_until:
        raise ConnectionError("Supabase circuit breaker open (recent connect failure)")
    try:
        import psycopg
        conn = psycopg.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            dbname=SUPABASE_DBNAME,
            connect_timeout=4,
            autocommit=True,
        )
        _db_down_until = 0.0
        return conn
    except Exception as exc:
        _db_down_until = _time.time() + 300
        logger.error("Failed to connect to Supabase PostgreSQL: %s", exc)
        raise


def init_db() -> None:
    """Initialize Supabase tables from schema DDL and seed reference data."""
    if not SCHEMA_FILE.exists():
        logger.warning("Schema file not found at %s", SCHEMA_FILE)
        return

    ddl = SCHEMA_FILE.read_text(encoding="utf-8")
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            logger.info("Executed database DDL successfully.")
            _seed_reference_data(cur)


def _seed_reference_data(cur) -> None:
    """Seed dimension tables and initial citizen profiles."""
    # 1. RTO Master
    rtos = [
        ("DL01", "DL", "Mall Road RTO", "Mall Road, Civil Lines, Delhi - 110054", ["110054", "110007", "110009"], True, 40),
        ("DL04", "DL", "Janakpuri RTO", "District Centre, Janakpuri, New Delhi - 110058", ["110058", "110018", "110059"], True, 35),
        ("KA01", "KA", "Koramangala RTO", "Bande Road, Koramangala 3rd Block, Bengaluru - 560034", ["560034", "560095", "560047"], True, 30),
        ("KA03", "KA", "Indiranagar RTO", "Binnamangala 2nd Stage, Indiranagar, Bengaluru - 560038", ["560038", "560008", "560075"], True, 30),
        ("UP16", "UP", "Noida RTO", "Transport Nagar, Sector 62, Noida - 201301", ["201301", "201309", "201307"], True, 30),
    ]
    for rto in rtos:
        cur.execute(
            """
            INSERT INTO dim_rto (rto_code, state_code, office_name, address, jurisdiction_pincodes, has_adtt_track, daily_slot_capacity)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (rto_code) DO NOTHING;
            """,
            rto,
        )

    # 2. Vehicle Classes
    classes = [
        ("LMV", "Light Motor Vehicle", "Car, Jeep, Private Passenger Vehicle", 18, 1350, True),
        ("MCWG", "Motorcycle with Gear", "Two-wheeler with manual or foot-operated gears", 18, 950, True),
        ("MCWOG", "Motorcycle without Gear", "Automatic scooter up to 50cc or EV two-wheeler", 16, 500, False),
    ]
    for vc in classes:
        cur.execute(
            """
            INSERT INTO dim_vehicle_class (class_code, title, description, min_age, statutory_fee, has_gear)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (class_code) DO NOTHING;
            """,
            vc,
        )

    # 3. Journey Stages
    stages = [
        ("no_licence", 0, "Not Applied", "apply", "Apply for New Driving Licence", 0, 0),
        ("ll_application_submitted", 1, "LL Application Submitted", "verify_documents", "Document Verification", 1, 0),
        ("ll_documents_verified", 2, "Documents Verified", "take_ll_test", "Take Online STALL Test", 1, 0),
        ("ll_test_scheduled", 3, "STALL Exam Scheduled", "take_ll_test", "Take Online STALL Test", 1, 0),
        ("ll_issued", 4, "Learner's Licence Active", "begin_practice", "Start 30-Day Practice Window", 0, 180),
        ("practice_window", 5, "Practice Window", "book_dl_test", "Book Driving Test Slot", 30, 180),
        ("dl_test_booked", 6, "Driving Test Scheduled", "take_dl_test", "Report to Automated Track", 7, 180),
        ("dl_test_result_fail", 7, "Driving Test Retry", "rebook_dl_test", "Rebook Driving Test Slot", 7, 180),
        ("dl_test_result_pass", 8, "Driving Test Cleared", "issue_dl", "Issue Driving Licence", 1, 0),
        ("dl_issued", 9, "Driving Licence Issued", "download_dl", "Download Form 7 Smart Card", 0, 7300),
    ]
    for st in stages:
        cur.execute(
            """
            INSERT INTO dim_journey_stages (stage_code, order_index, title, next_action_type, next_action_label, sla_days, validity_days)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (stage_code) DO NOTHING;
            """,
            st,
        )

    # 4. Initial Citizen Profiles (Replacing static citizens.json)
    initial_citizens = [
        (
            "applicant_clean",
            "9876543210",
            "Rohan Verma",
            date(2003, 8, 15),
            "male",
            "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=300",
            "4321",
            "Flat 204, Palm Grove, Indiranagar, Bengaluru, KA - 560038",
            "560038",
            "KA03",
            True,
            "ABCDP1234F",
            "Rohan Verma",
            date(2003, 8, 15),
        ),
        (
            "applicant_001",
            "9876543210",
            "Rohan Verma",
            date(2003, 8, 15),
            "male",
            "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=300",
            "4321",
            "Flat 402, Shanti Niketan, Mall Road, Civil Lines, Delhi - 110054",
            "110054",
            "DL01",
            True,
            "ABCDP1234F",
            "Rohan Verma",
            date(2003, 8, 15),
        ),
        (
            "applicant_student",
            "9876543211",
            "Priya Sharma",
            date(2004, 3, 22),
            "female",
            "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300",
            "8765",
            "C-42, Sector 15, Vasundhara, Ghaziabad, UP - 201012",
            "201012",
            "KA03",  # Student in Bengaluru, Aadhaar in UP
            False,
            "PQRSM5678K",
            "Priya Sharma",
            date(2004, 3, 22),
        ),
        (
            "applicant_mismatch",
            "9876543212",
            "Vikram Singh Chauhan",
            date(1999, 11, 5),
            "male",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300",
            "1122",
            "Plot 18, Block B, Janakpuri, New Delhi - 110058",
            "110058",
            "DL04",
            True,
            "XYZPK9988L",
            "Vikram S Chauhan",  # PAN Name Mismatch
            date(1999, 11, 5),
        ),
    ]

    for c in initial_citizens:
        cur.execute(
            """
            INSERT INTO tbl_citizens (
                citizen_id, phone, full_name, dob, gender, photo_url,
                aadhaar_last_four, registered_address, pincode, gps_suggested_rto, addresses_match
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (citizen_id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                dob = EXCLUDED.dob,
                registered_address = EXCLUDED.registered_address,
                gps_suggested_rto = EXCLUDED.gps_suggested_rto,
                addresses_match = EXCLUDED.addresses_match;
            """,
            c[:11],
        )
        # Seed identity verification
        pan_num, pan_name, pan_dob = c[11], c[12], c[13]
        mismatches = []
        clear = True
        if c[0] == "applicant_mismatch":
            clear = False
            mismatches.append({
                "field": "name",
                "fetched_value": "Vikram Singh Chauhan",
                "issue": "Aadhaar name 'Vikram Singh Chauhan' does not match PAN record 'Vikram S Chauhan'",
                "suggested_fix": "Update PAN via NSDL portal or upload gazette notification",
                "severity": "error",
            })
        elif c[0] == "applicant_student":
            mismatches.append({
                "field": "jurisdiction",
                "fetched_value": "KA-03 Indiranagar (Current Location)",
                "issue": "Device location in Karnataka differs from Aadhaar permanent address in Uttar Pradesh",
                "suggested_fix": "Select whether to apply under Aadhaar jurisdiction (UP-16) or Bangalore student residence",
                "severity": "warning",
            })

        cur.execute(
            """
            INSERT INTO tbl_identity_verifications (
                citizen_id, pan_number, pan_name, pan_dob, mismatches, clear_to_submit
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (c[0], pan_num, pan_name, pan_dob, json.dumps(mismatches), clear),
        )


# Helper query functions for Services & Agent -------------------------

def get_citizen(citizen_id: str) -> dict[str, Any] | None:
    """Fetch citizen demographic record from Supabase."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT citizen_id, phone, full_name, dob, gender, photo_url,
                       aadhaar_last_four, registered_address, pincode, gps_suggested_rto, addresses_match
                FROM tbl_citizens
                WHERE citizen_id = %s OR phone = %s;
                """,
                (citizen_id, citizen_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "citizen_id": row[0],
                "phone": row[1],
                "name": row[2],
                "dob": row[3],
                "gender": row[4],
                "photo_url": row[5],
                "aadhaar_last_four": row[6],
                "address": row[7],
                "pincode": row[8],
                "gps_suggested_rto": row[9],
                "addresses_match": row[10],
            }


def upsert_citizen(
    citizen_id: str,
    phone: str,
    name: str,
    dob: date,
    address: str,
    gps_rto: str = "DL01",
    vehicle_class: str = "LMV",
) -> dict[str, Any]:
    """Dynamically register or update a citizen from voice or web input."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tbl_citizens (
                    citizen_id, phone, full_name, dob, registered_address, gps_suggested_rto
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (phone) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    dob = EXCLUDED.dob,
                    registered_address = EXCLUDED.registered_address,
                    gps_suggested_rto = EXCLUDED.gps_suggested_rto,
                    updated_at = NOW()
                RETURNING citizen_id, phone, full_name, dob, registered_address, gps_suggested_rto;
                """,
                (citizen_id, phone, name, dob, address, gps_rto),
            )
            res = cur.fetchone()
            return {
                "citizen_id": res[0],
                "phone": res[1],
                "name": res[2],
                "dob": res[3],
                "address": res[4],
                "gps_suggested_rto": res[5],
                "vehicle_class": vehicle_class,
            }


def get_or_create_agent_session(session_id: str, citizen_id: str | None = None) -> dict[str, Any]:
    """Retrieve or initialize an agent conversation session in Supabase."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT session_id, citizen_id, channel, active_intent, pending_action FROM tbl_agent_sessions WHERE session_id = %s;",
                (session_id,),
            )
            row = cur.fetchone()
            if row:
                return {
                    "session_id": row[0],
                    "citizen_id": row[1],
                    "channel": row[2],
                    "active_intent": row[3],
                    "pending_action": row[4],
                }
            cur.execute(
                """
                INSERT INTO tbl_agent_sessions (session_id, citizen_id)
                VALUES (%s, %s)
                RETURNING session_id, citizen_id, channel, active_intent, pending_action;
                """,
                (session_id, citizen_id),
            )
            new_row = cur.fetchone()
            return {
                "session_id": new_row[0],
                "citizen_id": new_row[1],
                "channel": new_row[2],
                "active_intent": new_row[3],
                "pending_action": new_row[4],
            }


def update_agent_pending_action(session_id: str, pending_action: dict | None, active_intent: str | None = None) -> None:
    """Record pending action and intent so 'Haan kar do' triggers execution immediately."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tbl_agent_sessions
                SET pending_action = %s, active_intent = COALESCE(%s, active_intent), updated_at = NOW()
                WHERE session_id = %s;
                """,
                (json.dumps(pending_action) if pending_action else None, active_intent, session_id),
            )


def append_agent_message(
    session_id: str,
    sender: str,
    content: str,
    tool_called: str | None = None,
    tool_result: Any | None = None,
    interactive_options: list[str] | None = None,
) -> None:
    """Append a dialogue message with optional interactive options (MCQs) into Supabase."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Ensure parent session exists
            cur.execute(
                """
                INSERT INTO tbl_agent_sessions (session_id)
                VALUES (%s)
                ON CONFLICT (session_id) DO NOTHING;
                """,
                (session_id,),
            )
            cur.execute(
                """
                INSERT INTO tbl_agent_messages (
                    session_id, sender, content, tool_called, tool_result, interactive_options
                ) VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (
                    session_id,
                    sender,
                    content,
                    tool_called,
                    json.dumps(tool_result) if tool_result else None,
                    json.dumps(interactive_options or []),
                ),
            )


def get_agent_history(session_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Retrieve recent conversation history for a session from Supabase."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sender, content, tool_called, tool_result, interactive_options, created_at
                FROM tbl_agent_messages
                WHERE session_id = %s
                ORDER BY created_at ASC
                LIMIT %s;
                """,
                (session_id, limit),
            )
            rows = cur.fetchall()
            return [
                {
                    "sender": r[0],
                    "content": r[1],
                    "tool_called": r[2],
                    "tool_result": r[3],
                    "options": r[4] or [],
                    "created_at": r[5].isoformat() if r[5] else None,
                }
                for r in rows
            ]


def upsert_application(
    application_number: str,
    citizen_id: str,
    rto_code: str = "DL01",
    vehicle_class: str = "LMV",
    stage: str = "no_licence",
    confirmed_rto_code: str | None = None,
) -> None:
    """Sync or update application status in Supabase tbl_applications."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Ensure citizen exists in tbl_citizens
                cur.execute(
                    """
                    INSERT INTO tbl_citizens (citizen_id, phone, full_name, dob, registered_address)
                    VALUES (%s, '0000000000', %s, '2000-01-01', 'India')
                    ON CONFLICT (citizen_id) DO NOTHING;
                    """,
                    (citizen_id, citizen_id),
                )
                cur.execute(
                    """
                    INSERT INTO tbl_applications (
                        application_number, citizen_id, rto_code, vehicle_class, current_stage, confirmed_rto_code
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (application_number) DO UPDATE SET
                        current_stage = EXCLUDED.current_stage,
                        confirmed_rto_code = COALESCE(EXCLUDED.confirmed_rto_code, tbl_applications.confirmed_rto_code),
                        updated_at = NOW();
                    """,
                    (application_number, citizen_id, rto_code, vehicle_class, stage, confirmed_rto_code),
                )
    except Exception as exc:
        logger.warning("upsert_application error: %s", exc)

