import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import ts from 'typescript'

// 与现有测试一致，加载实际生产工具函数，不引入 DOM 或测试框架依赖。
const source = await readFile(new URL('../src/utils/markdownMedia.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
})
const { parseMediaWidth, resolveSvgViewport, prepareMarkdownImage, prepareMarkdownMedia } =
  await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`)

class Media {
  constructor(attributes = {}) {
    this.attributes = new Map(Object.entries(attributes))
    this.properties = new Map()
    this.style = {
      width: '',
      setProperty: (key, value) => this.properties.set(key, value),
      getPropertyValue: key => this.properties.get(key) || '',
      removeProperty: key => {
        if (key === 'width') this.style.width = ''
        this.properties.delete(key)
      },
    }
    this.classes = new Set()
    this.classList = {
      add: value => this.classes.add(value),
      toggle: (value, enabled) => enabled ? this.classes.add(value) : this.classes.delete(value),
    }
    this.parentElement = { tagName: 'P', childNodes: [this], closest: () => null }
  }
  getAttribute(key) { return this.attributes.get(key) ?? null }
  setAttribute(key, value) { this.attributes.set(key, value) }
  closest() { return null }
}

class SvgMedia extends Media {}
globalThis.SVGSVGElement = SvgMedia

function root(...media) {
  return { querySelectorAll: () => media }
}

test('固定画布可补 viewBox，仅有百分比或缺失尺寸时不猜测坐标系', () => {
  assert.deepEqual(resolveSvgViewport('280', '140px', null), {
    width: 280, height: 140, viewBox: '0 0 280 140',
  })
  for (const [width, height] of [['100%', '140'], ['12em', '8em'], [null, null], ['280', null], ['0', '140']]) {
    assert.equal(resolveSvgViewport(width, height, null), null)
  }
})

test('只有 viewBox 时以坐标画布确定自然比例，不随容器主动撑满', () => {
  assert.deepEqual(resolveSvgViewport(null, null, '-10 -20 620 180'), {
    width: 620, height: 180, viewBox: '-10 -20 620 180',
  })
  assert.deepEqual(resolveSvgViewport('300', null, '0 0 600 80'), {
    width: 300, height: 40, viewBox: '0 0 600 80',
  })
  assert.deepEqual(resolveSvgViewport(null, '40', '0,0,600,80'), {
    width: 300, height: 40, viewBox: '0,0,600,80',
  })
})

test('不改写已有 viewBox 原点或宽高不同的明确视口，不修复非法 viewBox', () => {
  assert.deepEqual(resolveSvgViewport('400', '200', '-20 10 600 600'), {
    width: 400, height: 200, viewBox: '-20 10 600 600',
  })
  for (const viewBox of ['0 0 0 10', '0 0 10 -1', '0 0 NaN 10', '0 0 Infinity 10', '0 0 1e308 1e-308', '0 0 10', 'bad']) {
    assert.equal(resolveSvgViewport('400', '200', viewBox), null)
  }
})

test('单图宽度只接受明确的正数和允许单位', () => {
  for (const [input, expected] of [['240', '240px'], [' 12em ', '12em'], ['80%', '80%'], ['15.5PX', '15.5px'], ['24rem', '24rem']]) {
    assert.equal(parseMediaWidth(input), expected)
  }
  for (const value of [null, '', '-1px', '0', 'Infinity', 'calc(100% + 10px)', 'url(x)', '300vw']) {
    assert.equal(parseMediaWidth(value), null)
  }
})

test('1024 像素矩阵只记录自然尺寸，显示尺寸交给共享规则，不写死成原图大小', () => {
  const image = new Media()
  image.naturalWidth = 1024
  image.naturalHeight = 1024
  prepareMarkdownImage(image)
  assert.equal(image.properties.get('--media-intrinsic-width'), '1024px')
  assert.equal(image.properties.get('--media-ratio'), '1')
  assert.equal(image.style.width, '')
  assert.equal(image.getAttribute('width'), null)
  image.naturalWidth = 1600
  image.naturalHeight = 400
  prepareMarkdownImage(image)
  assert.equal(image.properties.get('--media-ratio'), '4')
})

test('未加载或失败图片不产生零尺寸或无效比例', () => {
  const image = new Media()
  image.naturalWidth = 0
  image.naturalHeight = 0
  prepareMarkdownImage(image)
  assert.equal(image.properties.size, 0)
})

test('规范化保留单图宽度和宽图标记，跳过公式及嵌套 SVG', () => {
  const svg = new SvgMedia({ width: '280', height: '140', preserveAspectRatio: 'xMinYMin meet' })
  svg.style.width = '12em'
  svg.style.setProperty('max-height', 'none')
  svg.classes.add('media-wide')
  const formula = new SvgMedia({ width: '400', height: '100' })
  formula.closest = () => ({})
  const nested = new SvgMedia({ width: '100', height: '50' })
  nested.parentElement.closest = () => ({})
  const incomplete = new SvgMedia()

  assert.deepEqual(prepareMarkdownMedia(root(svg, formula, nested, incomplete)), [svg])
  assert.equal(svg.getAttribute('viewBox'), '0 0 280 140')
  assert.equal(svg.getAttribute('preserveAspectRatio'), 'xMinYMin meet')
  assert.equal(svg.properties.get('--media-preferred-width'), '12em')
  assert.ok(svg.classes.has('media-wide'))
  assert.ok(svg.classes.has('markdown-media-block'))
  assert.equal(svg.style.width, '')
  assert.equal(svg.properties.has('max-height'), false)
  prepareMarkdownMedia(root(svg))
  assert.equal(svg.properties.get('--media-preferred-width'), '12em')
  for (const untouched of [formula, nested, incomplete]) {
    assert.equal(untouched.getAttribute('viewBox'), null)
    assert.ok(!untouched.classes.has('markdown-media'))
  }
})

test('独立插图与文本混排区别处理，不强制拆开并排图片', () => {
  const image = new Media({ width: '240' })
  image.naturalWidth = 1024
  image.naturalHeight = 512
  prepareMarkdownMedia(root(image))
  assert.ok(image.classes.has('markdown-media-block'))
  assert.equal(image.properties.get('--media-preferred-width'), '240px')

  image.parentElement.childNodes.push({ nodeType: 3, textContent: '后面的正文' })
  prepareMarkdownMedia(root(image))
  assert.ok(!image.classes.has('markdown-media-block'))

  image.parentElement.childNodes = [image, new Media()]
  prepareMarkdownMedia(root(image))
  assert.ok(!image.classes.has('markdown-media-block'))
})
