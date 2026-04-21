from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
QUESTION_BANK = ROOT / "data" / "question_bank.json"


def main() -> None:
    questions = json.loads(QUESTION_BANK.read_text(encoding="utf-8"))
    if len(questions) != 256:
        raise SystemExit(f"题库数量错误：期望 256，实际 {len(questions)}")

    ids = [question["question_id"] for question in questions]
    if len(ids) != len(set(ids)):
        raise SystemExit("question_id 存在重复。")

    by_source = Counter(question["source_doc"] for question in questions)
    if by_source.get("伦理章节测.docx") != 62:
        raise SystemExit(f"伦理章节测.docx 数量错误：{by_source.get('伦理章节测.docx')}")
    if by_source.get("南京医科大学医学伦理学自测题库.docx") != 194:
        raise SystemExit(
            f"南京医科大学医学伦理学自测题库.docx 数量错误："
            f"{by_source.get('南京医科大学医学伦理学自测题库.docx')}"
        )

    for question in questions:
        required = {
            "question_id",
            "source_doc",
            "bank_key",
            "section_title",
            "question_type",
            "source_no",
            "display_order",
            "group_range",
            "stem",
            "options",
            "answer",
        }
        if set(question) != required:
            raise SystemExit(f"字段集合异常：{question['question_id']}")
        if question["answer"] not in {"A", "B", "C", "D", "E"}:
            raise SystemExit(f"答案异常：{question['question_id']}")
        option_keys = [option["key"] for option in question["options"]]
        expected_keys = ["A", "B", "C", "D"] if len(option_keys) == 4 else ["A", "B", "C", "D", "E"]
        if option_keys != expected_keys:
            raise SystemExit(f"选项异常：{question['question_id']}")

    b1_questions = [question for question in questions if question["question_type"] == "B1型题"]
    if not b1_questions:
        raise SystemExit("没有解析出 B1 型题。")

    a3_questions = [question for question in questions if question["question_type"] == "A3型题"]
    if len(a3_questions) != 5:
        raise SystemExit("A3 型题没有被正确识别成 5 题。")

    match_questions = [question for question in questions if question["question_type"] == "匹配题"]
    if len(match_questions) != 3:
        raise SystemExit("章节题库的匹配题没有被正确展开成 3 小题。")

    malformed_41 = [question for question in questions if question["source_no"] == "41"]
    if not malformed_41:
        raise SystemExit("缺少异常题号 41 的解析结果。")

    print("question_bank validation passed")
    print("counts by source:", dict(by_source))
    print(
        "counts by type:",
        dict(Counter(question["question_type"] for question in questions)),
    )


if __name__ == "__main__":
    main()
