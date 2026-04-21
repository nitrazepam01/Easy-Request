from __future__ import annotations

from collections import Counter

import streamlit as st

from lib.auth import current_user, require_login
from lib.data import filter_questions, load_question_bank, unique_sections, unique_source_docs, unique_question_types
from lib.persistence import get_backend_status, save_question_state, save_user_state, utcnow_iso
from lib.session import ensure_runtime_state, get_question_state, set_question_state
from lib.ui import (
    apply_theme,
    render_feedback_banner,
    render_hero,
    render_question_card,
    render_status_pills,
    setup_page,
    sidebar_profile,
)


def save_runtime_context(question_id: str, filters: dict[str, str]) -> None:
    auth = current_user()
    payload = {
        "current_page": "刷题",
        "current_question_id": question_id,
        "active_source": filters["source_doc"],
        "active_filters": filters,
    }
    st.session_state["user_state"] = payload
    if auth.get("nickname_norm"):
        save_user_state(auth["nickname_norm"], payload)


def resolve_current_question_id(filtered_questions: list[dict]) -> str | None:
    if not filtered_questions:
        return None

    query_qid = st.query_params.get("qid")
    if query_qid and any(question["question_id"] == query_qid for question in filtered_questions):
        return query_qid

    saved_qid = st.session_state["user_state"].get("current_question_id")
    if saved_qid and any(question["question_id"] == saved_qid for question in filtered_questions):
        return saved_qid

    return filtered_questions[0]["question_id"]


def go_to_question(question_id: str, position: int) -> None:
    st.session_state["quiz_current_qid"] = question_id
    st.query_params["qid"] = question_id
    st.query_params["pos"] = str(position)
    st.rerun()


setup_page("刷题 | 医学伦理复习平台", "📝")
apply_theme()
ensure_runtime_state()
auth = require_login()
backend_status = get_backend_status()
sidebar_profile(auth, backend_status)

questions = load_question_bank()
saved_filters = st.session_state["user_state"].get("active_filters") or {}
source_docs = ["全部题库"] + unique_source_docs(questions)
all_types = ["全部题型"] + unique_question_types(questions)

if "quiz_source_filter" not in st.session_state:
    st.session_state["quiz_source_filter"] = (
        saved_filters.get("source_doc")
        if saved_filters.get("source_doc") in source_docs
        else "全部题库"
    )

section_options = ["全部章节"] + unique_sections(questions, st.session_state["quiz_source_filter"])
if "quiz_section_filter" not in st.session_state or st.session_state["quiz_section_filter"] not in section_options:
    st.session_state["quiz_section_filter"] = (
        saved_filters.get("section_title")
        if saved_filters.get("section_title") in section_options
        else "全部章节"
    )

if "quiz_type_filter" not in st.session_state:
    st.session_state["quiz_type_filter"] = (
        saved_filters.get("question_type")
        if saved_filters.get("question_type") in all_types
        else "全部题型"
    )

render_hero(
    "刷题主面板",
    "从所有题库、章节单元和题型中自由切换。题号跳转和云端进度会一起保存，刷新页面后还能接着做。",
    "Study Flow",
)

filters_col, nav_col = st.columns([1.2, 1])
with filters_col:
    with st.expander("筛选器", expanded=False):
        st.caption("筛选变化会同步到云端 user_state。")
        source_choice = st.selectbox("题库来源", source_docs, key="quiz_source_filter")

        new_section_options = ["全部章节"] + unique_sections(questions, source_choice)
        if st.session_state["quiz_section_filter"] not in new_section_options:
            st.session_state["quiz_section_filter"] = "全部章节"
        section_choice = st.selectbox("章节 / 分组", new_section_options, key="quiz_section_filter")

        question_type_choice = st.selectbox("题型", all_types, key="quiz_type_filter")

with nav_col:
    with st.expander("导航提示", expanded=False):
        st.caption("符号含义：▶ 当前题，✓ 最近一次作答正确，✗ 曾经做错或最近答错，· 尚未作答。")
        render_status_pills(
            [
                ("▶ 当前题", "default"),
                ("✓ 最近作答正确", "correct"),
                ("✗ 错题 / 最近答错", "wrong"),
                ("· 尚未作答", "default"),
            ]
        )

active_filters = {
    "source_doc": source_choice,
    "section_title": section_choice,
    "question_type": question_type_choice,
}
filtered_questions = filter_questions(questions, **active_filters)

if not filtered_questions:
    st.warning("当前筛选条件下没有题目，请调整筛选器。")
    st.stop()

if "quiz_current_qid" not in st.session_state:
    st.session_state["quiz_current_qid"] = resolve_current_question_id(filtered_questions)

if not any(question["question_id"] == st.session_state["quiz_current_qid"] for question in filtered_questions):
    st.session_state["quiz_current_qid"] = resolve_current_question_id(filtered_questions)

current_qid = st.session_state["quiz_current_qid"]
current_index = next(
    index for index, question in enumerate(filtered_questions) if question["question_id"] == current_qid
)
current_question = filtered_questions[current_index]

save_runtime_context(current_qid, active_filters)
st.query_params["qid"] = current_qid
st.query_params["pos"] = str(current_index + 1)

stats = Counter(
    "attempted"
    if get_question_state(question["question_id"])["attempt_count"]
    else "unseen"
    for question in filtered_questions
)
metric1, metric2, metric3 = st.columns(3)
metric1.metric("当前筛选题量", len(filtered_questions))
metric2.metric("已作答", stats.get("attempted", 0))
metric3.metric("未作答", stats.get("unseen", 0))

question_state = get_question_state(current_qid)
render_feedback_banner(
    question_state["last_is_correct"],
    question_state.get("last_selected"),
    current_question["answer"],
)
render_question_card(current_question, current_index + 1, len(filtered_questions))

status_items = []
if question_state["attempt_count"]:
    status_items.append((f"作答次数 {question_state['attempt_count']}", "default"))
if question_state["last_is_correct"] is True:
    status_items.append(("最近一次答对", "correct"))
if question_state["ever_wrong"]:
    status_items.append((f"累计错题 {question_state['wrong_count']}", "wrong"))
if question_state["mastered"]:
    status_items.append(("已手动标记为掌握", "correct"))
if status_items:
    render_status_pills(status_items)

option_labels = [f"{option['key']}. {option['text']}" for option in current_question["options"]]
label_to_key = {label: option["key"] for label, option in zip(option_labels, current_question["options"])}
selected_key = question_state.get("last_selected")
selected_index = next(
    (index for index, option in enumerate(current_question["options"]) if option["key"] == selected_key),
    None,
)

choice = st.radio(
    "选择你的答案",
    option_labels,
    index=selected_index,
    key=f"quiz_radio_{current_qid}",
)

submit_col, prev_col, next_col = st.columns([1.3, 1, 1])
with submit_col:
    if st.button("提交当前答案", type="primary", use_container_width=True):
        chosen_key = label_to_key[choice]
        is_correct = chosen_key == current_question["answer"]
        new_state = set_question_state(
            current_qid,
            {
                "last_selected": chosen_key,
                "last_wrong_selected": question_state["last_wrong_selected"]
                if is_correct
                else chosen_key,
                "last_is_correct": is_correct,
                "attempt_count": question_state["attempt_count"] + 1,
                "wrong_count": question_state["wrong_count"] + (0 if is_correct else 1),
                "ever_wrong": question_state["ever_wrong"] or (not is_correct),
                "updated_at": utcnow_iso(),
            },
        )
        save_question_state(auth["nickname_norm"], current_qid, new_state)
        st.rerun()

with prev_col:
    if st.button("上一题", use_container_width=True, disabled=current_index == 0):
        go_to_question(filtered_questions[current_index - 1]["question_id"], current_index)

with next_col:
    if st.button("下一题", use_container_width=True, disabled=current_index == len(filtered_questions) - 1):
        go_to_question(filtered_questions[current_index + 1]["question_id"], current_index + 2)

with st.expander("题号跳转", expanded=False):
    st.caption("支持数字跳转和导航矩阵。")
    jump_left, jump_right = st.columns([1, 2])
    with jump_left:
        target_position = st.number_input(
            "跳转到第几题",
            min_value=1,
            max_value=len(filtered_questions),
            value=current_index + 1,
            step=1,
            key="quiz_target_position",
        )
        if st.button("跳转", use_container_width=True):
            go_to_question(filtered_questions[target_position - 1]["question_id"], target_position)

    with jump_right:
        grid_columns = st.columns(8)
        for index, question in enumerate(filtered_questions, start=1):
            state = get_question_state(question["question_id"])
            symbol = "·"
            if question["question_id"] == current_qid:
                symbol = "▶"
            elif state["last_is_correct"]:
                symbol = "✓"
            elif state["ever_wrong"] or state["last_is_correct"] is False:
                symbol = "✗"
            with grid_columns[(index - 1) % 8]:
                if st.button(f"{symbol}{index}", key=f"quiz-nav-{question['question_id']}"):
                    go_to_question(question["question_id"], index)
