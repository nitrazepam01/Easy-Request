from __future__ import annotations

from copy import deepcopy
from typing import Any

import streamlit as st

DEFAULT_FILTERS = {
    "source_doc": "全部题库",
    "section_title": "全部章节",
    "question_type": "全部题型",
}

DEFAULT_AUTH = {
    "nickname_norm": None,
    "nickname_display": None,
    "login_mode": "session",
}

DEFAULT_USER_STATE = {
    "current_page": "首页/登录",
    "current_question_id": None,
    "active_source": "全部题库",
    "active_filters": deepcopy(DEFAULT_FILTERS),
}

DEFAULT_QUESTION_STATE = {
    "last_selected": None,
    "last_wrong_selected": None,
    "last_is_correct": None,
    "attempt_count": 0,
    "wrong_count": 0,
    "ever_wrong": False,
    "mastered": False,
    "updated_at": None,
}


def ensure_runtime_state() -> None:
    st.session_state.setdefault("auth", deepcopy(DEFAULT_AUTH))
    st.session_state.setdefault("question_states", {})
    st.session_state.setdefault("user_state", deepcopy(DEFAULT_USER_STATE))
    st.session_state.setdefault("backend_status", {"available": False, "reason": "未初始化"})
    st.session_state.setdefault("question_bank_ready", False)


def reset_runtime_state() -> None:
    st.session_state["auth"] = deepcopy(DEFAULT_AUTH)
    st.session_state["question_states"] = {}
    st.session_state["user_state"] = deepcopy(DEFAULT_USER_STATE)

    for key in list(st.session_state.keys()):
        if key.startswith(("quiz_", "wrong_")):
            del st.session_state[key]


def merge_user_state(remote_state: dict[str, Any] | None) -> dict[str, Any]:
    merged = deepcopy(DEFAULT_USER_STATE)
    if not remote_state:
        return merged

    merged["current_page"] = remote_state.get("current_page") or merged["current_page"]
    merged["current_question_id"] = remote_state.get("current_question_id")
    merged["active_source"] = remote_state.get("active_source") or merged["active_source"]

    remote_filters = remote_state.get("active_filters") or {}
    merged["active_filters"] = {
        "source_doc": remote_filters.get("source_doc") or merged["active_filters"]["source_doc"],
        "section_title": remote_filters.get("section_title")
        or merged["active_filters"]["section_title"],
        "question_type": remote_filters.get("question_type")
        or merged["active_filters"]["question_type"],
    }
    return merged


def get_question_state(question_id: str) -> dict[str, Any]:
    ensure_runtime_state()
    raw = st.session_state["question_states"].get(question_id) or {}
    state = deepcopy(DEFAULT_QUESTION_STATE)
    state.update(raw)
    return state


def set_question_state(question_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    state = deepcopy(DEFAULT_QUESTION_STATE)
    state.update(st.session_state["question_states"].get(question_id) or {})
    state.update(payload)
    st.session_state["question_states"][question_id] = state
    return state


def is_authenticated() -> bool:
    ensure_runtime_state()
    return bool(st.session_state["auth"].get("nickname_norm"))
