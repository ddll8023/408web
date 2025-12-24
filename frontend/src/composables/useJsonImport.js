/**
 * JSON导入功能 composable
 * 支持AI输出的宽松JSON格式解析
 */
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * 创建JSON导入功能
 * @returns {Object} JSON导入相关状态和方法
 */
export function useJsonImport() {
  // 状态
  // 默认展开JSON导入面板
  const jsonImportVisible = ref(['jsonImport'])
  const jsonInput = ref('')

  /**
   * 转义字段值内部的双引号和反斜杠
   * 专门处理 AI 生成的宽松 JSON（如 SVG 内嵌双引号、LaTeX 反斜杠等）
   */
  const escapeJsonFieldValue = (value) => {
    if (!value) return value

    let result = ''
    let i = 0

    while (i < value.length) {
      const char = value[i]
      const next = value[i + 1]

      if (char === '\\') {
        if (next === '\\') {
          result += '\\\\'
          i += 2
        } else if (next === '"') {
          result += '\\"'
          i += 2
        } else if (next === 'n' || next === 't' || next === 'r' || next === '/' || next === 'b' || next === 'f') {
          result += '\\' + next
          i += 2
        } else if (next === 'u' && /^[0-9a-fA-F]{4}$/.test(value.slice(i + 2, i + 6))) {
          result += value.slice(i, i + 6)
          i += 6
        } else if (next === '<' || next === '>' || next === '*') {
          // \< \> \* 等无效JSON转义，去掉反斜杠
          result += next
          i += 2
        } else if (next != null) {
          result += '\\\\' + next
          i += 2
        } else {
          result += '\\\\'
          i++
        }
      } else if (char === '"') {
        result += '\\"'
        i++
      } else {
        result += char
        i++
      }
    }

    return result
  }

  /**
   * 宽松 JSON 预处理：整体解析策略
   */
  const normalizeRelaxedJsonText = (rawText) => {
    if (!rawText) return rawText

    console.log('[JSON预处理] 开始处理，原始长度:', rawText.length)

    const targetFields = ['content', 'answer', 'options']
    const fieldsToProcess = []

    for (const fieldName of targetFields) {
      const fieldPattern = new RegExp(`"${fieldName}"\\s*:\\s*"`, 'g')
      let match

      while ((match = fieldPattern.exec(rawText)) !== null) {
        const fieldStart = match.index
        const valueStart = fieldStart + match[0].length
        let valueEnd = -1

        for (let i = valueStart; i < rawText.length; i++) {
          if (rawText[i] === '"') {
            let backslashCount = 0
            let j = i - 1
            while (j >= valueStart && rawText[j] === '\\') {
              backslashCount++
              j--
            }

            if (backslashCount % 2 === 0) {
              const afterQuote = rawText.slice(i + 1, i + 30)

              if (/^,\s*\n\s*"/.test(afterQuote) ||
                /^\s*\n\s*\}/.test(afterQuote) ||
                /^\s*\}\s*$/.test(afterQuote) ||
                /^,\s*\n\s*\}/.test(afterQuote)) {
                valueEnd = i
                break
              }
            }
          }
        }

        if (valueEnd !== -1) {
          fieldsToProcess.push({ fieldName, valueStart, valueEnd })
        }
      }
    }

    fieldsToProcess.sort((a, b) => b.valueStart - a.valueStart)

    let result = rawText
    for (const field of fieldsToProcess) {
      const rawValue = result.slice(field.valueStart, field.valueEnd)
      const escapedValue = escapeJsonFieldValue(rawValue)
      result = result.slice(0, field.valueStart) + escapedValue + result.slice(field.valueEnd)
    }

    return result
  }

  /**
   * 解析JSON（支持宽松格式）
   */
  const parseJsonWithRelaxedSupport = (rawText) => {
    if (!rawText) {
      throw new Error('JSON内容为空')
    }

    try {
      return JSON.parse(rawText)
    } catch (strictError) {
      try {
        const fixedText = normalizeRelaxedJsonText(rawText)
        return JSON.parse(fixedText)
      } catch (relaxedError) {
        throw new Error(`${strictError.message}\n\n提示：请检查content/options/answer字段中是否有未转义的双引号或反斜杠`)
      }
    }
  }

  /**
   * 从剪贴板粘贴
   */
  const handlePasteJson = async () => {
    try {
      if (!(navigator && navigator.clipboard && window.isSecureContext)) {
        ElMessage.warning('当前环境不支持从剪贴板读取，请手动粘贴')
        return
      }

      const text = await navigator.clipboard.readText()
      if (!text) {
        ElMessage.warning('剪贴板中没有文本内容')
        return
      }

      jsonInput.value = text
      ElMessage.success('已从剪贴板粘贴到JSON输入框')
    } catch (error) {
      console.error('粘贴失败:', error)
      ElMessage.error('粘贴失败，请手动粘贴')
    }
  }

  /**
   * 清空JSON输入
   */
  const handleClearJson = () => {
    jsonInput.value = ''
  }

  /**
   * 显示JSON格式示例
   */
  const showJsonExample = (type = 'exam') => {
    const examples = {
      exam: {
        choice: `{
  "year": 2023,
  "questionNumber": 1,
  "questionType": "CHOICE",
  "subjectId": 1,
  "title": "栈的基本概念",
  "content": "下列关于栈的说法中，**错误**的是：",
  "options": {"A":"栈是后进先出","B":"可用数组实现","C":"不支持随机访问","D":"操作在栈顶进行"},
  "answer": "**正确答案：C**",
  "category": ["数据结构"],
  "difficulty": "MEDIUM"
}`,
        essay: `{
  "year": 2023,
  "questionNumber": 42,
  "questionType": "ESSAY",
  "subjectId": 1,
  "content": "设计一个算法...",
  "answer": "**解答：**\\n1. 首先...",
  "category": ["算法设计"],
  "difficulty": "HARD"
}`
      },
      mock: {
        choice: `{
  "source": "王道模拟",
  "questionNumber": 1,
  "questionType": "CHOICE",
  "subjectId": 1,
  "content": "题目内容...",
  "options": {"A":"选项A","B":"选项B","C":"选项C","D":"选项D"},
  "answer": "答案解析...",
  "category": ["分类"],
  "difficulty": "MEDIUM"
}`
      },
      exercise: {
        choice: `{
  "questionNumber": 1,
  "questionType": "CHOICE",
  "subjectId": 1,
  "difficulty": "MEDIUM",
  "content": "下列关于栈的说法中，**错误**的是：",
  "options": {"A":"栈是一种后进先出的数据结构","B":"栈可以用数组或链表实现","C":"栈不支持随机访问","D":"栈的插入和删除都在栈顶进行"},
  "answer": "**正确答案：C**\\n\\n解析：栈作为一种线性结构，如果用数组实现是可以随机访问的。"
}`,
        essay: `{
  "questionNumber": 41,
  "questionType": "ESSAY",
  "subjectId": 1,
  "difficulty": "HARD",
  "content": "设计一个算法，判断给定的二叉树是否为完全二叉树。\\n\\n**要求**：\\n1. 给出算法思路\\n2. 写出算法代码\\n3. 分析时间复杂度",
  "answer": "## 算法思路\\n\\n使用层序遍历（BFS）的方法。"
}`
      }
    }

    const example = examples[type] || examples.exam
    const content = example.choice + (example.essay ? `\n\n<strong>主观题示例：</strong>\n${example.essay}` : '')

    ElMessageBox.alert(
      `<div style="font-family: monospace; white-space: pre-wrap; font-size: 12px; max-height: 400px; overflow: auto;"><strong>选择题示例：</strong>\n${content}</div>`,
      'JSON格式示例',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '知道了',
        customClass: 'json-example-dialog'
      }
    )
  }

  return {
    // 状态
    jsonImportVisible,
    jsonInput,

    // 方法
    parseJsonWithRelaxedSupport,
    handlePasteJson,
    handleClearJson,
    showJsonExample
  }
}
