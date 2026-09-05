export type OptionValue = string | number | boolean
export interface SelectOption<V = OptionValue> { label: string; value: V }
export type SelectInput<V = OptionValue> = V | { label?: string; name?: string; value: V; id?: V } | { label?: string; name?: string; value?: V; id: V }
export interface CascaderOption { value?: string; name?: string; label?: string; children?: CascaderOption[] }
export interface NormalizedCascaderOption { value: string; label: string; children: NormalizedCascaderOption[] }
export interface TableColumn { prop: string; label: string; width?: string; align?: string; sortable?: boolean }
export interface TableSort { prop: string | null; order: 'ascending' | 'descending' | null }

export type TreeDropType = 'before' | 'inner' | 'after'
export interface TreeShape<T> { id: number; name: string; children: T[]; enabled?: boolean }
export interface TreeDrop<T> { draggingNode: T; targetNode: T; dropType: TreeDropType }
export type AllowDrop<T> = (dragging: { data: T }, target: { data: T }, type: TreeDropType) => boolean
