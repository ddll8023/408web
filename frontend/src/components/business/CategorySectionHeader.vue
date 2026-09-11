<template>
  <header
    class="relative min-h-[74px] overflow-hidden rounded-xl border px-4 py-3 shadow-sm transition-colors duration-200"
    :class="[theme.surface, theme.border]"
    :aria-label="`${theme.label}分类：${category}`"
  >
    <span
      class="absolute inset-y-0 left-0 w-1.5"
      :class="theme.accent"
      aria-hidden="true"
    />

    <div class="flex items-center justify-between gap-3 pl-2">
      <div class="flex min-w-0 items-center gap-3">
        <span
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
          :class="theme.iconSurface"
          aria-hidden="true"
        >
          <font-awesome-icon
            v-if="kind === 'exam'"
            :icon="['fas', 'book']"
            class="text-sm"
          />
          <font-awesome-icon
            v-else
            :icon="['fas', 'pencil']"
            class="text-sm"
          />
        </span>

        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <span
              class="text-[11px] font-bold uppercase tracking-[0.16em]"
              :class="theme.eyebrow"
            >
              {{ theme.label }}
            </span>
            <span
              v-if="depth > 0"
              class="rounded-full px-2 py-0.5 text-[10px] font-medium"
              :class="theme.childLabel"
            >
              子分类
            </span>
          </div>
          <h3
            class="mt-0.5 truncate font-semibold leading-tight"
            :class="depth === 0 ? 'text-lg text-[#27333d]' : 'text-base text-[#3f4b54]'"
          >
            {{ category }}
          </h3>
          <p class="mt-1 text-xs" :class="theme.subtitle">
            {{ depth === 0 ? '本分类题目' : '子分类题目' }}
          </p>
        </div>
      </div>

      <span
        class="inline-flex shrink-0 items-baseline gap-1 rounded-full px-3 py-1.5"
        :class="theme.badge"
      >
        <strong class="text-base leading-none">{{ count }}</strong>
        <span class="text-xs font-medium">题</span>
      </span>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type CategorySectionKind = 'exam' | 'mock'

interface Props {
  category: string
  count: number
  kind: CategorySectionKind
  depth?: number
}

const props = withDefaults(defineProps<Props>(), {
  depth: 0,
})

const theme = computed(() => {
  if (props.kind === 'exam') {
    return {
      label: '真题',
      surface: props.depth === 0 ? 'bg-[#EEF4F8]' : 'bg-white/90',
      border: 'border-[#C9D8E2]',
      accent: 'bg-[#56738A]',
      iconSurface: 'bg-[#DCE8F0] text-[#49677F]',
      eyebrow: 'text-[#56738A]',
      childLabel: 'bg-[#E7EFF4] text-[#607888]',
      subtitle: 'text-[#6B7E8D]',
      badge: 'bg-[#DFECF3] text-[#486B84]',
    }
  }

  return {
    label: '模拟题',
    surface: props.depth === 0 ? 'bg-[#EFF7F4]' : 'bg-white/90',
    border: 'border-[#CBE1D9]',
    accent: 'bg-[#3F8576]',
    iconSurface: 'bg-[#DCEEE8] text-[#347465]',
    eyebrow: 'text-[#3F8576]',
    childLabel: 'bg-[#E4F1EC] text-[#4B8276]',
    subtitle: 'text-[#668A80]',
    badge: 'bg-[#DDEFE9] text-[#347465]',
  }
})
</script>
