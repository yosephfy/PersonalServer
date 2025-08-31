from __future__ import annotations

import subprocess
import time
import os
import uuid
from typing import Dict, Optional, List


def run_command(cmd: str, timeout: Optional[int] = None, cwd: Optional[str] = None) -> Dict:
    start = time.time()
    try:
        # Run in shell for parity with bash usage, return combined results
        proc = subprocess.run(
            str(cmd),
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


def run_commands(cmds: List[str], timeout: Optional[int] = None, cwd: Optional[str] = None, stop_on_error: bool = False) -> Dict:
    """Run a list of shell commands sequentially.

    Returns an aggregate result with per-command outputs.
    """
    results: List[Dict] = []
    stopped = False
    current_cwd: Optional[str] = cwd or None
    for raw in cmds:
        c = str(raw).strip()
        if not c:
            continue

        # Handle 'cd' internally so directory persists across subsequent commands
        if c == "cd" or c.startswith("cd "):
            start = time.time()
            dest_arg = c[2:].strip()
            try:
                base = Path(current_cwd) if current_cwd else Path.cwd()
                if not dest_arg:
                    dest = Path(os.path.expanduser("~")).resolve()
                else:
                    # Expand ~ and environment vars, then resolve relative to base
                    expanded = os.path.expanduser(os.path.expandvars(dest_arg))
                    dest = (Path(expanded) if os.path.isabs(expanded) else (base / expanded)).resolve()

                if not dest.exists() or not dest.is_dir():
                    duration = time.time() - start
                    result = {
                        "ok": False,
                        "code": 1,
                        "stdout": "",
                        "stderr": f"cd: no such directory: {dest_arg}",
                        "duration_sec": round(duration, 4),
                    }
                else:
                    current_cwd = str(dest)
                    duration = time.time() - start
                    result = {
                        "ok": True,
                        "code": 0,
                        "stdout": current_cwd,
                        "stderr": "",
                        "duration_sec": round(duration, 4),
                    }
            except Exception as e:
                duration = time.time() - start
                result = {
                    "ok": False,
                    "code": 1,
                    "stdout": "",
                    "stderr": f"cd error: {e}",
                    "duration_sec": round(duration, 4),
                }
        else:
            result = run_command(c, timeout=timeout, cwd=current_cwd)

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


def run_commands_single_shell(
    cmds: List[str],
    timeout: Optional[int] = None,
    cwd: Optional[str] = None,
    stop_on_error: bool = False,
) -> Dict:
    """Run commands in a single shell session, preserving env and cwd.

    Returns per-command results by splitting combined output with unique delimiters.
    Notes:
    - stderr is merged into stdout for accurate segmenting (stdout contains both).
    - duration per command is not measured; set to None.
    """
    if not cmds:
        return {"ok": True, "stop_on_error": stop_on_error, "stopped": False, "results": []}

    delim = f"__PS_DELIM_{uuid.uuid4().hex}__"
    stop_flag = "1" if stop_on_error else "0"

    # Build a POSIX-sh compatible script
    lines: List[str] = []
    lines.append("#!/bin/sh")
    # Merge stderr into stdout so we can parse stream in order
    lines.append("exec 2>&1")
    lines.append(f"STOP_ON_ERROR={stop_flag}")
    lines.append(f"DELIM='{delim}'")

    for i, raw in enumerate(cmds):
        c = str(raw)
        lines.append(f"echo \"$DELIM BEGIN {i}\"")
        # Insert the command verbatim to preserve shell semantics (cd, exports, etc.)
        lines.append(c)
        lines.append("code=$?")
        lines.append(f"echo \"$DELIM END {i} $code\"")
        # Early exit if requested
        lines.append('[ "$STOP_ON_ERROR" = "1" ] && [ $code -ne 0 ] && exit $code')

    script = "\n".join(lines) + "\n"

    proc = subprocess.run(
        script,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd or None,
    )

    out = proc.stdout or ""
    # Parse segments
    results: List[Dict] = []
    idx = -1
    buf: List[str] = []
    expected = 0
    stopped = False
    for line in out.splitlines():
        if line.strip() == f"{delim} BEGIN {expected}":
            # Start of a new segment
            idx = expected
            buf = []
            continue
        if line.startswith(f"{delim} END "):
            # Attempt to parse "{delim} END i code"
            parts = line.strip().split()
            if len(parts) >= 4 and parts[0] == f"{delim}" and parts[1] == "END":
                try:
                    seg_i = int(parts[2])
                    code = int(parts[3])
                except Exception:
                    seg_i = idx if idx >= 0 else expected
                    code = 1
                # Finalize segment
                results.append(
                    {
                        "cmd": str(cmds[seg_i]) if 0 <= seg_i < len(cmds) else "",
                        "ok": code == 0,
                        "code": code,
                        "stdout": "\n".join(buf),
                        "stderr": "",  # merged into stdout
                        "duration_sec": None,
                    }
                )
                expected += 1
                idx = -1
                buf = []
                continue
        # Accumulate into current buffer if inside a segment
        if idx >= 0:
            buf.append(line)

    # If script exited early due to stop_on_error, detect incomplete coverage
    if stop_on_error and len(results) < len(cmds):
        stopped = True

    all_ok = (proc.returncode == 0) and all(r.get("ok") for r in results)
    return {
        "ok": all_ok,
        "stop_on_error": stop_on_error,
        "stopped": stopped,
        "results": results,
        "exit_code": proc.returncode,
    }
