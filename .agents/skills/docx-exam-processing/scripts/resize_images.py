"""按统一高度等比缩放 docx 中全部内嵌图片的显示尺寸。

用法：
    python resize_images.py "<file.docx>" [--from-height-cm 2.99] [--height-cm 4]
        [--max-width-cm 18.461] [--in-place] [--dry-run]

规则：
- 只处理 `<w:drawing>` 块内的内嵌图片，按块改写 `<wp:extent>` 与 `<a:ext>` 的 cx/cy，
  图片文件、样式表、页面设置、正文文字与其他 XML 部件一律不动；
- 仅当图片当前高度等于 `--from-height-cm`（容忍 0.01 cm 取整误差）且等比放大后宽度不超过
  `--max-width-cm` 时才改，其余图片原样保留并逐条打印原因；
- 输出仍是原格式 docx；默认写 `<原名>-图片<高度>cm.docx`，
  `--in-place` 时先复制 `<原名>.bak.docx` 再覆盖，且发现 Word/WPS 锁文件时拒绝执行。
"""

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

EMU_PER_CM = 360000
# Word 显示的高度按两位小数取整，比较时允许 0.01 cm 偏差
TOLERANCE_EMU = int(0.01 * EMU_PER_CM)

DRAWING_BLOCK = re.compile(r"<w:drawing>.*?</w:drawing>", re.DOTALL)
EXTENT = re.compile(r'<wp:extent cx="(\d+)" cy="(\d+)"')
A_EXTENT = re.compile(r'<a:ext cx="(\d+)" cy="(\d+)"')
PART = "word/document.xml"


def lock_paths(docx: Path):
    """返回该文档可能的 Word/WPS 锁文件路径（原名与去掉前两字符两种命名）。"""
    return [docx.with_name("~$" + docx.name), docx.with_name("~$" + docx.name[2:])]


def scale_block(block: str, from_emu: int, to_emu: int, max_width_emu: int):
    """处理单个 w:drawing 块。

    返回 (新块文本, 状态, 原尺寸 cm, 新尺寸 cm)；状态为 changed/skip:<原因>/fail:<原因>。
    """
    m = EXTENT.search(block)
    if m is None:
        return block, "fail:块内无 wp:extent", None, None
    cx, cy = int(m.group(1)), int(m.group(2))
    src = (cx / EMU_PER_CM, cy / EMU_PER_CM)
    if abs(cy - from_emu) > TOLERANCE_EMU:
        return block, "skip:当前高度非目标值 %.3f cm" % (cy / EMU_PER_CM), src, None
    new_cx = round(cx * to_emu / cy)
    if new_cx > max_width_emu:
        return block, "skip:放大后宽度 %.2f cm 超上限" % (new_cx / EMU_PER_CM), src, None
    new_block, n_wp = EXTENT.subn('<wp:extent cx="%d" cy="%d"' % (new_cx, to_emu), block, count=1)
    new_block, n_a = A_EXTENT.subn('<a:ext cx="%d" cy="%d"' % (new_cx, to_emu), new_block)
    if n_wp != 1 or n_a != 1:
        return block, "fail:wp:extent/a:ext 数量异常 (%d/%d)" % (n_wp, n_a), src, None
    return new_block, "changed", src, (new_cx / EMU_PER_CM, to_emu / EMU_PER_CM)


def process(data: bytes, from_emu: int, to_emu: int, max_width_emu: int):
    """改写 document.xml 文本，返回 (新文本, 明细列表)。"""
    xml = data.decode("utf-8")
    details = []

    def repl(match):
        new_block, status, src, dst = scale_block(match.group(0), from_emu, to_emu, max_width_emu)
        details.append((status, src, dst))
        return new_block

    new_xml = DRAWING_BLOCK.sub(repl, xml)
    total_extent = len(EXTENT.findall(xml))
    if total_extent != len(details):
        raise SystemExit(
            "取消：文档内 wp:extent 共 %d 处，但只匹配到 %d 个 w:drawing 块，结构不符预期"
            % (total_extent, len(details))
        )
    return new_xml.encode("utf-8"), details


def rewrite_zip(src: Path, dst: Path, new_part: bytes):
    """复制 docx 全部条目，仅替换 document.xml，保持条目顺序与压缩方式。"""
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for item in zin.infolist():
            data = new_part if item.filename == PART else zin.read(item.filename)
            zout.writestr(item, data)


def main() -> int:
    ap = argparse.ArgumentParser(description="按统一高度等比缩放 docx 全部内嵌图片")
    ap.add_argument("docx", help="待处理的 .docx 路径")
    ap.add_argument("--from-height-cm", type=float, default=2.99, help="仅处理该高度的图片")
    ap.add_argument("--height-cm", type=float, default=4.0, help="目标高度（cm）")
    ap.add_argument(
        "--max-width-cm",
        type=float,
        default=18.461,
        help="放大后宽度上限（cm），超过则保持原样",
    )
    ap.add_argument("--in-place", action="store_true", help="原地覆盖，先备份为 <原名>.bak.docx")
    ap.add_argument("--dry-run", action="store_true", help="只打印统计，不写文件")
    args = ap.parse_args()

    src = Path(args.docx)
    if not src.is_file():
        raise SystemExit("找不到文件：%s" % src)
    if src.suffix.lower() != ".docx":
        raise SystemExit("只支持 .docx：%s" % src)

    from_emu = round(args.from_height_cm * EMU_PER_CM)
    to_emu = round(args.height_cm * EMU_PER_CM)
    max_width_emu = int(args.max_width_cm * EMU_PER_CM)

    if args.in_place and not args.dry_run:
        locks = [p for p in lock_paths(src) if p.exists()]
        if locks:
            raise SystemExit(
                "取消：%s 仍被 Word/WPS 打开（锁文件 %s），请关闭文档后重试"
                % (src.name, ", ".join(p.name for p in locks))
            )

    with zipfile.ZipFile(src) as z:
        if PART not in z.namelist():
            raise SystemExit("不是有效的 Word 文档：缺少 %s" % PART)
        new_xml, details = process(z.read(PART), from_emu, to_emu, max_width_emu)

    changed = [d for d in details if d[0] == "changed"]
    skipped = [d for d in details if d[0].startswith("skip")]
    failed = [d for d in details if d[0].startswith("fail")]
    print("%s：图片块 %d 个 → 改写 %d，保持原样 %d，失败 %d" % (src.name, len(details), len(changed), len(skipped), len(failed)))
    for status, s, d in details:
        if status == "changed":
            print("  改：%.2f x %.3f cm → %.2f x %.2f cm" % (s[0], s[1], d[0], d[1]))
        else:
            print("  %s：当前 %.2f x %.3f cm" % (status, s[0], s[1]))
    if failed:
        raise SystemExit("存在未能处理的图片块，已放弃写入")

    if args.dry_run:
        print("dry-run：未写入任何文件")
        return 0

    if args.in_place:
        bak = src.with_name(src.stem + ".bak.docx")
        shutil.copy2(src, bak)
        print("已备份：%s" % bak)
        # 先写临时文件再替换，避免同一路径同时读写
        tmp = src.with_name(src.stem + ".resize.tmp.docx")
        try:
            rewrite_zip(src, tmp, new_xml)
            tmp.replace(src)
        finally:
            if tmp.exists():
                tmp.unlink()
        print("已写入：%s" % src)
        return 0

    out = src.with_name("%s-图片%gcm.docx" % (src.stem, args.height_cm))
    rewrite_zip(src, out, new_xml)
    print("已写入：%s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
