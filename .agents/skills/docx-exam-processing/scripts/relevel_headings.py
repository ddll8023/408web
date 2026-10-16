"""按章节编号重排标题级别：章节 1→H1、2.1→H2、3.1.1→H3，题目=所属章节+1，题内子标题整体跟随。

用法：
    python relevel_headings.py <docx> [--out NEW.docx | --in-place] [--dry-run]
        [--question-re REGEX] [--chapter-re REGEX]

依赖：python-docx。默认写出到 <原名>-标题层级.docx，不覆盖原文件。
仅改段落样式（pStyle），不改文字、图片、表格与样式表。
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import docx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_common import DEFAULT_CHAPTER_RE, DEFAULT_QUESTION_RE  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx")
    ap.add_argument("--out")
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--question-re", default=DEFAULT_QUESTION_RE)
    ap.add_argument("--chapter-re", default=DEFAULT_CHAPTER_RE)
    args = ap.parse_args()

    src = Path(args.docx)
    out = src if args.in_place else Path(args.out) if args.out else src.with_name(
        f"{src.stem}-标题层级{src.suffix}"
    )
    q_re = re.compile(args.question_re)
    c_re = re.compile(args.chapter_re)

    d = docx.Document(str(src))
    styles = {n: d.styles[f"Heading {n}"] for n in range(1, 10)}

    chapter_depth = 0
    question_level = 0
    changed = 0
    target_dist = Counter()
    for p in d.paragraphs:
        if not p.style.name.startswith("Heading "):
            continue
        level = int(p.style.name.split()[1])
        text = p.text.strip()
        if level == 1:
            if q_re.match(text):
                question_level = chapter_depth + 1
                target = question_level
            elif c_re.match(text):
                chapter_depth = len(text.split()[0].split("."))
                target = chapter_depth
            else:
                continue
        else:
            target = question_level + level - 1
        target_dist[target] += 1
        if target != level and not args.dry_run:
            p.style = styles[target]
            changed += 1
    print("目标层级分布:", dict(sorted(target_dist.items())))
    print("调整段落:", changed, "| dry-run:", args.dry_run)
    if not args.dry_run:
        d.save(str(out))
        print("输出:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
