<template>
  <div class="page">
    <div class="nav-row">
      <div class="nav-title">周计划</div>
      <div class="row" style="gap: 14px;">
        <button class="nav-action" @click="openCreate">＋ 新建</button>
        <button class="nav-action" :disabled="generating" @click="generate">✨ 生成</button>
      </div>
    </div>
    <div class="nav-hint">AI 参考历史记录生成，或手工从食谱库挑选</div>

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
        <div class="group-header">{{ day.label }}<template v-if="day.isToday"> · 今天</template></div>
        <div class="group">
          <div v-if="!day.items.length" class="grow-row" style="color: var(--label2); font-size: 14px;">还没有安排</div>
          <div v-for="item in day.items" :key="item.id" class="grow-row">
            <span class="meal-badge" :class="item.meal_type">{{ mealZh(item.meal_type) }}</span>
            <span class="grow tappable-name" @click="item.recipe && $router.push(`/recipes/${item.recipe.id}`)">{{ item.recipe ? item.recipe.name : '未知' }}</span>
            <span class="text-2 kcal" v-if="item.recipe">{{ Math.round(item.recipe.calories) }} 千卡</span>
            <button class="del-btn" @click="removeItem(item)">−</button>
          </div>
          <div class="apply-row" style="gap: 18px;">
            <button class="text-action" @click="openPicker(day)">＋ 添加菜品</button>
            <button v-if="day.items.length" class="text-action sub" @click="applyDay(day)">记入这天</button>
          </div>
        </div>
      </template>
    </template>

    <div v-if="!plan && !generating" class="empty">
      <div class="empty-icon">🗓️</div>
      还没有周计划<br />
      <span class="small text-2">「生成」让 AI 参考你的历史记录自动安排<br />「新建」手工从食谱库挑选菜品</span>
    </div>

    <!-- 手工创建计划 -->
    <div v-if="create.show" class="sheet-mask" @click.self="create.show = false">
      <div class="sheet">
        <div class="grabber"></div>
        <div class="sheet-header">
          <span>手工创建周计划</span>
          <button class="sheet-close" @click="create.show = false">取消</button>
        </div>
        <div class="sheet-body">
          <div class="field">
            <label>开始日期（周一）</label>
            <input v-model="create.startDate" type="date" class="input" />
            <div class="help">默认从下周一开始，共 7 天；创建后可逐天挑选菜品</div>
          </div>
          <button class="btn btn-primary btn-block" :disabled="!create.startDate" @click="submitCreate">创建</button>
        </div>
      </div>
    </div>

    <!-- 挑选菜品 -->
    <div v-if="picker.show" class="sheet-mask" @click.self="picker.show = false">
      <div class="sheet">
        <div class="grabber"></div>
        <div class="sheet-header">
          <span>添加到 {{ picker.dayLabel }}</span>
          <button class="sheet-close" @click="picker.show = false">完成</button>
        </div>
        <div class="sheet-body">
          <div class="meal-chips">
            <button
              v-for="mt in PLAN_MEALS" :key="mt.key"
              class="chip" :class="{ active: picker.mealType === mt.key }"
              @click="picker.mealType = mt.key"
            >{{ mt.zh }}</button>
          </div>
          <div class="search-box" style="margin: 0 0 10px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.8-3.8"/></svg>
            <input v-model="picker.q" placeholder="搜索食谱" @input="onSearch" />
          </div>
          <div v-if="picker.loading" class="loading"><span class="spinner"></span></div>
          <div v-else class="pick-list">
            <div
              v-for="r in picker.results" :key="r.id" class="pick-item"
              :class="{ added: addedNames.has(r.name) }"
              @click="pickRecipe(r)"
            >
              <div class="grow">
                <div style="font-size: 15.5px; font-weight: 500;">{{ r.name }}</div>
                <div class="small text-2">{{ r.category }} · {{ Math.round(r.calories) }} 千卡/份</div>
              </div>
              <div v-if="addedNames.has(r.name)" class="added-mark">✓</div>
              <div v-else class="add-mark">＋</div>
            </div>
            <div v-if="!picker.results.length" class="empty small" style="padding: 16px;">没有匹配的食谱</div>
          </div>
          <div v-if="picker.addedCount" class="small center text-2 mt-8" style="padding: 6px 0;">
            已添加 {{ picker.addedCount }} 道，继续挑选或点「完成」
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { api } from '../api'
import { addDays, fmtDate, mondayOf, parseDate, weekdayZh, MEAL_TYPES } from '../utils'

const PLAN_MEALS = MEAL_TYPES  // breakfast/lunch/dinner/snack
const MEAL_ZH = Object.fromEntries(MEAL_TYPES.map(m => [m.key, m.zh]))

const plan = ref(null)
const generating = ref(false)
const error = ref('')
const message = ref('')

const create = reactive({ show: false, startDate: '' })
const picker = reactive({
  show: false, day: null, dayLabel: '', mealType: 'lunch',
  q: '', results: [], loading: false, addedCount: 0,
})
let searchTimer = null

function mealZh(key) {
  return MEAL_ZH[key] || key
}

// 手工计划展开全部 7 天（便于挑选）；AI 计划只显示有安排的工作日（休息日不生成）
const days = computed(() => {
  if (!plan.value) return []
  const today = fmtDate(new Date())
  const byDate = {}
  for (const item of plan.value.items) {
    ;(byDate[item.date] = byDate[item.date] || []).push(item)
  }
  const toDay = (ds) => {
    const d = parseDate(ds)
    return {
      date: ds,
      label: `${d.getMonth() + 1}/${d.getDate()} ${weekdayZh(d)}`,
      isToday: ds === today,
      items: byDate[ds] || [],
    }
  }
  if (plan.value.mode === 'manual') {
    const start = parseDate(plan.value.start_date)
    return Array.from({ length: 7 }, (_, i) => toDay(fmtDate(addDays(start, i))))
  }
  return Object.keys(byDate).sort().map(toDay)
})

const addedNames = computed(() => {
  if (!picker.day || !plan.value) return new Set()
  return new Set(
    plan.value.items.filter(i => i.date === picker.day).map(i => i.recipe?.name).filter(Boolean)
  )
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

function nextMondayStr() {
  // 本周一（无论今天周几）+7 = 下周一
  return fmtDate(addDays(mondayOf(new Date()), 7))
}

function openCreate() {
  create.startDate = nextMondayStr()
  create.show = true
}

async function submitCreate() {
  try {
    plan.value = await api.createPlan(create.startDate)
    create.show = false
    message.value = '已创建空计划，点击每天下方的「添加菜品」开始挑选'
  } catch (e) {
    error.value = e.message
  }
}

function openPicker(day) {
  picker.show = true
  picker.day = day.date
  picker.dayLabel = day.label
  picker.q = ''
  picker.addedCount = 0
  // 默认选中当前最少安排的餐段之后：简单起见默认午餐
  picker.mealType = 'lunch'
  runSearch()
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(runSearch, 250)
}

async function runSearch() {
  picker.loading = true
  try {
    const res = await api.listRecipes(picker.q.trim(), '', 1, 50)
    picker.results = res.items
  } catch (e) {
    error.value = e.message
    picker.results = []
  } finally {
    picker.loading = false
  }
}

async function pickRecipe(r) {
  if (addedNames.value.has(r.name)) return
  try {
    await api.addPlanItem(plan.value.id, {
      date: picker.day,
      meal_type: picker.mealType,
      recipe_id: r.id,
    })
    picker.addedCount += 1
    await load()  // 刷新计划（addedNames 随之更新）
  } catch (e) {
    error.value = e.message
  }
}

async function removeItem(item) {
  const name = item.recipe ? item.recipe.name : ''
  if (!confirm(`从计划中移除「${name}」？`)) return
  try {
    await api.deletePlanItem(item.id)
    await load()
  } catch (e) {
    error.value = e.message
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

.tappable-name { font-weight: 500; font-size: 15px; cursor: pointer; }
.kcal { font-size: 13px; font-variant-numeric: tabular-nums; }
.del-btn {
  width: 26px; height: 26px; border-radius: 50%; border: none;
  background: rgba(255, 59, 48, 0.12); color: var(--red);
  font-size: 16px; font-weight: 700; cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; padding-bottom: 1px;
}
.del-btn:active { opacity: 0.4; }
.apply-row {
  padding: 9px 16px; display: flex; justify-content: center;
  border-top: 0.5px solid var(--sep-soft);
}
.text-action {
  background: none; border: none; color: var(--blue);
  font-size: 14.5px; font-weight: 600; font-family: inherit; cursor: pointer;
}
.text-action.sub { color: var(--green); }
.text-action:active { opacity: 0.4; }

.meal-chips { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.pick-list { max-height: 46vh; overflow-y: auto; }
.pick-item {
  display: flex; align-items: center; gap: 10px;
  padding: 11px 13px; border-radius: var(--radius-sm);
  margin-bottom: 6px; cursor: pointer; background: var(--card);
}
.pick-item.added { opacity: 0.55; }
.pick-item:active { background: var(--fill-tertiary); }
.add-mark {
  width: 26px; height: 26px; border-radius: 50%;
  background: rgba(0, 122, 255, 0.12); color: var(--blue);
  font-size: 16px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.added-mark { color: var(--green); font-weight: 700; font-size: 17px; width: 26px; text-align: center; }
</style>
