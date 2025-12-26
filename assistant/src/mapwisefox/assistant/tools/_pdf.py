from pathlib import Path

import pymupdf
import re
import stopwords
from collections import defaultdict
import math

EN_STOPWORDS = stopwords.get_stopwords("english")
SENTENCE_TERMINATION_RE = re.compile(r"(?<=[.!?])\s+", re.M)
NON_SENTENCE_TERMINATION_RE = re.compile(r"(?<=[^\s.!?])\s+(?=[^\s.!?])", re.M)
LINE_NUMBERING_RE = re.compile(r"(\n|\s)\d+?(?:\n|$)", re.M)
BIBLIOGRAPHY_SECTION_RE = re.compile(r"\b(references|bibliography|文献)\b", re.I)
SECTION_HEADER_RE = re.compile(r"((?:(?:[IVXLCDM]+)|\d+)(?:[.)](?:[a-z]+|\d+|(?:ix|iv|v?i{0,3}|xl|xc|cd|cm|d?c{0,3})))*[.)\n])\s*([^\n.?!]{,50})(?:[\n.?!]|$)", re.M)


def _iter_lines(doc: pymupdf.Document):
    for page_index, page in enumerate(doc):
        page_height = page.rect.height
        page_width = page.rect.width
        raw = page.get_text("dict")
        for block_no, block in enumerate(raw.get("blocks", []), 1):
            for line_no, line in enumerate(block.get("lines", []), 1):
                x0, y0, x1, y1 = line["bbox"]
                spans = line.get("spans", [])
                text = "".join(span.get("text", "") for span in spans)
                if not text:
                    continue
                font_sizes = [span.get("size", 0) for span in spans if span.get("size")]
                max_font = max(font_sizes) if font_sizes else 0
                font_flags = [span.get("flags", 0) for span in spans]
                is_bold = any(f & 2 for f in font_flags)
                x_mid = (x0 + x1) / 2
                y_mid = (y0 + y1) / 2
                x_norm = x_mid / page_width
                y_norm = y_mid / page_height
                yield {
                    "page": page_index,
                    "text": text,
                    "norm": re.sub(r"[\\W\\d_]+", " ", text.lower()).strip(),
                    "bbox": (x0, y0, x1, y1),
                    "y_norm": y_norm,
                    "x_norm": x_norm,
                    "block_no": block_no,
                    "line_no": line_no,
                    "char_count": len(text),
                    "font_size": max_font,
                    "is_bold": is_bold,
                }


def _compute_flow_bounds(lines):
    ys = sorted(l["y_norm"] for l in lines)
    if not ys:
        return 0.0, 1.0
    lo = ys[int(len(ys) * 0.1)]
    hi = ys[int(len(ys) * 0.9)]
    return lo, hi


def _is_prose_line(text: str):
    if not text:
        return False
    n = len(text)
    if n < 20:
        return False

    alpha = sum(c.isalpha() for c in text)
    digit = sum(c.isdigit() for c in text)

    alpha_ratio = alpha / n
    digit_ratio = digit / n

    return alpha_ratio >= 0.5 and digit_ratio < 0.2


# Minimal section header detector: preserves headers even if not prose-like.
def _is_section_header(line, median_font_size):
    text = line["text"].strip()
    if not text:
        return False
    n = len(text)
    # short-ish, mostly alphabetic
    if n > 120:
        return False

    alpha_ratio = sum(c.isalpha() for c in text) / max(n, 1)
    if alpha_ratio < 0.5:
        return False

    is_bold = bool(line.get("is_bold", False))
    font_size = float(line.get("font_size", 0.0))

    return (
        font_size >= median_font_size * 1.3
        or
        (is_bold and font_size >= median_font_size)
    )


def _filter_out_of_flow_elements(lines, page_count):
    sig_pages = defaultdict(set)

    for l in lines:
        if not l.get("out_of_flow", False):
            continue
        y_bin = round(l["y_norm"] / 0.02)
        x_bin = round(l["x_norm"] / 0.05)
        sig = (y_bin, x_bin, l["norm"])
        sig_pages[sig].add(l["page"])

    repetitive = {
        sig for sig, pages in sig_pages.items()
        if len(pages) >= max(3, math.ceil(page_count * 0.3))
    }

    kept = []
    for l in lines:
        y_bin = round(l["y_norm"] / 0.02)
        x_bin = round(l["x_norm"] / 0.05)
        sig = (y_bin, x_bin, l["norm"])
        # remove repetitive headings
        if l.get("out_of_flow", False) and sig in repetitive:
            continue
        # remove page numbers
        if l.get("out_of_flow", False) and l["char_count"] <= 4 and l["text"].isdigit():
            continue
        kept.append(l)

    return kept

def extract_pdf_text(file: str | Path) -> str:
    with open(file, "rb") as fp:
        doc = pymupdf.Document(filename=fp)

    all_lines = list(_iter_lines(doc))
    page_count = doc.page_count

    by_page = defaultdict(list)
    for l in all_lines:
        by_page[l["page"]].append(l)

    filtered = []
    for page, lines in by_page.items():
        lo, hi = _compute_flow_bounds(lines)
        for l in lines:
            out_of_flow = l["y_norm"] < lo or l["y_norm"] > hi
            filtered.append({**l, "out_of_flow": out_of_flow})

    filtered = _filter_out_of_flow_elements(filtered, page_count)
    font_sizes = [l["font_size"] for l in filtered if l.get("font_size")]
    median_font = sorted(font_sizes)[len(font_sizes)//2] if font_sizes else 0
    filtered = [
        l for l in filtered
        if _is_prose_line(l["text"]) or _is_section_header(l, median_font)
    ]

    def _sort_key(l):
        return l["page"], l["block_no"], l["line_no"], l["x_norm"], l["y_norm"]

    filtered.sort(key=_sort_key)
    return "\n".join(l["text"] for l in filtered)
