"""
Conversation memory manager.

Maintains per-session chat histories in memory (dict).
For production, replace with Redis or a DB backend.
"""

from typing import List
from collections import defaultdict

_sessions: dict[str, List[dict]] = defaultdict(list)
MAX_HISTORY = 20  # keep last 20 messages per session


def get_history(session_id: str) -> List[dict]:
    return list(_sessions[session_id])


def add_turn(session_id: str, question: str, answer: str) -> None:
    history = _sessions[session_id]
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    # Trim to max
    if len(history) > MAX_HISTORY:
        _sessions[session_id] = history[-MAX_HISTORY:]


def clear_session(session_id: str) -> None:
    _sessions[session_id] = []


def list_sessions() -> List[str]:
    return list(_sessions.keys())
