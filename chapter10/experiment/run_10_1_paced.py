"""Run Experiment 10-1 through the canonical runner with provider pacing.

This wrapper changes neither the task logic nor the scoring logic.  It only
spaces top-level Chat Completions calls so a low-RPM account does not fail in
the middle of a multi-step trajectory.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from openai import OpenAI as RealOpenAI


PROJECT_DIR = Path(__file__).resolve().parents[1] / "multi-role-transfer"
sys.path.insert(0, str(PROJECT_DIR))

import run_comparison as canonical  # noqa: E402


class _PacedCompletions:
    def __init__(self, inner, interval_seconds: float):
        self._inner = inner
        self._interval_seconds = interval_seconds
        self._last_started_at: float | None = None

    def create(self, *args, **kwargs):
        if self._last_started_at is not None:
            elapsed = time.monotonic() - self._last_started_at
            remaining = self._interval_seconds - elapsed
            if remaining > 0:
                print(f"[rate-limit] waiting {remaining:.1f}s before next model request")
                time.sleep(remaining)
        self._last_started_at = time.monotonic()
        return self._inner.create(*args, **kwargs)


class _PacedChat:
    def __init__(self, inner, interval_seconds: float):
        self.completions = _PacedCompletions(inner.completions, interval_seconds)


class _PacedClient:
    def __init__(self, inner, interval_seconds: float):
        self.chat = _PacedChat(inner.chat, interval_seconds)


def _paced_openai(*args, **kwargs):
    interval = float(os.getenv("AGENTBOOK_MIN_REQUEST_INTERVAL", "21"))
    if interval < 0:
        raise ValueError("AGENTBOOK_MIN_REQUEST_INTERVAL must be >= 0")
    return _PacedClient(RealOpenAI(*args, **kwargs), interval)


def main() -> int:
    canonical.OpenAI = _paced_openai
    return canonical.main(canonical.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
