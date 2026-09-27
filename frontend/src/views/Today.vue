<template>
  <div class="page">
    <!-- iOS 大标题 + 日期切换 -->
    <div class="nav-large">
      <div class="nav-title">今天</div>
    </div>
    <div class="date-nav">
      <button class="nav-circle" @click="shiftDate(-1)">‹</button>
      <div class="date-display" :class="{ today: isToday }" @click="goToday">
        <span class="date-pill">{{ dateLabel }}</span>
      </div>
      <button class="nav-circle" @click="shiftDate(1)">›</button>
    </div>

    <!-- 营养摘要 -->
    <div class="group nutrition-card">
      <div class="cal-main">
        <div class="cal-num">{{ Math.round(nutrition.calories) }}</div>
        <div class="cal-unit">千卡 · 今日已摄入</div>
      </div>
      <div class="macro-row">
        <div class="macro">
          <div class="macro-val">{{ Math.round(nutrition.protein) }}<span class="macro-unit">g</span></div>
          <div class="macro-name">蛋白质</div>
        </div>
        <div class="macro">
          <div class="macro-val">{{ Math.round(nutrition.fat) }}<span class="macro-unit">g</span></div>
          <div class="macro-name">脂肪</div>
        </div>
        <div class="macro">
          <div class="macro-val">{{ Math.round(nutrition.carbs) }}<span class="macro-unit">g</span></div>
          <div class="macro-name">碳水</div>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="message" class="ok-banner">{{ message }}</div>

    <!-- 周计划导入 -->
    <div v-if="planCoveredToday && !hasAnyMeal" class="group" style="padding: 13px 16px;">
      <div class="row-between">
        <div class="grow">
          <div style="font-size: 15px; font-weight: 600">今天有一周计划的安排</div>
          <div class="small text-2 mt-8" style="line-height: 1.5">{{ todayPlanNames }}</div>
        </div>
        <button class="btn btn-green btn-sm" @click="applyToday">一键记录</button>
      </div>
    </div>

    <!-- 今日用餐记录（不分餐段） -->
    <div class="group">
      <div class="group-title">
        <span>用餐记录</span>
        <button class="text-action" @click="openPicker">添加</button>
      </div>
      <div v-if="meals.length === 0" class="grow-row" style="color: var(--label2); font-size: 14px;">还没有记录</div>
      <div v-for="log in meals" :key="log.id" class="grow-row">
        <div class="grow" style="cursor: pointer;" @click="log.recipe_id && $router.push(`/recipes/${log.recipe_id}`)">
          <div class="meal-name">
            {{ log.recipe ? log.recipe.name : log.custom_name }}
            <span v-if="log.servings != 1" class="text-2" style="font-size: 13px;"> ×{{ log.servings }}</span>
          </div>
        </div>
        <span class="kcal">{{ log.recipe ? Math.round(log.recipe.calories * log.servings) + ' 千卡' : '自定义' }}</span>
        <button class="del-btn" @click="removeMeal(log)">−</button>
      </div>
    </div>

    <!-- 添加弹层 -->
    <div v-if="picker.show" class="sheet-mask" @click.self="picker.show = false">
      <div class="sheet">
        <div class="grabber"></div>
        <div class="sheet-header">
          <span>添加用餐记录</span>
          <button class="sheet-close" @click="picker.show = false">完成</button>
        </div>
        <div class="sheet-body">
          <div class="search-box">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.8-3.8"/></svg>
            <input v-model="picker.q" placeholder="搜索食谱" @input="onSearch" />
          </div>
          <div v-if="picker.loading" class="loading"><span class="spinner"></span></div>
          <template v-else>
            <div class="pick-list">
              <div
                v-for="r in picker.results" :key="r.id" class="pick-item"
                :class="{ active: picker.selected && picker.selected.id === r.id }"
                @click="picker.selected = r"
              >
                <div class="grow">
                  <div style="font-size: 15.5px; font-weight: 500;">{{ r.name }}</div>
                  <div class="small text-2">{{ Math.round(r.calories) }} 千卡/份 · 蛋白{{ Math.round(r.protein) }}g</div>
                </div>
                <div v-if="picker.selected && picker.selected.id === r.id" class="pick-check">✓</div>
              </div>
            </div>
            <div v-if="!picker.results.length && picker.q" class="empty small" style="padding: 20px 8px;">
              没找到「{{ picker.q }}」，可在下方直接记录这道菜
            </div>
          </template>

          <div class="field mt-16">
            <label>或自定义菜名（不在食谱库）</label>
            <input v-model="picker.customName" class="input" placeholder="例如：楼下买的煎饼" />
          </div>
          <div class="field">
            <label>份数（人份）</label>
            <input v-model.number="picker.servings" type="number" min="0.1" step="0.5" class="input" />
          </div>
          <button class="btn btn-primary btn-block" :disabled="!canSubmit || picker.submitting" @click="submitPick">
            {{ picker.submitting ? '保存中…' : '保存记录' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted, watch } from 'vue'
import { api } from '../api'
import { addDays, fmtDate, parseDate, weekdayZh } from '../utils'

const dateStr = ref(fmtDate(new Date()))
const meals = ref([])
const nutrition = ref({ calories: 0, protein: 0, fat: 0, carbs: 0, meals: 0 })
const plan = ref(null)
const error = ref('')
const message = ref('')

const picker = reactive({
  show: false, q: '', results: [], loading: false,
  selected: null, customName: '', servings: 1, submitting: false,
})
let searchTimer = null

const isToday = computed(() => dateStr.value === fmtDate(new Date()))
const dateLabel = computed(() => {
  const d = parseDate(dateStr.value)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${weekdayZh(d)}`
})
const hasAnyMeal = computed(() => meals.value.length > 0)
const planCoveredToday = computed(() => {
  if (!plan.value) return false
  return plan.value.items.some(i => i.date === dateStr.value)
})
const todayPlanNames = computed(() => {
  if (!plan.value) return ''
  return plan.value.items.filter(i => i.date === dateStr.value)
    .map(i => i.recipe?.name || '').filter(Boolean).join('、')
})

function shiftDate(n) {
  const d = addDays(parseDate(dateStr.value), n)
  dateStr.value = fmtDate(d)
}

function goToday() {
  if (!isToday.value) dateStr.value = fmtDate(new Date())
}

async function load() {
  error.value = ''
  try {
    const [m, n] = await Promise.all([
      api.listMeals(dateStr.value),
      api.dailyNutrition(dateStr.value),
    ])
    meals.value = m
    nutrition.value = n
  } catch (e) {
    error.value = e.message
  }
}

watch(dateStr, () => { message.value = ''; load() })
onMounted(async () => {
  load()
  try { plan.value = await api.currentPlan() } catch { /* 忽略 */ }
})

function openPicker() {
  picker.show = true
  picker.q = ''
  picker.customName = ''
  picker.servings = 1
  picker.selected = null
  runSearch()
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(runSearch, 250)
}

async function runSearch() {
  picker.loading = true
  try {
    picker.results = await api.listRecipes(picker.q.trim())
  } catch (e) {
    error.value = e.message
    picker.results = []
  } finally {
    picker.loading = false
  }
}

const canSubmit = computed(() => picker.selected || picker.customName.trim())

async function submitPick() {
  picker.submitting = true
  try {
    await api.addMeal({
      date: dateStr.value,
      recipe_id: picker.selected ? picker.selected.id : null,
      custom_name: picker.selected ? '' : picker.customName.trim(),
      servings: picker.servings || 1,
    })
    picker.show = false
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    picker.submitting = false
  }
}

async function removeMeal(log) {
  if (!confirm(`删除「${log.recipe ? log.recipe.name : log.custom_name}」这条记录？`)) return
  try {
    await api.deleteMeal(log.id)
    await load()
  } catch (e) {
    error.value = e.message
  }
}

async function applyToday() {
  try {
    const res = await api.applyPlanDay(plan.value.id, dateStr.value)
    message.value = `已按计划记录 ${res.added.length} 道菜`
    await load()
  } catch (e) {
    error.value = e.message
  }
}
</script>

<style scoped>
.date-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 20px 18px; gap: 12px;
}
.date-display { flex: 1; text-align: center; }
.date-pill {
  display: inline-block; font-size: 15px; font-weight: 600;
  background: var(--fill); border-radius: 999px; padding: 7px 18px;
}
.date-display.today .date-pill { background: var(--blue); color: #fff; }
.date-display:active { opacity: 0.6; }

.nutrition-card { text-align: center; padding: 22px 16px 16px; }
.cal-num { font-size: 52px; font-weight: 800; color: var(--blue); line-height: 1.05; letter-spacing: -1px; font-variant-numeric: tabular-nums; }
.cal-unit { color: var(--label2); font-size: 13.5px; margin-top: 4px; }
.macro-row { display: flex; margin-top: 16px; border-top: 0.5px solid var(--sep-soft); padding-top: 14px; }
.macro { flex: 1; }
.macro-val { font-size: 19px; font-weight: 700; font-variant-numeric: tabular-nums; }
.macro-unit { font-size: 12px; color: var(--label2); margin-left: 1px; font-weight: 400; }
.macro-name { font-size: 12.5px; color: var(--label2); margin-top: 2px; }

.text-action {
  background: none; border: none; color: var(--blue);
  font-size: 15px; font-weight: 600; font-family: inherit; cursor: pointer; padding: 4px;
}
.text-action:active { opacity: 0.4; }

.meal-name { font-weight: 500; font-size: 15.5px; }
.kcal { color: var(--label2); font-size: 13.5px; font-variant-numeric: tabular-nums; flex-shrink: 0; }
.del-btn {
  width: 28px; height: 28px; border-radius: 50%; border: none;
  background: rgba(255, 59, 48, 0.12); color: var(--red);
  font-size: 17px; font-weight: 700; cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; padding-bottom: 1px;
}
.del-btn:active { opacity: 0.4; }

.pick-list { max-height: 40vh; overflow-y: auto; border-radius: var(--radius-sm); }
.pick-item {
  display: flex; align-items: center; gap: 10px;
  padding: 11px 13px; border-radius: var(--radius-sm);
  margin-bottom: 6px; cursor: pointer; background: var(--card);
}
.pick-item.active { background: rgba(0, 122, 255, 0.1); }
.pick-check { color: var(--blue); font-weight: 700; font-size: 17px; }
</style>
