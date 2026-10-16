---
name: docx-exam-processing
description: 处理按章节组织的试题 Word 文档（.docx）：按章节编号重排标题级别、把 LaTeX 字面量渲染成 Word 原生公式、修正表格与选项对齐及 WPS 居中问题、从带答案文档拆出纯题目文档，并做结构回读与渲染验证。当用户要求整理真题/试题 docx 的标题层级、渲染或转换文档里的公式、让选项或表格左对齐、去掉答案区另存题目文档、核对 docx 改动结果时使用。不适用于 xlsx/pptx/pdf 处理、扫描件 OCR、纯 Markdown 写作或网页前端排版。
license: 内部使用（由本仓库自行维护）
compatibility: Windows 优先；需要 python-docx 与 lxml；公式渲染需要 Node 18+ 与 katex，以及本机 Office 提供的 MML2OMML.XSL；渲染抽查需要 LibreOffice 与 pymupdf。
---

# 试题 Word 文档处理

针对"按章节编号组织的真题合集"这类 `.docx`，提供标题层级、公式渲染、排版修正、
题目/答案拆分与结果验证的可复用流程。

## 前置阅读

| 情况 | 先读 |
| --- | --- |
| 第一次处理某份文档、要确认结构与识别规则 | `references/doc-structure.md` |
| 要渲染公式、排查公式切分或转换失败 | `references/math-pipeline.md` |
| 出现"公式仍居中"、文件体积突变、要用 WPS 打开 | `references/wps-quirks.md` |

脚本位于本 skill 的 `scripts/`，用绝对或相对本目录的路径调用；脚本参数中的文件路径必须显式给出。

## 工作方式（每个任务都照此执行）

1. **只读勘察**：先跑 `scripts/inspect_docx.py "<file.docx>"`，拿到段落/表格/图片数量、标题层级
   分布、章节与题目计数、LaTeX 片段与公式统计、选项表格对齐分布，作为改动基线。
2. **提方案与执行清单**：给出改动范围、准确文件路径、操作类型与风险，等用户确认后再动手；
   未确认不改文件。
3. **最小改动**：脚本默认写到新文件（`<原名>-<用途>.docx`），只有明确 `--in-place` 才覆盖，
   覆盖前自动备份为 `<原名>.<用途>.bak.docx`。不触碰无关段落、样式表、图片与页面设置。
4. **回读与渲染验证**：`scripts/verify_docx.py` 做结构回读，`--render` 时用 LibreOffice 转 PDF
   并抽页渲染 PNG 供人工核对。
5. **报告**：结果、修改（文件与范围）、实际执行的验证、风险与未验证项。

## 任务 A：按章节编号重排标题级别

```text
python scripts/relevel_headings.py "<file.docx>" [--in-place] [--dry-run]
```

- 规则：章节编号段数决定级别（`1`→H1、`2.1`→H2、`3.1.1`→H3）；题目标题 = 所属章节 + 1；
  `题目`/`选项`/`答案` 及题内子标题整体跟随下移。
- 只用 `pStyle` 表达层级，文字、图片、表格、样式表不动。
- 若章节标题全部是 Heading 1（导出文档常见），本步骤是恢复层级的前提；先 `--dry-run`
  看目标层级分布，再实际执行。
- 样式表字号可能不是逐级递减（曾出现 H3 大于 H2、H4/H5 与 H2 同号），需要时单独调整
  `Heading 1..7` 的 `w:sz`，但要把"标题是否大于正文"按正文 run 的实际字号判断。

## 任务 B：把 LaTeX 渲染成 Word 原生公式

```text
python scripts/render_latex_math.py "<file.docx>" [--in-place] [--dry-run]
    [--no-o-notation] [--no-center-display] [--strip-dollar] [--xsl <path>] [--katex <path>]
```

- 管线与切分规则见 `references/math-pipeline.md`；渲染前先 `--dry-run` 确认涉及段落与片段数量。
- 默认把 `O(n)` 这类大 O 记号也识别为公式（`--no-o-notation` 关闭）。
- 整段只有公式的正文段落默认居中；**表格单元格里的公式不要居中**，否则选项会被推到行中间。
- 结束后核对：插入数 = `m:oMath` 增量、残留 LaTeX 段落为 0、失败清单为空（用 `verify_docx.py`）。
- 失败片段会保留原 LaTeX 文本并逐条打印，不要静默放过。

## 任务 C：修正表格/选项对齐与 WPS 居中

```text
python scripts/fix_alignment.py "<file.docx>" table-left [--baseline <改动前.docx>] [--in-place]
python scripts/fix_alignment.py "<file.docx>" unwrap-display [--in-place]
python scripts/fix_alignment.py "<file.docx>" zwsp [--in-place]
```

- 选项在导出文档里通常是 2 列 4 行表格（字母列 + 内容列），对齐要改的是**单元格段落**，不是正文。
- `table-left`：选项表格内所有单元格段落改左对齐；带 `--baseline` 时按改动前文档还原非选项
  表格中被顺手改动的对齐与缩进。
- `unwrap-display`：拆除 `m:oMathPara` 显示式容器（WPS 写入，会覆盖段落对齐并居中）。
- `zwsp`：给"整段只有公式"的表格单元格追加零宽空格，避免 WPS 再按独立公式居中。
- 现象、成因与判定方法见 `references/wps-quirks.md`。

## 任务 D：拆出纯题目文档

```text
python scripts/split_questions.py "<file.docx>" --out "<new.docx>"
```

- 默认删除每题答案区：从 `答案` 标题到下一个题目标题 / 章节标题之前的全部段落、表格与图片引用，
  并清理只被这些内容引用的图片关系（避免新文件里留孤儿图片）。
- 保留章节标题、题目标题、`题目` 区块及其配图、`选项` 区块与选项表格。
- 输出必须是新文件；脚本拒绝覆盖原文件。

## 关键约束

- 修改类脚本一律不自动执行验证、转换或构建；转 PDF、渲染页面、跑批处理都需要用户明确授权。
- 不覆盖原文件；`--in-place` 前先确认用户同意，并保留备份。
- 不改与任务无关的内容：正文文字、样式表、图片、页眉页脚、页面设置。
- 表格单元格里的公式保持左对齐，不要套用"独立公式居中"。
- 交付前提醒用户：最终查看用 Word，在 WPS 里只读打开，保存会重新引入显示式容器并放大文件。

## 失败与边界处理

| 情况 | 处理 |
| --- | --- |
| 找不到 `MML2OMML.XSL` | 报错并提示用 `--xsl` 指定（随 Office/WPS 安装） |
| KaTeX 解析失败或 XSLT 转换失败 | 保留原 LaTeX 文本、逐条列出，不静默跳过 |
| 段落 run 内含 tab/图片等元素 | 整段跳过替换并在报告中标出，避免丢内容 |
| 切分后仍残留 LaTeX | 视为切分规则不足，先调整 `spans_of` 规则或补充样例，再重跑 |
| 结构与预期不符（标题全 H1、选项不在表格里等） | 回到勘察结果，按实际结构改脚本参数，不硬套本 skill 的默认假设 |

## 资源

- `scripts/docx_common.py`：共享逻辑（段落遍历、片段切分、OMML 构建、段落重写、对齐与关系清理）。
- `scripts/inspect_docx.py`：只读勘察报告，任何任务的第一步。
- `scripts/relevel_headings.py`：任务 A。
- `scripts/render_latex_math.py` + `scripts/katex_batch.js`：任务 B。
- `scripts/fix_alignment.py`：任务 C。
- `scripts/split_questions.py`：任务 D。
- `scripts/verify_docx.py`：结构回读、基线比对与渲染抽查。
- `references/doc-structure.md`、`references/math-pipeline.md`、`references/wps-quirks.md`：按需读取。
