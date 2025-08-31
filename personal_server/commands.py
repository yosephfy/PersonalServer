from __future__ import annotations

import shlex
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional, List


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


def run_commands(cmds: List[str], timeout: Optional[int] = None, cwd: Optional[str] = None, stop_on_error: bool = False) -> Dict:
    """Run a list of shell commands sequentially.

    Returns an aggregate result with per-command outputs.
    """
    results: List[Dict] = []
    stopped = False
    for c in cmds:
        result = run_command(c, timeout=timeout, cwd=cwd)
        result_with_cmd = {"cmd": c, **result}
        results.append(result_with_cmd)
        if stop_on_error and not result.get("ok"):
            stopped = True
            break

    all_ok = all(r.get("ok") for r in results) if results else True
    return {
        "ok": all_ok,
        "stop_on_error": stop_on_error,
        "stopped": stopped,
        "results": results,
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
