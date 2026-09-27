<template>
  <div class="page">
    <div class="nav-large">
      <div class="nav-title">营养</div>
      <div class="nav-sub">看看这一周吃得怎么样</div>
    </div>

    <!-- 周切换 -->
    <div class="week-nav">
      <button class="nav-circle" @click="shiftWeek(-1)">‹</button>
      <div class="grow center">
        <div style="font-weight: 700; font-size: 15.5px;">{{ weekLabel }}</div>
        <div class="small text-2">{{ weekOffset === 0 ? '本周' : (weekOffset > 0 ? '下周' : -weekOffset + ' 周前') }}</div>
      </div>
      <button class="nav-circle" @click="shiftWeek(1)" :disabled="weekOffset >= 1">›</button>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <!-- 均值 -->
    <div class="group" v-if="loaded" style="padding: 18px 16px 14px;">
      <div class="avg-grid">
        <div class="avg">
          <div class="avg-val">{{ Math.round(avg.calories) }}</div>
          <div class="avg-name">千卡/天</div>
        </div>
        <div class="avg">
          <div class="avg-val">{{ Math.round(avg.protein) }}g</div>
          <div class="avg-name">蛋白质</div>
        </div>
        <div class="avg">
          <div class="avg-val">{{ Math.round(avg.fat) }}g</div>
          <div class="avg-name">脂肪</div>
        </div>
        <div class="avg">
          <div class="avg-val">{{ Math.round(avg.carbs) }}g</div>
          <div class="avg-name">碳水</div>
        </div>
      </div>
      <div class="small text-2 mt-16 center" style="line-height: 1.5;">参考：成人每日约 1800-2400 千卡、蛋白质 55-65g</div>
    </div>

    <!-- 每日热量图 -->
    <div class="group-header">每日热量 · 千卡</div>
    <div class="group" v-if="loaded" style="padding: 16px 12px 12px;">
      <div class="chart" v-if="maxCal > 0">
        <div v-for="d in daily" :key="d.date" class="bar-col">
          <div class="bar-num">{{ d.calories ? Math.round(d.calories) : '' }}</div>
          <div class="bar-track">
            <div class="bar-fill" :class="{ low: d.calories < 1200 && d.meals > 0 }" :style="{ height: barHeight(d.calories) }"></div>
          </div>
          <div class="bar-label">{{ shortDay(d.date) }}</div>
          <div class="bar-dot" :class="{ has: d.meals > 0 }"></div>
        </div>
      </div>
      <div v-else class="empty small"><div class="empty-icon">🍽️</div>这一周还没有用餐记录</div>
    </div>

    <!-- AI 分析 -->
    <div class="group-header">AI 膳食建议</div>
    <div class="group" v-if="loaded" style="padding: 14px 16px;">
      <div class="small text-2" style="margin-bottom: 14px; line-height: 1.5;">让大模型结合一周数据分析营养均衡情况并给出改进建议</div>
      <button class="btn btn-primary btn-block" :disabled="ai.loading" @click="runAI">
        <span v-if="ai.loading" class="spinner" style="border-color: rgba(255,255,255,.35); border-top-color: #fff;"></span>
        {{ ai.loading ? '分析中，约需 10-30 秒…' : '开始分析' }}
      </button>
      <div v-if="ai.error" class="error-banner mt-16" style="margin: 16px 0 0;">{{ ai.error }}</div>
      <div v-if="ai.result" class="ai-result mt-16">{{ ai.result }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted, watch } from 'vue'
import { api } from '../api'
import { addDays, fmtDate, mondayOf } from '../utils'

const weekOffset = ref(0)
const daily = ref([])
const loaded = ref(false)
const error = ref('')
const ai = reactive({ loading: false, error: '', result: '' })

const weekStart = computed(() => addDays(mondayOf(new Date()), weekOffset.value * 7))
const weekEnd = computed(() => addDays(weekStart.value, 6))
const weekLabel = computed(() => `${fmtDate(weekStart.value).slice(5)} ~ ${fmtDate(weekEnd.value).slice(5)}`)

const avg = computed(() => {
  const n = 7
  const sum = daily.value.reduce((acc, d) => ({
    calories: acc.calories + d.calories,
    protein: acc.protein + d.protein,
    fat: acc.fat + d.fat,
    carbs: acc.carbs + d.carbs,
  }), { calories: 0, protein: 0, fat: 0, carbs: 0 })
  return { calories: sum.calories / n, protein: sum.protein / n, fat: sum.fat / n, carbs: sum.carbs / n }
})

const maxCal = computed(() => Math.max(100, ...daily.value.map(d => d.calories)))

function barHeight(cal) {
  return Math.max(2, Math.round((cal / maxCal.value) * 100)) + '%'
}

function shortDay(iso) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function shiftWeek(n) {
  weekOffset.value = Math.min(1, weekOffset.value + n)
}

async function load() {
  error.value = ''
  ai.result = ''
  try {
    daily.value = await api.rangeNutrition(fmtDate(weekStart.value), fmtDate(weekEnd.value))
    loaded.value = true
  } catch (e) {
    error.value = e.message
  }
}

watch(weekOffset, load)
onMounted(load)

async function runAI() {
  ai.loading = true
  ai.error = ''
  ai.result = ''
  try {
    const res = await api.aiAnalyze(fmtDate(weekStart.value), 7)
    ai.result = res.analysis
  } catch (e) {
    ai.error = e.message
  } finally {
    ai.loading = false
  }
}
</script>

<style scoped>
.week-nav {
  display: flex; align-items: center; gap: 10px;
  padding: 2px 20px 16px;
}
.avg-grid { display: flex; text-align: center; }
.avg { flex: 1; }
.avg-val { font-size: 21px; font-weight: 700; color: var(--blue); font-variant-numeric: tabular-nums; }
.avg-name { font-size: 12px; color: var(--label2); margin-top: 2px; }

.chart { display: flex; align-items: flex-end; gap: 6px; height: 176px; padding-top: 18px; }
.bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; }
.bar-num { font-size: 10.5px; color: var(--label2); height: 15px; font-variant-numeric: tabular-nums; }
.bar-track { flex: 1; width: 100%; max-width: 34px; background: var(--fill); border-radius: 7px; display: flex; align-items: flex-end; overflow: hidden; }
.bar-fill {
  width: 100%; background: linear-gradient(180deg, #409CFF, var(--blue));
  border-radius: 7px 7px 0 0; transition: height 0.4s cubic-bezier(0.32, 0.72, 0, 1); min-height: 3px;
}
.bar-fill.low { background: linear-gradient(180deg, #5AC8FA, #32ADE6); }
.bar-label { font-size: 10.5px; color: var(--label2); margin-top: 5px; }
.bar-dot { width: 5px; height: 5px; border-radius: 50%; margin-top: 4px; background: transparent; }
.bar-dot.has { background: var(--green); }

.ai-result {
  background: var(--fill); border-radius: var(--radius-sm);
  padding: 14px; font-size: 14.5px; white-space: pre-wrap; line-height: 1.75;
}
</style>
