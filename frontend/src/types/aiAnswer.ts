/** AI 答案生成类型：题面草稿、对比基线和仅供编辑框采用的候选答案。 */
import type { AiQuestionKind } from '@/api/aiSession'
import type { QuestionOptions, QuestionType } from '@/types'

export interface AiAnswerDraft {
  questionType: QuestionType
  subjectId: number | null
  content: string
  options: QuestionOptions | null
}

export interface AiAnswerSource extends AiAnswerDraft {
  answer: string | null
}

export interface AiAnswerCandidate {
  questionKind: AiQuestionKind
  questionId: number
  source: AiAnswerSource
  answer: string
}
