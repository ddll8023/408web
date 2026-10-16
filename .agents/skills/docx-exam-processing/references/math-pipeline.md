# LaTeX → Word 原生公式（OMML）管线

## 管线与依赖

```text
段落文字里的 LaTeX 片段
  └─ KaTeX（Node，scripts/katex_batch.js，output='mathml'）→ MathML
       └─ MML2OMML.XSL（本机 Office 自带）+ lxml → OMML
            └─ 插入段落，成为 Word 原生公式 m:oMath
```

- KaTeX 位置：`katex_batch.js` 依次尝试 `--katex`、`require('katex')`、`<cwd>/node_modules/katex`、
  `<项目根>/frontend/node_modules/katex`。
- `MML2OMML.XSL` 常见路径：`C:\Program Files (x86)\Microsoft Office\Office12\MML2OMML.XSL`、
  `C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL`。脚本会自动探测，也可 `--xsl` 指定。
- 该 XSL 只做 MathML→OMML 映射，不会生成 `m:oMathPara`；出现该容器说明是编辑器（WPS）后来写入的。

## 片段切分（无定界符时的启发式）

导出文档里的公式往往**没有可靠定界符**（`$` 可能被导出过程吞掉），只能按文本形状切分：

1. 触发条件：ASCII 连续段中包含 LaTeX 命令（`\xxx`）、`^`，或合法下标 `_{...}`/`_1`/`_x`。
2. 向左扩展：吞掉相邻的 ASCII 字符（字母、数字、括号、运算符、空格）。
3. 向右扫描：跟踪 `{}` 深度与 `\begin{}`/`\end{}` 环境；**括号内或环境内允许出现中文**
   （`\text{根结点}`、`\begin{array}{c}…`）；深度为 0 时遇到中文、中文标点或非数学符号即结束。
4. 清理：去掉首尾空白与尾随的 `.`/`,`/`;`/`:`（当它们不是 `}`/`)`/`]` 之后时）。
5. 排除误判：代码常量不当作公式——形如 `LLONG_MAX`、`MAX_SIZE`、`INT_MIN`，或含 `;`、`#`、`->`
  且没有 LaTeX 命令的片段。
6. 大 O 记号：`O(n)`、`O(1)`、`O(m+n)` 这类不含 LaTeX 命令的写法默认也识别为公式
   （`--no-o-notation` 可关闭）。它们常与 `O(\log n)` 出现在同一段，不处理会明显不一致。

已知边界（需要时人工确认）：

- 形如 `x < n/2`、`AE=5`、`T(n)=2T(n/2)+n` 的纯 ASCII 表达式**不会**被切出，因为与代码行
  （`x = 2;`、`while (x < n / 2)`）无法可靠区分；这类保持原文。
- 片段若跨多个 run（例如公式里夹着加粗），对应段落会跳过替换并在报告中列出。

## 段落重写

`docx_common.rewrite_paragraph()` 按字符偏移把原 run 切成"文字 run + 公式"，文字 run 复制原
run 的 `rPr`，`m:oMath` 插在片段起始位置；段落样式、缩进、书签等非 run 元素保持原位。
`run` 内含 tab/图片等非文字元素时整段跳过，避免丢内容。

## 失败处理与计数校验

- KaTeX 解析失败或 XSLT 转换失败的片段：保留原 LaTeX 文本，逐条打印，预期 0 处。
- 处理前后用数量核对：`m:oMath` 总数应等于成功插入数；正文与表格中不应再残留 LaTeX 命令；
  段落数、表格数、图片部件数应保持不变（`verify_docx.py` 可一次检查）。
- 整段即公式的段落默认居中（`w:jc=center` + 左缩进 0）；表格单元格里的公式**不要**居中，
  否则选项会被推到行中间。
