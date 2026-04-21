from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "question_bank.json"
DOC1 = ROOT / "伦理章节测.docx"
DOC2 = ROOT / "南京医科大学医学伦理学自测题库.docx"

OPTION_RE = re.compile(r"^([A-E])[、.．]\s*(.+)$")
ANSWER_RE = re.compile(r"^答案[:：]\s*([A-E])$")
GROUP_RANGE_RE = re.compile(r"^[（(]\s*(\d+)\s*[—-]\s*(\d+)\s*题.*备选答案[）)]$")
MATCH_PROMPT_RE = re.compile(r"^\((\d+)\)\s*(.+)$")
MATCH_ANSWER_RE = re.compile(r"\((\d+)\)\s*([A-E])")
QUESTION_PREFIX_RE = re.compile(r"^(?P<num>\d+)\.?(?P<body>.+)$")
ANSWER_TOKEN_RE = re.compile(r"(?<!\S)([A-E])(?!\S)")
A3_GROUP_RE = re.compile(r"^[（(]\s*(\d+)\s*[—-]\s*(\d+)\s*题共用题干[）)]$")
SECTION_HEADERS = {"A1型题", "A2型题", "A3型题", "B1型题"}
TRAILING_ANSWER_RE = re.compile(r"^(?P<stem>.+?)(?P<answer>[A-E])$")


def normalize_text(text: str) -> str:
    cleaned = text.replace("\u00a0", " ").replace("\u3000", " ").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s*([，。；：？！）])", r"\1", cleaned)
    cleaned = re.sub(r"([（])\s*", r"\1", cleaned)
    return cleaned.strip()


def load_paragraphs(path: Path) -> list[str]:
    doc = Document(path)
    return [normalize_text(paragraph.text) for paragraph in doc.paragraphs if paragraph.text.strip()]


def parse_chapter_bank() -> list[dict]:
    paragraphs = load_paragraphs(DOC1)
    questions: list[dict] = []
    section_title = ""
    current_type = "单选题"
    current: dict | None = None
    matching_group: dict | None = None

    for text in paragraphs:
        if text.startswith("第") and "单元" in text:
            section_title = text
            current_type = "单选题"
            continue
        if text in {"一、单选题", "单选题"}:
            current_type = "单选题"
            continue
        if text == "匹配题":
            current_type = "匹配题"
            matching_group = {
                "prompts": [],
                "options": [],
            }
            continue

        if current_type == "匹配题":
            if matching_group is None:
                raise ValueError("匹配题状态异常。")

            answer_text = text.replace("答案：", "").replace("答案:", "")
            prompt_match = MATCH_PROMPT_RE.match(text)
            option_match = OPTION_RE.match(text)

            if prompt_match:
                matching_group["prompts"].append(
                    {
                        "order": int(prompt_match.group(1)),
                        "stem": normalize_text(prompt_match.group(2)),
                    }
                )
                continue

            if option_match:
                matching_group["options"].append(
                    {
                        "key": option_match.group(1),
                        "text": normalize_text(option_match.group(2)),
                    }
                )
                continue

            if text.startswith("答案：") or text.startswith("答案:"):
                answers = {
                    int(order): answer
                    for order, answer in MATCH_ANSWER_RE.findall(answer_text)
                }
                if len(matching_group["options"]) != 5:
                    raise ValueError("匹配题选项数量异常。")
                if len(answers) != len(matching_group["prompts"]):
                    raise ValueError("匹配题答案数量与小题数量不一致。")

                for prompt in matching_group["prompts"]:
                    questions.append(
                        {
                            "source_doc": DOC1.name,
                            "bank_key": "chapter_review_bank",
                            "section_title": section_title,
                            "question_type": "匹配题",
                            "source_no": None,
                            "display_order": None,
                            "group_range": answer_text.replace(" ", ""),
                            "stem": prompt["stem"],
                            "options": list(matching_group["options"]),
                            "answer": answers[prompt["order"]],
                        }
                    )
                matching_group = None
                current_type = "单选题"
                continue

            if matching_group["options"]:
                matching_group["options"][-1]["text"] = normalize_text(
                    f'{matching_group["options"][-1]["text"]} {text}'
                )
            elif matching_group["prompts"]:
                matching_group["prompts"][-1]["stem"] = normalize_text(
                    f'{matching_group["prompts"][-1]["stem"]} {text}'
                )
            continue

        answer_match = ANSWER_RE.match(text)
        if answer_match:
            if not current:
                raise ValueError("章节题库中出现了没有题干的答案标记。")
            current["answer"] = answer_match.group(1)
            current["stem"] = normalize_text(" ".join(current.pop("stem_lines")))
            if len(current["options"]) not in {4, 5}:
                raise ValueError(f"章节题库题目选项数量异常：{current['stem']}")
            questions.append(current)
            current = None
            continue

        option_match = OPTION_RE.match(text)
        if option_match:
            if not current:
                raise ValueError(f"章节题库选项缺少题干：{text}")
            current["options"].append(
                {"key": option_match.group(1), "text": normalize_text(option_match.group(2))}
            )
            continue

        if current is None:
            current = {
                "source_doc": DOC1.name,
                "bank_key": "chapter_review_bank",
                "section_title": section_title,
                "question_type": "单选题",
                "source_no": None,
                "display_order": None,
                "group_range": None,
                "stem_lines": [text],
                "options": [],
                "answer": None,
            }
            continue

        if current["options"]:
            current["options"][-1]["text"] = normalize_text(
                f'{current["options"][-1]["text"]} {text}'
            )
        else:
            current["stem_lines"].append(text)

    for index, question in enumerate(questions, start=1):
        question["source_no"] = str(index)
        type_key = "single" if question["question_type"] == "单选题" else "match"
        question["question_id"] = f"chapter_review-{type_key}-{index:03d}"
    return questions


def parse_a_type_question(paragraph: str) -> tuple[int, str, str]:
    match = QUESTION_PREFIX_RE.match(paragraph)
    if not match:
        raise ValueError(f"未能识别 A 型题题干：{paragraph}")

    body = normalize_text(match.group("body"))
    answer_matches = list(ANSWER_TOKEN_RE.finditer(body))
    if not answer_matches:
        raise ValueError(f"未能识别 A 型题答案：{paragraph}")

    answer_match = answer_matches[-1]
    answer = answer_match.group(1)
    stem = normalize_text(f"{body[:answer_match.start()]} {body[answer_match.end():]}")
    return int(match.group("num")), stem, answer


def split_question_prefix(paragraph: str) -> tuple[int, str] | None:
    match = QUESTION_PREFIX_RE.match(paragraph)
    if not match:
        return None
    return int(match.group("num")), normalize_text(match.group("body"))


def extract_answer_and_stem(text: str) -> tuple[str, str | None]:
    body = normalize_text(text)
    answer_matches = list(ANSWER_TOKEN_RE.finditer(body))
    if not answer_matches:
        trailing = TRAILING_ANSWER_RE.match(body)
        if not trailing:
            return body, None
        return normalize_text(trailing.group("stem")), trailing.group("answer")
    answer_match = answer_matches[-1]
    answer = answer_match.group(1)
    stem = normalize_text(f"{body[:answer_match.start()]} {body[answer_match.end():]}")
    return stem, answer


def looks_like_question_line(text: str) -> bool:
    prefix_match = QUESTION_PREFIX_RE.match(text)
    if not prefix_match:
        return False
    body = normalize_text(prefix_match.group("body"))
    return bool(ANSWER_TOKEN_RE.search(body))


def consume_question_block(
    paragraphs: list[str],
    start_index: int,
    current_type: str,
) -> tuple[int, str, str, list[dict], int]:
    prefix = split_question_prefix(paragraphs[start_index])
    if prefix is None:
        raise ValueError(f"{current_type} 题块起始位置不是题号行：{paragraphs[start_index]}")

    question_no, first_chunk = prefix
    stem_parts = []
    stem_chunk, answer = extract_answer_and_stem(first_chunk)
    if stem_chunk:
        stem_parts.append(stem_chunk)

    index = start_index + 1
    while answer is None and index < len(paragraphs):
        next_text = paragraphs[index]
        if next_text in SECTION_HEADERS or GROUP_RANGE_RE.match(next_text) or A3_GROUP_RE.match(next_text):
            raise ValueError(f"{current_type} 第 {question_no} 题缺少答案段。")
        if OPTION_RE.match(next_text):
            raise ValueError(f"{current_type} 第 {question_no} 题在答案出现前进入了选项段。")
        if split_question_prefix(next_text):
            raise ValueError(f"{current_type} 第 {question_no} 题在答案出现前进入了下一题。")

        stem_chunk, answer = extract_answer_and_stem(next_text)
        if stem_chunk:
            stem_parts.append(stem_chunk)
        index += 1

    options = []
    while index < len(paragraphs):
        next_text = paragraphs[index]
        if next_text in SECTION_HEADERS or GROUP_RANGE_RE.match(next_text) or A3_GROUP_RE.match(next_text):
            break
        if split_question_prefix(next_text):
            break

        option_match = OPTION_RE.match(next_text)
        if option_match:
            options.append(
                {
                    "key": option_match.group(1),
                    "text": normalize_text(option_match.group(2)),
                }
            )
            index += 1
            continue

        if options:
            options[-1]["text"] = normalize_text(f'{options[-1]["text"]} {next_text}')
            index += 1
            continue

        raise ValueError(f"{current_type} 第 {question_no} 题存在无法归类的内容：{next_text}")

    return question_no, normalize_text(" ".join(stem_parts)), answer or "", options, index


def parse_self_test_bank() -> list[dict]:
    paragraphs = load_paragraphs(DOC2)
    questions: list[dict] = []
    index = 0
    current_type = ""

    while index < len(paragraphs):
        text = paragraphs[index]
        if text in {"A1型题", "A2型题", "A3型题", "B1型题"}:
            current_type = text
            index += 1
            continue

        if current_type in {"A1型题", "A2型题"}:
            if text in {"南京医科大学医学伦理学自测题库"}:
                index += 1
                continue
            if split_question_prefix(text) is None:
                index += 1
                continue
            question_no, stem, answer, options, index = consume_question_block(
                paragraphs, index, current_type
            )
            if len(options) not in {4, 5}:
                raise ValueError(f"{current_type} 第 {question_no} 题选项数量异常。")

            questions.append(
                {
                    "question_id": f"nmu_self_test-{current_type[:2].lower()}-{question_no:03d}",
                    "source_doc": DOC2.name,
                    "bank_key": "nmu_self_test_bank",
                    "section_title": current_type,
                    "question_type": current_type,
                    "source_no": str(question_no),
                    "display_order": None,
                    "group_range": None,
                    "stem": stem,
                    "options": options,
                    "answer": answer,
                }
            )
            continue

        if current_type == "A3型题":
            group_match = A3_GROUP_RE.match(text)
            if not group_match:
                index += 1
                continue

            start_no = int(group_match.group(1))
            end_no = int(group_match.group(2))
            group_range = f"{start_no}-{end_no}"
            index += 1

            shared_stem_parts = []
            while index < len(paragraphs) and split_question_prefix(paragraphs[index]) is None:
                next_text = paragraphs[index]
                if next_text in SECTION_HEADERS or GROUP_RANGE_RE.match(next_text) or A3_GROUP_RE.match(next_text):
                    raise ValueError(f"A3 型题 {group_range} 缺少共用题干。")
                shared_stem_parts.append(next_text)
                index += 1

            shared_stem = normalize_text(" ".join(shared_stem_parts))

            for expected_no in range(start_no, end_no + 1):
                question_no, stem, answer, options, index = consume_question_block(
                    paragraphs, index, current_type
                )
                if question_no != expected_no:
                    raise ValueError(
                        f"A3 型题编号不连续，期望 {expected_no}，实际 {question_no}"
                    )
                if len(options) not in {4, 5}:
                    raise ValueError(f"A3 型题第 {question_no} 题选项数量异常。")
                questions.append(
                    {
                        "question_id": f"nmu_self_test-a3-{question_no:03d}",
                        "source_doc": DOC2.name,
                        "bank_key": "nmu_self_test_bank",
                        "section_title": current_type,
                        "question_type": current_type,
                        "source_no": str(question_no),
                        "display_order": None,
                        "group_range": group_range,
                        "stem": normalize_text(f"{shared_stem} {stem}"),
                        "options": options,
                        "answer": answer,
                    }
                )
            continue

        if current_type == "B1型题":
            group_match = GROUP_RANGE_RE.match(text)
            if not group_match:
                index += 1
                continue

            start_no = int(group_match.group(1))
            end_no = int(group_match.group(2))
            group_range = f"{start_no}-{end_no}"
            index += 1

            shared_options = []
            while index < len(paragraphs):
                option_match = OPTION_RE.match(paragraphs[index])
                if not option_match:
                    break
                shared_options.append(
                    {
                        "key": option_match.group(1),
                        "text": normalize_text(option_match.group(2)),
                    }
                )
                index += 1

            if len(shared_options) != 5:
                raise ValueError(f"B1 型题共用选项数量异常：{group_range}")

            for expected_no in range(start_no, end_no + 1):
                if index >= len(paragraphs):
                    raise ValueError(f"B1 型题 {group_range} 题组提前结束。")
                question_no, stem, answer = parse_a_type_question(paragraphs[index])
                if question_no != expected_no:
                    raise ValueError(
                        f"B1 型题编号不连续，期望 {expected_no}，实际 {question_no}"
                    )
                questions.append(
                    {
                        "question_id": f"nmu_self_test-b1-{question_no:03d}",
                        "source_doc": DOC2.name,
                        "bank_key": "nmu_self_test_bank",
                        "section_title": current_type,
                        "question_type": current_type,
                        "source_no": str(question_no),
                        "display_order": None,
                        "group_range": group_range,
                        "stem": stem,
                        "options": list(shared_options),
                        "answer": answer,
                    }
                )
                index += 1
            continue

        index += 1

    return questions


def build_question_bank() -> list[dict]:
    chapter_questions = parse_chapter_bank()
    self_test_questions = parse_self_test_bank()
    questions = chapter_questions + self_test_questions

    for display_order, question in enumerate(questions, start=1):
        question["display_order"] = display_order
    return questions


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    questions = build_question_bank()
    OUT_PATH.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"question_bank written: {OUT_PATH}")
    print(f"total={len(questions)}")


if __name__ == "__main__":
    main()
