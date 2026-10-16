"""docx 处理共享工具：段落遍历、LaTeX 片段切分、OMML 构建与关系清理。

依赖：python-docx、lxml（MML2OMML.XSL 由本机 Office 提供）。

约定：
- 所有函数只操作传入的 python-docx 对象，不读写磁盘；保存由调用方负责。
- LaTeX 片段切分采用启发式，规则与边界案例见 references/math-pipeline.md。
"""

import copy
import re
import shutil
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.text.run import Run
from lxml import etree

BS = chr(92)
CMD = re.compile(BS + BS + r"[a-zA-Z]+")
ASCII_OK = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    " \t()[]{}<>+-*/=.,:;|!?'\"&%~^_" + BS
)
MATH_SYM = set("∞≈≤≥→←×·√∑∏∫≠±∅∈∉⊆∪∩…∗⋅")
# 代码常量（LLONG_MAX、MAX_SIZE、含 ; / # / -> 的片段）不作为公式
CODE_LIKE = re.compile(r"[A-Z]{2,}_[A-Z]{2,}|[#;]|->")
# 大 O 记号：O(n)、O(1)、O(m+n) 等不含 LaTeX 命令的写法
O_PAT = re.compile(r"O\([^()\n]{1,40}\)")
WORD = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

DEFAULT_XSL_CANDIDATES = (
    r"C:\Program Files (x86)\Microsoft Office\Office12\MML2OMML.XSL",
    r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL",
    r"C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL",
)


def iter_paragraphs(document):
    """按文档顺序返回正文段落与表格单元格段落。"""
    for p in document.paragraphs:
        yield p
    for t in document.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p


def is_option_table(table) -> bool:
    """2 列且首列是 A./B./C./D. 的表格视为选项表格。"""
    if len(table.columns) != 2:
        return False
    return [r.cells[0].text.strip() for r in table.rows][:4] == ["A.", "B.", "C.", "D."]


def is_trigger(text: str, i: int) -> bool:
    """位置 i 是否可作为公式片段起点（LaTeX 命令、上标、合法下标）。"""
    ch = text[i]
    if ch == BS:
        return bool(re.match(BS + BS + r"[a-zA-Z]+", text[i:]))
    if ch == "^":
        return True
    if ch == "_":
        nxt = text[i + 1 : i + 2]
        return bool(nxt) and (nxt in "{0123456789" or (nxt.isascii() and nxt.isalpha()))
    return False


def spans_of(text: str, o_notation: bool = True):
    """切出 LaTeX 片段，返回 [(start, end, latex), ...]。

    规则：ASCII 连续段内含 LaTeX 命令 / ^ / 合法下标即视为公式；括号与环境内
    允许出现中文（\\text{中文}、\\begin{array} 等）；o_notation=True 时额外识别 O(...)。
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        if o_notation:
            m = O_PAT.match(text, i)
            if m and (i == 0 or text[i - 1] not in WORD) and (
                m.end() >= n or text[m.end()] not in WORD
            ):
                out.append((i, m.end(), text[i : m.end()]))
                i = m.end()
                continue
        if not is_trigger(text, i):
            i += 1
            continue
        s = i
        while s > 0 and text[s - 1] in ASCII_OK:
            s -= 1
        depth = env = 0
        j = s
        while j < n:
            ch = text[j]
            if ch == BS and re.match(BS + BS + r"begin\{", text[j:]):
                env += 1
            elif ch == BS and re.match(BS + BS + r"end\{", text[j:]):
                env = max(0, env - 1)
            if ch == "{":
                depth += 1
            elif ch == "}":
                if depth == 0:
                    break
                depth -= 1
            if depth > 0 or env > 0:
                j += 1
                continue
            if ch in ASCII_OK or ch in MATH_SYM:
                j += 1
                continue
            break
        e = j
        while s < e and text[s] in " \t":
            s += 1
        while e > s and text[e - 1] in " \t":
            e -= 1
        while e > s and text[e - 1] in ".,;:" and text[e - 2 : e - 1] not in ("}", ")", "]"):
            e -= 1
        run = text[s:e]
        if run:
            if CMD.search(run) or "^" in run or not CODE_LIKE.search(run):
                out.append((s, e, run))
                i = e
                continue
        i += 1
    return out


def run_has_extra(run_el) -> bool:
    """run 内除 rPr / t 之外是否还有其他元素（tab、br、drawing 等）。"""
    return any(child.tag not in (qn("w:rPr"), qn("w:t")) for child in run_el)


def make_text_run(src_run_el, text: str, paragraph):
    """复制原 run 的格式，替换为给定文本，返回新的 w:r 元素。"""
    new = copy.deepcopy(src_run_el)
    for t in new.findall(qn("w:t")):
        new.remove(t)
    Run(new, paragraph).text = text
    return new


def find_xsl(explicit: str | None = None) -> Path:
    """定位 MML2OMML.XSL，找不到时抛出带说明的异常。"""
    candidates = [Path(explicit)] if explicit else [Path(p) for p in DEFAULT_XSL_CANDIDATES]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "未找到 MML2OMML.XSL，请用 --xsl 指定路径（随 Office/WPS 安装提供）"
    )


def build_omml(tex: str, mathml: dict, xslt):
    """LaTeX -> KaTeX MathML -> OMML 元素；失败返回 None。"""
    html = mathml.get(tex)
    if not html or html.startswith("ERROR:"):
        return None
    m = re.search(r"<math.*?</math>", html, re.S)
    if not m:
        return None
    try:
        result = xslt(etree.fromstring(m.group(0).encode()))
    except Exception:  # noqa: BLE001
        return None
    root = result.getroot()
    if root is None:
        return None
    node = copy.deepcopy(root)
    etree.cleanup_namespaces(node)
    return node


def rewrite_paragraph(paragraph, spans, omml_of, text_fix=None):
    """把段落中的 LaTeX 片段替换为 OMML，返回 (插入数, 失败列表, 是否成功)。

    text_fix：可选字符串，逐字符从文字片段中删除（例如残留的 "$"）。
    omml_of：可调用对象，输入 latex 片段返回 OMML 元素或 None。
    """
    text = paragraph.text
    if not spans:
        return 0, [], True
    items = []
    pos = 0
    for s, e, tex in spans:
        if s > pos:
            items.append(("text", pos, s, None))
        items.append(("math", s, e, tex))
        pos = e
    if pos < len(text):
        items.append(("text", pos, len(text), None))

    children = list(paragraph._p)
    new_children = []
    bad_run = False
    inserted = 0
    failed = []
    item_idx = 0
    cursor = 0
    for child in children:
        if child.tag != qn("w:r"):
            new_children.append(child)
            continue
        run = Run(child, paragraph)
        rtext = run.text
        rs, re_ = cursor, cursor + len(rtext)
        cursor = re_
        while item_idx < len(items) and items[item_idx][2] <= rs:
            item_idx += 1
        plan = []
        while item_idx < len(items) and items[item_idx][1] < re_:
            kind, a, b, tex = items[item_idx]
            if kind == "text":
                lo, hi = max(a, rs), min(b, re_)
                if lo < hi:
                    piece = text[lo:hi]
                    if text_fix:
                        piece = piece.replace(text_fix, "")
                    if piece:
                        plan.append(("text", piece, None))
                if b <= re_:
                    item_idx += 1
                else:
                    break
            else:
                if a >= rs:
                    plan.append(("math", None, tex))
                item_idx += 1
        if not plan:
            if text_fix and text_fix in rtext:
                new_children.append(make_text_run(child, rtext.replace(text_fix, ""), paragraph))
            else:
                new_children.append(child)
            continue
        if any(k == "math" for k, _, _ in plan) and run_has_extra(child):
            bad_run = True
        for kind, payload, tex in plan:
            if kind == "text":
                new_children.append(make_text_run(child, payload, paragraph))
            else:
                node = omml_of(tex)
                if node is None:
                    failed.append(tex)
                    new_children.append(make_text_run(child, tex, paragraph))
                else:
                    new_children.append(node)
                    inserted += 1
    if bad_run:
        return 0, failed, False
    for child in children:
        paragraph._p.remove(child)
    for child in new_children:
        paragraph._p.append(child)
    return inserted, failed, True


def set_alignment(paragraph, value):
    """设置段落 w:jc；value 为 None 时移除该属性。"""
    pPr = paragraph._p.get_or_add_pPr()
    jc = pPr.find(qn("w:jc"))
    if value is None:
        if jc is not None:
            pPr.remove(jc)
        return
    if jc is None:
        jc = pPr.makeelement(qn("w:jc"), {})
        pPr.append(jc)
    jc.set(qn("w:val"), value)


def set_indent(paragraph, state):
    """设置段落 w:ind；state 为 None 或 (left, leftChars)。"""
    pPr = paragraph._p.get_or_add_pPr()
    ind = pPr.find(qn("w:ind"))
    if state is None:
        if ind is not None:
            pPr.remove(ind)
        return
    if ind is None:
        ind = pPr.makeelement(qn("w:ind"), {})
        pPr.append(ind)
    for attr, value in (("w:left", state[0]), ("w:leftChars", state[1])):
        key = qn(attr)
        if value is None:
            ind.attrib.pop(key, None)
        else:
            ind.set(key, value)


def rel_ids(element) -> set:
    """收集元素及其子元素引用的关系 id（图片、链接等）。"""
    ids = set()
    for el in element.iter():
        for attr in ("embed", "link", "id"):
            value = el.get(REL_NS + attr)
            if value:
                ids.add(value)
    return ids


def drop_unused_rels(document, keep_rids: set, drop_rids: set):
    """删除只被待删内容引用的关系，返回 (删除数, 释放字节数)。"""
    dropped = 0
    freed = 0
    for rid in drop_rids - keep_rids:
        rel = document.part.rels.get(rid)
        if rel is None:
            continue
        try:
            freed += len(rel.target_part.blob)
        except Exception:  # noqa: BLE001
            pass
        document.part.drop_rel(rid)
        dropped += 1
    return dropped, freed


def load_document(path):
    """打开 docx；调用方负责保存与备份。"""
    return docx.Document(str(path))


def resolve_outputs(src: Path, out: str | None, in_place: bool, tag: str):
    """解析输出与备份路径。

    默认写到 <原名>-<tag>.docx；--in-place 时先备份为 <原名>.<tag>.bak.docx。
    返回 (输出路径, 备份路径或 None)。
    """
    if in_place:
        backup = src.with_name(f"{src.stem}.{tag}.bak{src.suffix}")
        shutil.copy2(src, backup)
        return src, backup
    target = Path(out) if out else src.with_name(f"{src.stem}-{tag}{src.suffix}")
    return target, None
