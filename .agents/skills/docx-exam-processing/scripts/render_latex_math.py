"""把 docx 中的 LaTeX 字面量渲染为 Word 原生公式（OMML）。

用法：
    python render_latex_math.py <docx> [--out NEW.docx | --in-place] [--dry-run]
        [--xsl MML2OMML.XSL] [--katex PATH] [--no-o-notation] [--no-center-display]
        [--strip-dollar]

管线：LaTeX 片段 -> KaTeX(MathML, Node) -> MML2OMML.XSL(lxml) -> m:oMath 插入段落。
依赖：python-docx、lxml、Node+katex（见 katex_batch.js）、本机 Office 的 MML2OMML.XSL。

副作用：默认写出到 <原名>-公式.docx；--in-place 时先备份为 <原名>.公式.bak.docx。
切分失败的片段保留原 LaTeX 文本并在报告中列出（预期 0 处）。
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import docx
from docx.oxml.ns import qn
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from docx_common import (  # noqa: E402
    build_omml,
    find_xsl,
    iter_paragraphs,
    resolve_outputs,
    rewrite_paragraph,
    spans_of,
)

SCRIPT_DIR = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx")
    ap.add_argument("--out")
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="只统计切分结果，不写文件")
    ap.add_argument("--xsl", help="MML2OMML.XSL 路径")
    ap.add_argument("--katex", help="katex 模块路径（传给 katex_batch.js）")
    ap.add_argument("--no-o-notation", action="store_true", help="不把 O(...) 视为公式")
    ap.add_argument("--no-center-display", action="store_true", help="整段公式不居中")
    ap.add_argument("--strip-dollar", action="store_true", help='删除残留的 "$" 字符')
    args = ap.parse_args()

    src = Path(args.docx)
    out, backup = resolve_outputs(src, args.out, args.in_place, "公式")
    d = docx.Document(str(src))

    targets = []
    unique = set()
    for p in iter_paragraphs(d):
        text = p.text
        sp = spans_of(text, o_notation=not args.no_o_notation)
        if sp or (args.strip_dollar and "$" in text):
            targets.append((p, text, sp))
            unique.update(tex for _, _, tex in sp)
    print("涉及段落:", len(targets), "| 不同公式片段:", len(unique))
    if args.dry_run:
        print("dry-run，未写文件")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        spans_json = Path(tmp) / "spans.json"
        mathml_json = Path(tmp) / "mathml.json"
        spans_json.write_text(json.dumps(sorted(unique), ensure_ascii=False), encoding="utf-8")
        cmd = ["node", str(SCRIPT_DIR / "katex_batch.js"), str(spans_json), str(mathml_json)]
        if args.katex:
            cmd += ["--katex", args.katex]
        subprocess.run(cmd, check=True)
        mathml = json.loads(mathml_json.read_text(encoding="utf-8"))

    xslt = etree.XSLT(etree.parse(str(find_xsl(args.xsl))))
    cache = {}
    failed = []
    inserted = rebuilt = centered = skipped = 0
    dollars = 0
    for p, text, sp in targets:
        dollars += text.count("$")
        if not sp:
            for r in p.runs:
                if "$" in r.text:
                    r.text = r.text.replace("$", "")
            continue

        def omml_of(tex):
            if tex not in cache:
                cache[tex] = build_omml(tex, mathml, xslt)
            return cache[tex]

        n, fail, ok = rewrite_paragraph(
            p, sp, omml_of, text_fix="$" if args.strip_dollar else None
        )
        failed.extend(fail)
        if not ok:
            skipped += 1
            print("  ! 段落含 tab/图片等 run，未替换:", text[:40])
            continue
        inserted += n
        rebuilt += 1
        if not args.no_center_display and len(sp) == 1 and sp[0][2] == text.strip():
            pPr = p._p.get_or_add_pPr()
            jc = pPr.find(qn("w:jc"))
            if jc is None:
                jc = pPr.makeelement(qn("w:jc"), {})
                pPr.append(jc)
            jc.set(qn("w:val"), "center")
            ind = pPr.find(qn("w:ind"))
            if ind is None:
                ind = pPr.makeelement(qn("w:ind"), {})
                pPr.append(ind)
            ind.set(qn("w:left"), "0")
            ind.set(qn("w:leftChars"), "0")
            centered += 1

    d.save(str(out))
    print(f"重写段落 {rebuilt} | 插入公式 {inserted} | 整段公式居中 {centered} | 跳过 {skipped}")
    print(f'删除残留 "$": {dollars} | 转换失败: {len(failed)}')
    for tex in failed[:20]:
        print("   FAIL", repr(tex[:60]))
    if backup:
        print("备份:", backup)
    print("输出:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
