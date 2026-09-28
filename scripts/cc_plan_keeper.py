"""
Keeps creator-code/quiz/plan.json (the quizzes, On This Day and the seasonal
series, planned ahead by cc_quiz_plan.py) from running out, so the daily
lineup never finds an empty day, for years.

    load_plan(extend_to=day)   the plan; if it ends before `extend_to`, it is
                               re-planned from its next day for 180 days more
                               (days already planned stay exactly as they are)
                               and, on GitHub, committed back to the branch

Best effort: if the planner or the push fails, the build carries on with the
plan it has (the lineup falls back to other formats on a day the plan lacks)
and tries again the next night.
"""

import json
import os
import subprocess
import sys
from datetime import date, timedelta

from cc_common import CC_DIR, log

PLAN = CC_DIR / "quiz" / "plan.json"
ROOT = CC_DIR.parent
BRANCH = "claude/creator-code-bad-automation-0jjc1k"
MORE_DAYS = 180


def _last(plan: dict) -> date | None:
    days = [v["date"] for v in plan.get("videos", [])]
    return date.fromisoformat(max(days)) if days else None


def load_plan(extend_to: date | None = None) -> dict:
    plan = json.loads(PLAN.read_text()) if PLAN.exists() else {"videos": [], "items": {}}
    last = _last(plan)
    if extend_to is None or (last and last >= extend_to) or not plan.get("start"):
        return plan
    start = date.fromisoformat(plan["start"])
    new_last = max(extend_to, last or extend_to) + timedelta(days=MORE_DAYS)
    frm = (last + timedelta(days=1)) if last else extend_to
    log(f"The plan ends {last}; planning {frm} to {new_last}")
    try:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "cc_quiz_plan.py"), "--from", frm.isoformat(),
                        "--days", str((new_last - start).days + 1)], check=True, cwd=ROOT, timeout=1800)
    except (OSError, subprocess.SubprocessError) as e:
        log(f"  planning failed ({e!r}); carrying on with the current plan")
        return plan
    plan = json.loads(PLAN.read_text())
    log(f"  the plan now runs to {_last(plan)}")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        _push(f"Plan: extend the quiz and series plan to {_last(plan)} (automatic)")
    return plan


def _git(*args, check=True):
    return subprocess.run(["git", "-c", "user.name=usecodebad-bot",
                           "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com", *args],
                          cwd=ROOT, check=check, capture_output=True, text=True, timeout=300)


def _push(message: str):
    """Commit the plan to the branch the nightly jobs build from."""
    try:
        _git("add", str(PLAN.relative_to(ROOT)))
        if not _git("diff", "--cached", "--quiet", check=False).returncode:
            return
        _git("commit", "-m", message)
        for _ in range(3):
            if _git("push", "origin", f"HEAD:{BRANCH}", check=False).returncode == 0:
                log("  plan committed to the branch")
                return
            _git("pull", "--rebase", "origin", BRANCH, check=False)
        log("  couldn't push the plan; it is re-planned next night")
    except (OSError, subprocess.SubprocessError) as e:
        log(f"  couldn't commit the plan ({e!r})")
