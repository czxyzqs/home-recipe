<template>
  <div class="page">
    <div class="nav-row">
      <div class="nav-title">周计划</div>
      <button class="nav-action" :disabled="generating" @click="generate">✨ 生成</button>
    </div>
    <div class="nav-hint">AI 根据历史用餐记录生成一周食谱</div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="message" class="ok-banner">{{ message }}</div>

    <div v-if="generating" class="group center" style="padding: 34px 16px;">
      <span class="spinner"></span>
      <div class="small text-2 mt-16">大模型正在规划一周菜单，约需 20-60 秒…</div>
    </div>

    <template v-if="plan && !generating">
      <div class="group-header">{{ plan.start_date }} ~ {{ plan.end_date }}</div>
      <div class="group" style="padding: 12px 16px;">
        <div class="small text-2" style="line-height: 1.6;">{{ plan.note }}</div>
        <button class="btn btn-sm mt-16" style="width: 100%;" @click="removePlan">删除此计划</button>
      </div>

      <template v-for="day in days" :key="day.date">
        <div class="group-header">{{ day.label }}</div>
        <div class="group">
          <div v-if="!day.items.length" class="grow-row" style="color: var(--label2); font-size: 14px;">—</div>
          <div v-for="item in day.items" :key="item.id" class="grow-row tappable" @click="item.recipe && $router.push(`/recipes/${item.recipe.id}`)">
            <span class="meal-badge" :class="item.meal_type">{{ mealZh(item.meal_type) }}</span>
            <span class="grow" style="font-weight: 500; font-size: 15px;">{{ item.recipe ? item.recipe.name : '未知' }}</span>
            <span class="text-2 kcal" v-if="item.recipe">{{ Math.round(item.recipe.calories) }} 千卡</span>
            <span class="chevron">›</span>
          </div>
          <div v-if="day.items.length" class="apply-row">
            <button class="text-action" @click="applyDay(day)">将这一天记入用餐记录</button>
          </div>
        </div>
      </template>
    </template>

    <div v-if="!plan && !generating" class="empty">
      <div class="empty-icon">🗓️</div>
      还没有周计划<br />
      <span class="small text-2">点击右上角「生成」，AI 会参考你最近的饮食记录安排一周三餐<br />（需先在「设置」中配置大模型）</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { api } from '../api'
import { fmtDate, parseDate, weekdayZh, MEAL_TYPES } from '../utils'

const plan = ref(null)
const generating = ref(false)
const error = ref('')
const message = ref('')

const MEAL_ZH = Object.fromEntries(MEAL_TYPES.map(m => [m.key, m.zh]))

function mealZh(key) {
  return MEAL_ZH[key] || key
}

const days = computed(() => {
  if (!plan.value) return []
  const today = fmtDate(new Date())
  const byDate = {}
  for (const item of plan.value.items) {
    ;(byDate[item.date] = byDate[item.date] || []).push(item)
  }
  return Object.keys(byDate).sort().map(date => {
    const d = parseDate(date)
    return {
      date,
      label: `${d.getMonth() + 1}/${d.getDate()} ${weekdayZh(d)}`,
      isToday: date === today,
      items: byDate[date],
    }
  })
})

onMounted(load)

async function load() {
  error.value = ''
  try {
    plan.value = await api.currentPlan()
  } catch (e) {
    error.value = e.message
  }
}

async function generate() {
  generating.value = true
  error.value = ''
  message.value = ''
  try {
    plan.value = await api.generatePlan()
    message.value = '已生成新的一周计划'
  } catch (e) {
    error.value = e.message
  } finally {
    generating.value = false
  }
}

async function applyDay(day) {
  if (!confirm(`把 ${day.label} 的 ${day.items.length} 道菜记入当天用餐记录？`)) return
  try {
    const res = await api.applyPlanDay(plan.value.id, day.date)
    message.value = `已记录：${res.added.join('、')}`
  } catch (e) {
    error.value = e.message
  }
}

async function removePlan() {
  if (!confirm('删除当前周计划？')) return
  try {
    await api.deletePlan(plan.value.id)
    plan.value = null
  } catch (e) {
    error.value = e.message
  }
}
</script>

<style scoped>
.nav-hint { font-size: 14px; color: var(--label2); padding: 0 20px 14px; }

.meal-badge {
  flex-shrink: 0; font-size: 12px; font-weight: 600;
  padding: 3px 9px; border-radius: 6px;
  background: var(--fill2); color: var(--label2);
  min-width: 44px; text-align: center;
}
.meal-badge.breakfast { background: rgba(255, 149, 0, 0.13); color: var(--orange); }
.meal-badge.lunch { background: rgba(0, 122, 255, 0.1); color: var(--blue); }
.meal-badge.dinner { background: rgba(175, 82, 222, 0.11); color: var(--purple); }
.meal-badge.snack { background: rgba(52, 199, 89, 0.13); color: var(--green); }

.kcal { font-size: 13px; font-variant-numeric: tabular-nums; }
.apply-row { padding: 9px 16px; display: flex; justify-content: center; border-top: 0.5px solid var(--sep-soft); }
.text-action {
  background: none; border: none; color: var(--blue);
  font-size: 14.5px; font-weight: 600; font-family: inherit; cursor: pointer;
}
.text-action:active { opacity: 0.4; }
</style>
