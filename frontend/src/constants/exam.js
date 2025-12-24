// 难度映射常量
export const DIFFICULTY_MAP = {
  'EASY': { label: '简单', type: 'success' },
  'MEDIUM': { label: '中等', type: 'warning' },
  'HARD': { label: '困难', type: 'danger' }
}

// 获取难度标签文本
export const getDifficultyLabel = (difficulty) => {
  return DIFFICULTY_MAP[difficulty]?.label || difficulty
}

// 获取难度对应的Element UI类型
export const getDifficultyType = (difficulty) => {
  return DIFFICULTY_MAP[difficulty]?.type || 'info'
}
