# WPS 对含公式 docx 的处理与对策

在 WPS 中打开并**保存**含 Word 原生公式的文档会改变文件，实测现象：

1. **公式被包进显示式容器**：独占一段的公式会被写成 `<m:oMathPara><m:oMath>…</m:oMath></m:oMathPara>`
   （无 `m:oMathParaPr`，即默认居中）。该容器**自带居中并覆盖段落 `w:jc`**，所以段落明明设成
   左对齐，选项里的公式仍显示在中间。
2. **文件体积膨胀**：重新压缩后体积可上涨约 10%（例如 29.2MB → 32.0MB），即使内容没变。
3. **可能的公式合并**：相邻公式偶尔被合并，`m:oMath` 计数会比插入时少 1 个左右。

判定方法：`verify_docx.py` 报出 `m:oMathPara > 0`，或文件体积明显变大、修改时间不是自己写入的时间。

## 对策

- **拆除容器**：`fix_alignment.py <docx> unwrap-display`，把 `m:oMathPara` 拆回行内 `m:oMath`，
  让段落对齐重新生效；正文里的独立公式段仍由 `w:jc=center` 保持居中。
- **避免"公式独占一段"**：`fix_alignment.py <docx> zwsp` 给这类表格单元格追加零宽空格
  （U+200B），使段落不再只有公式，WPS 会按行内公式处理。若仍居中，可把占位符移到公式之前
  或前后各放一个。
- **对齐基线**：`fix_alignment.py <docx> table-left --baseline <改动前.docx>` 可把被公式渲染
  顺手改动的单元格对齐与缩进还原为改动前状态。

## 交付建议

- 最终查看/交付优先用 Word；在 WPS 里**只读打开**，不要保存，否则上述问题会再次出现。
- 交付前用 `verify_docx.py --render` 抽查渲染结果，并确认 `m:oMathPara` 为 0。
- 每次修改前保留备份（脚本默认写新文件，`--in-place` 时自动生成 `*.bak.docx`）。
