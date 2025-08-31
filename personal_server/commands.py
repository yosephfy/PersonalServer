from __future__ import annotations

import shlex
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional


def run_command(cmd: str, timeout: Optional[int] = None, cwd: Optional[str] = None) -> Dict:
    start = time.time()
    try:
        # Run in shell for parity with bash usage, return combined results
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or None,
        )
        duration = time.time() - start
        return {
            "ok": proc.returncode == 0,
            "code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "duration_sec": round(duration, 4),
        }
    except subprocess.TimeoutExpired as e:
        duration = time.time() - start
        return {
            "ok": False,
            "code": None,
            "stdout": e.stdout or "",
            "stderr": (e.stderr or "") + "\nTIMEOUT",
            "duration_sec": round(duration, 4),
        }
    except Exception as e:
        duration = time.time() - start
        return {
            "ok": False,
            "code": None,
            "stdout": "",
            "stderr": f"ERROR: {e}",
            "duration_sec": round(duration, 4),
        }

