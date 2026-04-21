from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import streamlit as st

try:
    from supabase import create_client
except ImportError:  # pragma: no cover - handled gracefully at runtime
    create_client = None


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_secret(name: str) -> str | None:
    try:
        return st.secrets.get(name)
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def get_supabase_client():
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_KEY")
    if not create_client or not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


def get_backend_status() -> dict[str, Any]:
    if not create_client:
        return {"available": False, "reason": "未安装 supabase 依赖，当前为本地会话模式。"}

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return {"available": False, "reason": "未配置 Supabase secrets，当前为本地会话模式。"}

    client = get_supabase_client()
    if client is None:
        return {"available": False, "reason": "Supabase 客户端初始化失败，当前为本地会话模式。"}

    return {"available": True, "reason": "云端进度与错题同步已启用。"}


def upsert_profile(nickname_norm: str, nickname_display: str) -> None:
    client = get_supabase_client()
    if client is None:
        return

    payload = {
        "nickname_norm": nickname_norm,
        "nickname_display": nickname_display,
        "last_seen_at": utcnow_iso(),
    }
    client.table("profiles").upsert(payload, on_conflict="nickname_norm").execute()


def load_remote_state(nickname_norm: str) -> dict[str, Any]:
    client = get_supabase_client()
    if client is None:
        return {"user_state": None, "question_states": {}}

    user_res = (
        client.table("user_state")
        .select("*")
        .eq("nickname_norm", nickname_norm)
        .limit(1)
        .execute()
    )
    question_res = (
        client.table("question_state").select("*").eq("nickname_norm", nickname_norm).execute()
    )

    user_data = (user_res.data or [None])[0] if isinstance(user_res.data, list) else user_res.data
    question_rows = question_res.data or []
    question_map = {row["question_id"]: row for row in question_rows}
    return {"user_state": user_data, "question_states": question_map}


def save_user_state(nickname_norm: str, payload: dict[str, Any]) -> None:
    client = get_supabase_client()
    if client is None:
        return

    body = {
        "nickname_norm": nickname_norm,
        "current_page": payload.get("current_page"),
        "current_question_id": payload.get("current_question_id"),
        "active_source": payload.get("active_source"),
        "active_filters": payload.get("active_filters") or {},
        "updated_at": utcnow_iso(),
    }
    client.table("user_state").upsert(body, on_conflict="nickname_norm").execute()


def save_question_state(nickname_norm: str, question_id: str, payload: dict[str, Any]) -> None:
    client = get_supabase_client()
    if client is None:
        return

    body = {
        "nickname_norm": nickname_norm,
        "question_id": question_id,
        "last_selected": payload.get("last_selected"),
        "last_wrong_selected": payload.get("last_wrong_selected"),
        "last_is_correct": payload.get("last_is_correct"),
        "attempt_count": payload.get("attempt_count", 0),
        "wrong_count": payload.get("wrong_count", 0),
        "ever_wrong": payload.get("ever_wrong", False),
        "mastered": payload.get("mastered", False),
        "updated_at": utcnow_iso(),
    }
    client.table("question_state").upsert(
        body, on_conflict="nickname_norm,question_id"
    ).execute()
