import type { Difficulty } from '@/types'

type DifficultyStyle = 'success' | 'warning' | 'danger' | 'info'
export const DIFFICULTY_MAP: Record<Difficulty, { label: string; type: DifficultyStyle }> = {
  EASY: { label: '简单', type: 'success' },
  MEDIUM: { label: '中等', type: 'warning' },
  HARD: { label: '困难', type: 'danger' }
}

export const getDifficultyLabel = (difficulty: Difficulty | '' | null | undefined) => {
  return difficulty ? DIFFICULTY_MAP[difficulty].label : ''
}

export const getDifficultyType = (difficulty: Difficulty | '' | null | undefined): DifficultyStyle => {
  return difficulty ? DIFFICULTY_MAP[difficulty].type : 'info'
}
