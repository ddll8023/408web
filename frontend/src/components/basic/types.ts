/**
 * 基础组件共享类型。
 * 集中定义选择器选项、级联节点、表格列与排序等跨组件契约。
 */
export type OptionValue = string | number | boolean
export interface SelectOption<V = OptionValue> { label: string; value: V }
export type SelectInput<V = OptionValue> = V | { label?: string; name?: string; value: V; id?: V } | { label?: string; name?: string; value?: V; id: V }
export interface CascaderOption {
  value?: string
  name?: string
  label?: string
  children?: CascaderOption[]
  selectable?: boolean
}
export interface NormalizedCascaderOption {
  value: string
  label: string
  children: NormalizedCascaderOption[]
  selectable: boolean
}
export type TableRowKey = string | number
export interface TableColumn { prop: string; label: string; width?: string; minWidth?: string; align?: string; sortable?: boolean; fixed?: string; slot?: boolean }
export interface TableSort { prop: string | null; order: 'ascending' | 'descending' | null }
