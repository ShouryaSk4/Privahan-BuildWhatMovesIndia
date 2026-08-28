"""Unified server runner for Parivahan MVP.

Runs all 3 active services concurrently with graceful Ctrl+C shutdown:
- Module 3 (Identity & Document Service) on http://127.0.0.1:8003
- Module 4 (Driving Academy Assistant)   on http://127.0.0.1:8004
- Module 6 (Bol Ke Apply Front Door)     on http://127.0.0.1:8006
"""

import signal
import subprocess
import sys
import time


def main():
    print("\n" + "=" * 65)
    print("🚀 LAUNCHING ALL PARIVAHAN MVP ACTIVE SERVICES")
    print("=" * 65)

    services = [
        {
            "name": "Module 3: Identity Service",
            "cmd": [sys.executable, "-m", "uvicorn", "identity_service.main:app", "--host", "127.0.0.1", "--port", "8003"],
            "url": "http://127.0.0.1:8003/docs",
            "cwd": "services/identity",
        },
        {
            "name": "Module 4: Driving Academy",
            "cmd": [sys.executable, "-m", "uvicorn", "academy_service.main:app", "--host", "127.0.0.1", "--port", "8004"],
            "url": "http://127.0.0.1:8004/docs",
            "cwd": "services/academy",
        },
        {
            "name": "Module 6: Bol Ke Apply",
            "cmd": [sys.executable, "-m", "uvicorn", "bol_ke_apply.api:app", "--host", "127.0.0.1", "--port", "8006"],
            "url": "http://127.0.0.1:8006",
            "cwd": "services/bol-ke-apply",
        },
    ]

    processes = []
    for s in services:
        p = subprocess.Popen(s["cmd"])
        processes.append(p)
        print(f"  [+] Started {s['name']}")
        print(f"      Dashboard: {s['url']}")

    print("\n" + "=" * 65)
    print("✨ ALL SERVICES ONLINE!")
    print("   👉 Open Bol Ke Apply Web Console: http://127.0.0.1:8006")
    print("   👉 Module 3 API Docs:             http://127.0.0.1:8003/docs")
    print("   👉 Module 4 API Docs:             http://127.0.0.1:8004/docs")
    print("=" * 65)
    print("Press Ctrl+C to stop all services.\n")

    def handle_sigint(sig, frame):
        print("\nStopping all services...")
        for p in processes:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handle_sigint(None, None)


if __name__ == "__main__":
    main()
