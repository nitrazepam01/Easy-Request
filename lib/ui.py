from __future__ import annotations

import html

import streamlit as st


def setup_page(title: str, icon: str) -> None:
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Noto+Serif+SC:wght@400;500;600;700;900&display=swap');

        :root {
            --paper: #f7f1e4;
            --paper-edge: #e4d8c2;
            --ink: #1f2828;
            --muted: #6e6a61;
            --wine: #8f2f2f;
            --green: #2f5c50;
            --gold: #aa8a4d;
            --card: rgba(253, 248, 238, 0.86);
            --card-deep: rgba(248, 241, 228, 0.95);
            --shadow: 0 20px 60px rgba(38, 32, 20, 0.12);
            --line: rgba(59, 47, 31, 0.12);
        }

        html, body, [data-testid="stAppViewContainer"] {
            font-family: "Noto Serif SC", "Palatino Linotype", serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(143, 47, 47, 0.10), transparent 32%),
                radial-gradient(circle at 85% 12%, rgba(47, 92, 80, 0.12), transparent 28%),
                linear-gradient(180deg, #fbf7ef 0%, #f2ead7 100%);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(41, 32, 24, 0.88), rgba(24, 29, 28, 0.94)),
                radial-gradient(circle at top, rgba(170, 138, 77, 0.18), transparent 38%);
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        [data-testid="stSidebar"] * {
            color: #f4ede0;
        }

        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }

        .hero-shell, .paper-card, .question-card, .metric-card, .status-card {
            background: var(--card);
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
            border-radius: 28px;
            position: relative;
            overflow: hidden;
        }

        .hero-shell::before, .paper-card::before, .question-card::before,
        .metric-card::before, .status-card::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(135deg, rgba(170, 138, 77, 0.08), transparent 35%),
                repeating-linear-gradient(
                    0deg,
                    rgba(110, 106, 97, 0.03),
                    rgba(110, 106, 97, 0.03) 1px,
                    transparent 1px,
                    transparent 28px
                );
            pointer-events: none;
        }

        .hero-shell {
            padding: 1.8rem 2rem;
            margin-bottom: 1rem;
        }

        .eyebrow {
            color: var(--wine);
            font-size: 0.88rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 0.6rem;
        }

        .hero-title {
            font-family: "Cormorant Garamond", "Noto Serif SC", serif;
            font-size: 3rem;
            line-height: 0.95;
            margin: 0;
            color: var(--ink);
        }

        .hero-subtitle {
            margin-top: 0.9rem;
            max-width: 48rem;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.8;
        }

        .paper-card, .question-card, .status-card {
            padding: 1.25rem 1.4rem;
            margin-bottom: 1rem;
        }

        .metric-card {
            padding: 1rem 1.1rem;
            min-height: 132px;
        }

        .metric-kicker {
            color: var(--muted);
            font-size: 0.86rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        .metric-value {
            font-size: 2rem;
            color: var(--ink);
            font-weight: 700;
            line-height: 1;
            margin-bottom: 0.35rem;
        }

        .metric-note {
            color: var(--muted);
            font-size: 0.93rem;
            line-height: 1.6;
        }

        .tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-bottom: 1rem;
        }

        .tag {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.38rem 0.8rem;
            border-radius: 999px;
            background: rgba(47, 92, 80, 0.08);
            color: var(--green);
            border: 1px solid rgba(47, 92, 80, 0.18);
            font-size: 0.88rem;
        }

        .tag.is-wine {
            background: rgba(143, 47, 47, 0.08);
            color: var(--wine);
            border-color: rgba(143, 47, 47, 0.16);
        }

        .question-title {
            font-size: 1.45rem;
            font-weight: 700;
            line-height: 1.65;
            margin: 0 0 1rem;
        }

        .support-copy {
            color: var(--muted);
            line-height: 1.7;
        }

        .status-pill {
            display: inline-block;
            padding: 0.34rem 0.82rem;
            border-radius: 999px;
            font-size: 0.86rem;
            border: 1px solid var(--line);
            background: rgba(255,255,255,0.54);
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
        }

        .status-pill.correct {
            color: var(--green);
            border-color: rgba(47, 92, 80, 0.22);
            background: rgba(47, 92, 80, 0.08);
        }

        .status-pill.wrong {
            color: var(--wine);
            border-color: rgba(143, 47, 47, 0.18);
            background: rgba(143, 47, 47, 0.08);
        }

        div[data-testid="stForm"],
        div[data-testid="stMetric"],
        div[data-testid="stDataFrame"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 22px !important;
        }

        div[data-testid="stForm"] {
            background: var(--card-deep);
            border: 1px solid var(--line);
            padding: 1rem 1rem 0.6rem;
            box-shadow: var(--shadow);
        }

        .stTextInput input, .stSelectbox select, .stNumberInput input {
            border-radius: 16px !important;
            background: rgba(255,255,255,0.7) !important;
            border: 1px solid rgba(59, 47, 31, 0.16) !important;
        }

        .stRadio > div {
            gap: 0.75rem;
        }

        .stRadio label {
            border: 1px solid rgba(59, 47, 31, 0.12);
            background: rgba(255,255,255,0.62);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }

        .stRadio label:hover {
            transform: translateY(-1px);
            border-color: rgba(47, 92, 80, 0.28);
            box-shadow: 0 10px 24px rgba(29, 24, 20, 0.08);
        }

        .stButton > button, .stDownloadButton > button {
            border-radius: 999px !important;
            padding: 0.62rem 1.15rem !important;
            border: 1px solid rgba(59, 47, 31, 0.14) !important;
            background: linear-gradient(180deg, #fbf6ed, #eadfc9) !important;
            color: var(--ink) !important;
            font-weight: 700 !important;
            box-shadow: 0 10px 24px rgba(52, 42, 29, 0.10);
        }

        .stButton > button[kind="primary"], .stFormSubmitButton > button {
            background: linear-gradient(180deg, #2f5c50, #22483f) !important;
            color: #fffdf7 !important;
            border-color: rgba(255,255,255,0.12) !important;
        }

        .nav-note {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.7;
        }

        .section-heading {
            font-family: "Cormorant Garamond", "Noto Serif SC", serif;
            color: var(--ink);
            font-size: 2rem;
            margin-bottom: 0.25rem;
        }

        .divider {
            height: 1px;
            background: linear-gradient(90deg, rgba(143,47,47,0), rgba(143,47,47,0.25), rgba(143,47,47,0));
            margin: 0.8rem 0 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str, eyebrow: str) -> None:
    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="eyebrow">{html.escape(eyebrow)}</div>
            <h1 class="hero-title">{html.escape(title)}</h1>
            <p class="hero-subtitle">{html.escape(subtitle)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(kicker: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <section class="metric-card">
            <div class="metric-kicker">{html.escape(kicker)}</div>
            <div class="metric-value">{html.escape(value)}</div>
            <div class="metric-note">{html.escape(note)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_question_card(question: dict, position: int, total: int) -> None:
    tags = [
        f'<span class="tag">{html.escape(question["source_doc"])}</span>',
        f'<span class="tag">{html.escape(question["section_title"])}</span>',
        f'<span class="tag is-wine">{html.escape(question["question_type"])}</span>',
    ]
    if question.get("group_range"):
        tags.append(f'<span class="tag">共用备选 {html.escape(question["group_range"])}</span>')

    st.markdown(
        f"""
        <section class="question-card">
            <div class="tag-row">{''.join(tags)}</div>
            <p class="support-copy">当前位次：第 {position} / {total} 题</p>
            <h2 class="question-title">{html.escape(question["stem"])}</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_status_pills(items: list[tuple[str, str]]) -> None:
    classes = {
        "correct": "status-pill correct",
        "wrong": "status-pill wrong",
    }
    html_items = []
    for label, variant in items:
        css = classes.get(variant, "status-pill")
        html_items.append(f'<span class="{css}">{html.escape(label)}</span>')
    st.markdown("".join(html_items), unsafe_allow_html=True)


def sidebar_profile(auth: dict, backend_status: dict) -> None:
    with st.sidebar:
        st.markdown("### 复习档案")
        if auth.get("nickname_display"):
            st.write(f"**当前昵称**：{auth['nickname_display']}")
            st.write(f"**同步模式**：{'云端' if backend_status['available'] else '本地会话'}")
        st.caption(backend_status["reason"])


def section_heading(title: str, note: str = "") -> None:
    st.markdown(f'<div class="section-heading">{html.escape(title)}</div>', unsafe_allow_html=True)
    if note:
        st.caption(note)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
