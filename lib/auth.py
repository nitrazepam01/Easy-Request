from __future__ import annotations

import re
from typing import Any

import streamlit as st

from lib.persistence import get_backend_status, load_remote_state, upsert_profile
from lib.session import ensure_runtime_state, merge_user_state, reset_runtime_state

LOCAL_DEMO_INVITE = "DEMO"


def normalize_nickname(raw: str) -> str:
    cleaned = raw.replace("\u3000", " ").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def nickname_key(display_name: str) -> str:
    return normalize_nickname(display_name).casefold()


def current_expected_invite() -> str:
    try:
        configured = st.secrets.get("APP_INVITE_CODE")
    except Exception:
        configured = None
    return configured or LOCAL_DEMO_INVITE


def login_hint() -> str:
    try:
        configured = st.secrets.get("APP_INVITE_CODE")
    except Exception:
        configured = None
    if configured:
        return "已启用正式邀请码校验。"
    return f"未配置 `APP_INVITE_CODE`，当前使用本地演示邀请码：`{LOCAL_DEMO_INVITE}`。"


def current_user() -> dict[str, Any]:
    ensure_runtime_state()
    return st.session_state["auth"]


def is_authenticated() -> bool:
    return bool(current_user().get("nickname_norm"))


def login_user(invite_code: str, nickname: str) -> tuple[bool, str]:
    ensure_runtime_state()
    nickname_display = normalize_nickname(nickname)
    if not nickname_display:
        return False, "请输入昵称。"

    if normalize_nickname(invite_code) != current_expected_invite():
        return False, "邀请码不正确，请重新确认。"

    nickname_norm = nickname_key(nickname_display)
    backend_status = get_backend_status()
    remote = load_remote_state(nickname_norm)
    upsert_profile(nickname_norm, nickname_display)

    st.session_state["auth"] = {
        "nickname_norm": nickname_norm,
        "nickname_display": nickname_display,
        "login_mode": "cloud" if backend_status["available"] else "session",
    }
    st.session_state["backend_status"] = backend_status
    st.session_state["question_states"] = remote["question_states"]
    st.session_state["user_state"] = merge_user_state(remote["user_state"])
    return True, "已进入复习平台。"


def logout_user() -> None:
    reset_runtime_state()


def require_login() -> dict[str, Any]:
    ensure_runtime_state()
    auth = current_user()
    if auth.get("nickname_norm"):
        return auth

    st.warning("请先回到首页输入邀请码和昵称，再进入刷题页面。")
    st.page_link("app.py", label="返回首页 / 登录")
    st.stop()
