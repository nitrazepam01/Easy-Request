from __future__ import annotations

from datetime import datetime

import streamlit as st

from lib.auth import current_user, require_login
from lib.data import load_question_bank
from lib.exporters import build_wrong_questions_docx
from lib.persistence import get_backend_status, save_question_state, save_user_state, utcnow_iso
from lib.session import ensure_runtime_state, get_question_state, set_question_state
from lib.ui import (
    apply_theme,
    render_hero,
    render_question_card,
    render_status_pills,
    section_heading,
    setup_page,
    sidebar_profile,
)


setup_page("错题本 | 医学伦理复习平台", "📕")
apply_theme()
ensure_runtime_state()
auth = require_login()
backend_status = get_backend_status()
sidebar_profile(auth, backend_status)

questions = load_question_bank()
wrong_questions = [
    question
    for question in questions
    if (state := get_question_state(question["question_id"]))["ever_wrong"] and not state["mastered"]
]

st.session_state["user_state"] = {
    "current_page": "错题本",
    "current_question_id": st.session_state["user_state"].get("current_question_id"),
    "active_source": st.session_state["user_state"].get("active_source", "全部题库"),
    "active_filters": st.session_state["user_state"].get("active_filters", {}),
}
save_user_state(auth["nickname_norm"], st.session_state["user_state"])

render_hero(
    "错题复盘页",
    "这里只保留“曾经答错且尚未标记为已掌握”的题。你可以继续重做、查看最近一次错误答案，或者手动把已经吃透的题移出错题本。",
    "Wrong Book",
)

top1, top2, top3 = st.columns(3)
top1.metric("待复盘错题", len(wrong_questions))
top2.metric(
    "已掌握错题",
    sum(1 for question in questions if get_question_state(question["question_id"])["mastered"]),
)
top3.metric(
    "曾经做错过",
    sum(1 for question in questions if get_question_state(question["question_id"])["ever_wrong"]),
)

if not wrong_questions:
    st.success("目前错题本是空的，可以继续刷题把状态积累起来。")
    st.page_link("pages/1_刷题.py", label="去刷题", icon="📝")
    st.stop()

export_buffer = build_wrong_questions_docx(
    auth["nickname_display"],
    wrong_questions,
    st.session_state["question_states"],
)
st.download_button(
    "导出当前错题为 DOCX",
    data=export_buffer.getvalue(),
    file_name=f"医学伦理错题本_{auth['nickname_display']}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    use_container_width=True,
)

if "wrong_current_qid" not in st.session_state or not any(
    question["question_id"] == st.session_state["wrong_current_qid"] for question in wrong_questions
):
    st.session_state["wrong_current_qid"] = wrong_questions[0]["question_id"]

current_index = next(
    index
    for index, question in enumerate(wrong_questions)
    if question["question_id"] == st.session_state["wrong_current_qid"]
)
current_question = wrong_questions[current_index]
current_qid = current_question["question_id"]
question_state = get_question_state(current_qid)

render_question_card(current_question, current_index + 1, len(wrong_questions))
render_status_pills(
    [
        (f"作答次数 {question_state['attempt_count']}", "default"),
        (f"累计错题 {question_state['wrong_count']}", "wrong"),
        (
            f"最近一次错误答案 {question_state['last_wrong_selected'] or '暂无'}",
            "wrong",
        ),
    ]
)

option_labels = [f"{option['key']}. {option['text']}" for option in current_question["options"]]
label_to_key = {label: option["key"] for label, option in zip(option_labels, current_question["options"])}
selected_key = question_state.get("last_selected")
selected_index = next(
    (index for index, option in enumerate(current_question["options"]) if option["key"] == selected_key),
    None,
)

choice = st.radio(
    "重新作答",
    option_labels,
    index=selected_index,
    key=f"wrong_radio_{current_qid}",
)

action1, action2, action3 = st.columns(3)
with action1:
    if st.button("提交复盘答案", type="primary", use_container_width=True):
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
                "ever_wrong": True,
                "updated_at": utcnow_iso(),
            },
        )
        save_question_state(auth["nickname_norm"], current_qid, new_state)
        if is_correct:
            st.success(f"这次答对了，正确答案是 {current_question['answer']}。")
        else:
            st.error(
                f"这次仍然错误，你选择了 {chosen_key}，正确答案是 {current_question['answer']}。"
            )
        st.rerun()

with action2:
    if st.button("标记已掌握", use_container_width=True):
        new_state = set_question_state(
            current_qid,
            {
                "mastered": True,
                "updated_at": utcnow_iso(),
            },
        )
        save_question_state(auth["nickname_norm"], current_qid, new_state)
        st.success("题目已移出错题本。")
        st.rerun()

with action3:
    if st.button("恢复到错题本", use_container_width=True, disabled=not question_state["mastered"]):
        new_state = set_question_state(
            current_qid,
            {
                "mastered": False,
                "updated_at": utcnow_iso(),
            },
        )
        save_question_state(auth["nickname_norm"], current_qid, new_state)
        st.success("题目已重新放回错题本。")
        st.rerun()

section_heading("错题导航", "这里只导航当前仍在错题本中的题目。")
nav_cols = st.columns(8)
for index, question in enumerate(wrong_questions, start=1):
    state = get_question_state(question["question_id"])
    symbol = "▶" if question["question_id"] == current_qid else "✗"
    if state["last_is_correct"]:
        symbol = "✓" if question["question_id"] != current_qid else "▶"
    with nav_cols[(index - 1) % 8]:
        if st.button(f"{symbol}{index}", key=f"wrong-nav-{question['question_id']}"):
            st.session_state["wrong_current_qid"] = question["question_id"]
            st.rerun()
