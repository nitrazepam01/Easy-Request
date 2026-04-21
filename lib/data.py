from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
QUESTION_BANK_PATH = ROOT / "data" / "question_bank.json"


@lru_cache(maxsize=1)
def load_question_bank() -> list[dict[str, Any]]:
    with QUESTION_BANK_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def question_lookup() -> dict[str, dict[str, Any]]:
    return {question["question_id"]: question for question in load_question_bank()}


def unique_source_docs(questions: list[dict[str, Any]]) -> list[str]:
    return sorted({question["source_doc"] for question in questions})


def unique_question_types(questions: list[dict[str, Any]]) -> list[str]:
    return sorted({question["question_type"] for question in questions})


def unique_sections(questions: list[dict[str, Any]], source_doc: str = "全部题库") -> list[str]:
    scoped = questions if source_doc == "全部题库" else [
        question for question in questions if question["source_doc"] == source_doc
    ]
    return sorted({question["section_title"] for question in scoped})


def filter_questions(
    questions: list[dict[str, Any]],
    source_doc: str = "全部题库",
    section_title: str = "全部章节",
    question_type: str = "全部题型",
) -> list[dict[str, Any]]:
    scoped = questions
    if source_doc != "全部题库":
        scoped = [question for question in scoped if question["source_doc"] == source_doc]
    if section_title != "全部章节":
        scoped = [question for question in scoped if question["section_title"] == section_title]
    if question_type != "全部题型":
        scoped = [question for question in scoped if question["question_type"] == question_type]
    return scoped


def count_by_source(questions: list[dict[str, Any]]) -> Counter:
    return Counter(question["source_doc"] for question in questions)


def count_by_type(questions: list[dict[str, Any]]) -> Counter:
    return Counter(question["question_type"] for question in questions)
