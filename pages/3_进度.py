from __future__ import annotations

import pandas as pd
import streamlit as st

from lib.auth import current_user, require_login
from lib.data import load_question_bank
from lib.persistence import get_backend_status, save_user_state
from lib.session import ensure_runtime_state, get_question_state
from lib.ui import apply_theme, render_hero, render_metric_card, section_heading, setup_page, sidebar_profile


setup_page("进度 | 医学伦理复习平台", "📈")
apply_theme()
ensure_runtime_state()
auth = require_login()
backend_status = get_backend_status()
sidebar_profile(auth, backend_status)

questions = load_question_bank()
question_rows = []
for question in questions:
    state = get_question_state(question["question_id"])
    question_rows.append(
        {
            "question_id": question["question_id"],
            "source_doc": question["source_doc"],
            "section_title": question["section_title"],
            "question_type": question["question_type"],
            "attempted": state["attempt_count"] > 0,
            "last_is_correct": state["last_is_correct"] is True,
            "ever_wrong": state["ever_wrong"],
            "mastered": state["mastered"],
        }
    )

df = pd.DataFrame(question_rows)
attempted_count = int(df["attempted"].sum())
correct_count = int(df["last_is_correct"].sum())
wrong_active_count = int(((df["ever_wrong"]) & (~df["mastered"])).sum())
mastered_count = int(df["mastered"].sum())

st.session_state["user_state"]["current_page"] = "进度"
save_user_state(auth["nickname_norm"], st.session_state["user_state"])

render_hero(
    "学习进度总览",
    "把刷题、错题和当前定位放到一页里看清楚，便于自己决定接下来是继续推进覆盖率，还是专注消化错题。",
    "Progress Ledger",
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_metric_card("覆盖率", f"{attempted_count}/{len(df)}", "至少作答过一次的题目数量。")
with col2:
    render_metric_card("最近答对", str(correct_count), "按最近一次作答结果统计。")
with col3:
    render_metric_card("待复盘错题", str(wrong_active_count), "曾经做错且尚未标记为已掌握。")
with col4:
    render_metric_card("已掌握错题", str(mastered_count), "从错题本移出的题目数量。")

section_heading("继续学习", "从上次位置继续，或者直接打开指定页面。")
resume_col1, resume_col2, resume_col3 = st.columns(3)
with resume_col1:
    st.metric("上次所在页面", st.session_state["user_state"].get("current_page") or "首页/登录")
with resume_col2:
    st.metric("上次题目 ID", st.session_state["user_state"].get("current_question_id") or "暂无")
with resume_col3:
    st.page_link("pages/1_刷题.py", label="继续刷题", icon="📝")

section_heading("按来源统计")
source_summary = (
    df.groupby("source_doc")
    .agg(
        总题量=("question_id", "count"),
        已作答=("attempted", "sum"),
        最近答对=("last_is_correct", "sum"),
        曾做错=("ever_wrong", "sum"),
        已掌握=("mastered", "sum"),
    )
    .reset_index()
    .rename(columns={"source_doc": "来源"})
)
st.dataframe(source_summary, use_container_width=True, hide_index=True)

section_heading("按题型统计")
type_summary = (
    df.groupby("question_type")
    .agg(
        总题量=("question_id", "count"),
        已作答=("attempted", "sum"),
        最近答对=("last_is_correct", "sum"),
        待复盘=("ever_wrong", "sum"),
    )
    .reset_index()
    .rename(columns={"question_type": "题型"})
)
st.dataframe(type_summary, use_container_width=True, hide_index=True)
