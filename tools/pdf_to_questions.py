import argparse
import json
import re
from pathlib import Path

import fitz
import numpy as np
from pypdf import PdfReader

OPTION_RE = re.compile(r"^\s*([ABCD])[\.\)]\s*(.*)$", re.IGNORECASE)
QUESTION_RE = re.compile(r"^\s*(\d+)[\.\)]\s+(.*)$")
ANSWER_RE = re.compile(r"^\s*Correct\s*Answer\s*:\s*([ABCD])\s*$", re.IGNORECASE)


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def yellow_ratio_for_bbox(page: fitz.Page, bbox: tuple[float, float, float, float]) -> float:
    zoom = 2.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)

    x0, y0, x1, y1 = bbox
    ix0 = max(0, int(x0 * zoom))
    iy0 = max(0, int(y0 * zoom))
    ix1 = min(pix.width, int(x1 * zoom))
    iy1 = min(pix.height, int(y1 * zoom))
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0

    roi = arr[iy0:iy1, ix0:ix1]
    yellow = (
        (roi[:, :, 0] > 180)
        & (roi[:, :, 1] > 160)
        & (roi[:, :, 2] < 170)
    )
    return float(yellow.mean()) if yellow.size else 0.0


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_from_text_with_answer_key(pdf_path: Path, week: int) -> list[dict]:
    text = extract_text(pdf_path)
    lines = [normalize(x) for x in text.splitlines() if normalize(x)]
    parsed = []

    qnum = None
    qtext = ""
    options: list[str] = []
    answer_letter = None

    def flush():
        nonlocal qnum, qtext, options, answer_letter
        if qnum is None or len(options) != 4 or not answer_letter:
            qnum = None
            qtext = ""
            options = []
            answer_letter = None
            return
        answer_index = "ABCD".index(answer_letter.upper())
        parsed.append(
            {
                "id": f"W{week:02d}Q{qnum:02d}",
                "week": week,
                "question": normalize(qtext),
                "options": [normalize(o) for o in options],
                "answer_index": answer_index,
                "explanation": "",
                "source": pdf_path.name,
                "answer_source": "explicit_correct_answer_line",
                "answer_confidence": "high",
            }
        )
        qnum = None
        qtext = ""
        options = []
        answer_letter = None

    for line in lines:
        qm = QUESTION_RE.match(line)
        if qm:
            flush()
            qnum = int(qm.group(1))
            qtext = qm.group(2)
            continue

        om = OPTION_RE.match(line)
        if om and qnum is not None:
            options.append(om.group(2))
            continue

        am = ANSWER_RE.match(line)
        if am and qnum is not None:
            answer_letter = am.group(1).upper()
            flush()
            continue

        if qnum is not None and len(options) == 0:
            if "NPTEL Online Certification Course" not in line and "Page" not in line:
                qtext = f"{qtext} {line}".strip()
        elif qnum is not None and 0 < len(options) < 4:
            if "NPTEL Online Certification Course" not in line and "Page" not in line:
                options[-1] = f"{options[-1]} {line}".strip()

    flush()
    return parsed


def extract_lines_with_bbox(page: fitz.Page) -> list[dict]:
    blocks = page.get_text("dict").get("blocks", [])
    lines = []
    for b in blocks:
        for line in b.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(s.get("text", "") for s in spans)
            if not text.strip():
                continue
            x0 = min(s["bbox"][0] for s in spans)
            y0 = min(s["bbox"][1] for s in spans)
            x1 = max(s["bbox"][2] for s in spans)
            y1 = max(s["bbox"][3] for s in spans)
            lines.append({"text": text.strip(), "bbox": (x0, y0, x1, y1)})
    lines.sort(key=lambda x: (x["bbox"][1], x["bbox"][0]))
    return lines


def parse_assignment(pdf_path: Path, week: int) -> list[dict]:
    from_text = parse_from_text_with_answer_key(pdf_path, week)
    if len(from_text) >= 10:
        return from_text

    doc = fitz.open(pdf_path)
    parsed = []
    qnum = None
    qtext = ""
    options = []
    option_bboxes = []

    def flush():
        nonlocal qnum, qtext, options, option_bboxes
        if qnum is None or len(options) != 4:
            return
        ratios = [yellow_ratio_for_bbox(doc[pg], bb) for pg, bb in option_bboxes]
        answer_index = int(np.argmax(ratios)) if ratios else 0
        confidence = "high" if max(ratios) > 0.03 else "low"
        parsed.append(
            {
                "id": f"W{week:02d}Q{qnum:02d}",
                "week": week,
                "question": normalize(qtext),
                "options": [normalize(o) for o in options],
                "answer_index": answer_index,
                "explanation": "",
                "source": pdf_path.name,
                "answer_source": "yellow_highlight_detected",
                "answer_confidence": confidence,
            }
        )
        qnum = None
        qtext = ""
        options = []
        option_bboxes = []

    for pi, page in enumerate(doc):
        for line in extract_lines_with_bbox(page):
            text = line["text"]
            qm = QUESTION_RE.match(text)
            if qm:
                flush()
                qnum = int(qm.group(1))
                qtext = qm.group(2)
                continue
            om = OPTION_RE.match(text)
            if om and qnum is not None:
                options.append(om.group(2))
                option_bboxes.append((pi, line["bbox"]))
                continue
            if qnum is not None and len(options) == 0:
                # Continuation of long question text before options start.
                if "NPTEL Online Certification Course" not in text and "Page" not in text:
                    qtext = f"{qtext} {text}".strip()
            elif qnum is not None and 0 < len(options) < 4:
                # Continuation line for current option.
                if "NPTEL Online Certification Course" not in text and "Page" not in text:
                    options[-1] = f"{options[-1]} {text}".strip()

    flush()
    doc.close()
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract MCQs and highlighted answers from PDFs.")
    parser.add_argument("--pdf-dir", required=True, help="Folder containing assignment PDFs")
    parser.add_argument("--output", default="data/questions.json", help="Output JSON path")
    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir)
    output_file = Path(args.output)

    all_questions = []
    for pdf in sorted(pdf_dir.glob("Assignment *.pdf")):
        week_match = re.search(r"(\d+)", pdf.stem)
        if not week_match:
            print(f"Skipping (week not found in filename): {pdf.name}")
            continue
        week = int(week_match.group(1))
        qs = parse_assignment(pdf, week=week)
        print(f"{pdf.name}: parsed {len(qs)} questions")
        all_questions.extend(qs)

    all_questions.sort(key=lambda q: (q["week"], q["id"]))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(all_questions)} questions to {output_file}")
    print("Review entries with answer_confidence='low'.")


if __name__ == "__main__":
    main()
