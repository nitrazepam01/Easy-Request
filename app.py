from __future__ import annotations

from collections import Counter

import streamlit as st

from lib.auth import current_user, is_authenticated, login_hint, login_user, logout_user
from lib.data import count_by_source, load_question_bank
from lib.persistence import get_backend_status
from lib.session import ensure_runtime_state
from lib.ui import apply_theme, render_hero, render_metric_card, setup_page, sidebar_profile


setup_page("医学伦理复习平台", "📚")
apply_theme()
ensure_runtime_state()

questions = load_question_bank()
st.session_state["question_bank_ready"] = True
st.session_state["backend_status"] = get_backend_status()

auth = current_user()
sidebar_profile(auth, st.session_state["backend_status"])

render_hero(
    "医学伦理学复习档案",
    "把两份 Word 题库整理成可持续刷题、错题复盘与云端进度恢复的一站式平台。首页负责进入身份与查看整体概况，其余页面专注学习流本身。",
    "Ethics Revision Archive",
)

source_counts = count_by_source(questions)
col1, col2, col3 = st.columns(3)
with col1:
    render_metric_card("题库总量", str(len(questions)), "两份 DOCX 已合并入统一题库，但保留原始来源标签。")
with col2:
    render_metric_card(
        "章节练习",
        str(source_counts.get("伦理章节测.docx", 0)),
        "按六个单元组织，适合章节回顾。",
    )
with col3:
    render_metric_card(
        "自测题库",
        str(source_counts.get("南京医科大学医学伦理学自测题库.docx", 0)),
        "覆盖 A1 / A2 / B1 多种题型。",
    )

left, right = st.columns([1.2, 1])

with left:
    st.markdown("### 进入平台")
    st.caption(login_hint())
    with st.form("login-form", clear_on_submit=False):
        invite_code = st.text_input("邀请码", placeholder="请输入统一邀请码")
        nickname = st.text_input("昵称", placeholder="例如：小林 / 临床一班-阿周")
        submitted = st.form_submit_button("进入复习平台", use_container_width=True)
        if submitted:
            ok, message = login_user(invite_code, nickname)
            if ok:
                st.success(message)
                st.rerun()
            st.error(message)

    if is_authenticated():
        st.success(f"当前已登录：{auth['nickname_display']}")
        quick1, quick2, quick3 = st.columns(3)
        with quick1:
            st.page_link("pages/1_刷题.py", label="去刷题", icon="📝")
        with quick2:
            st.page_link("pages/2_错题本.py", label="去错题本", icon="📕")
        with quick3:
            st.page_link("pages/3_进度.py", label="看进度", icon="📈")
        if st.button("退出当前昵称", use_container_width=True):
            logout_user()
            st.rerun()

with right:
    st.markdown("### 本平台包含")
    st.markdown(
        """
        <section class="paper-card">
            <ul class="support-copy">
                <li>题号跳转、上一题 / 下一题、导航矩阵</li>
                <li>错题自动沉淀到错题本，并支持导出 DOCX</li>
                <li>用 Supabase 保存进度与错题，换设备也能继续</li>
                <li>基于纸本文献 / 医学档案风格定制界面，而不是默认 Streamlit 面板</li>
            </ul>
        </section>
        """,
        unsafe_allow_html=True,
    )

    type_counts = Counter(question["question_type"] for question in questions)
    st.markdown("### 题型概览")
    st.dataframe(
        [{"题型": key, "数量": value} for key, value in sorted(type_counts.items())],
        use_container_width=True,
        hide_index=True,
    )
