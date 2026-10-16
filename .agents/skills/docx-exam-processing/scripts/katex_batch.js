// 批量把 LaTeX 片段转成 KaTeX 的 MathML 输出。
//
// 用法: node katex_batch.js <in.json> <out.json> [--katex <katex模块路径>]
//   in.json : LaTeX 片段字符串数组
//   out.json: {片段: "<span class=\"katex\">…</span>"}，解析失败写 "ERROR:<信息>"
//
// 依赖：Node 18+ 与 katex 包（默认依次尝试 require('katex')、
//       <cwd>/node_modules/katex、<项目根>/frontend/node_modules/katex）。
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const katexFlag = args.indexOf('--katex');
let katexPath = null;
if (katexFlag >= 0) {
  katexPath = args[katexFlag + 1];
  args.splice(katexFlag, 2);
}
const [inPath, outPath] = args;
if (!inPath || !outPath) {
  console.error('用法: node katex_batch.js <in.json> <out.json> [--katex <path>]');
  process.exit(2);
}

const scriptDir = __dirname;
const candidates = [
  katexPath,
  'katex',
  path.join(process.cwd(), 'node_modules', 'katex'),
  path.resolve(scriptDir, '../../../frontend/node_modules/katex'),
].filter(Boolean);

let katex = null;
const tried = [];
for (const candidate of candidates) {
  try {
    katex = require(candidate);
    break;
  } catch (e) {
    tried.push(candidate);
  }
}
if (!katex) {
  console.error('未找到 katex 模块，已尝试: ' + tried.join(', '));
  process.exit(3);
}

const spans = JSON.parse(fs.readFileSync(inPath, 'utf8'));
const out = {};
let ok = 0;
for (const tex of spans) {
  try {
    out[tex] = katex.renderToString(tex, {
      throwOnError: true,
      output: 'mathml',
      displayMode: false,
      strict: false,
    });
    ok += 1;
  } catch (e) {
    out[tex] = 'ERROR:' + String(e.message);
  }
}
fs.writeFileSync(outPath, JSON.stringify(out), 'utf8');
console.log(`katex ok: ${ok} / ${spans.length}`);
