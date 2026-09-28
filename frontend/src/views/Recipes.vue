<template>
  <div class="page">
    <div class="nav-row">
      <div class="nav-title">食谱库</div>
      <button class="nav-action" @click="openEdit(null)">＋ 新建</button>
    </div>

    <div class="search-box">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.8-3.8"/></svg>
      <input v-model="q" placeholder="搜索菜名 / 食材" @input="onSearch" />
    </div>
    <div class="chips">
      <button class="chip" :class="{ active: category === '' }" @click="setCategory('')">全部</button>
      <button v-for="c in categories" :key="c" class="chip" :class="{ active: category === c }" @click="setCategory(c)">{{ c }}</button>
    </div>

    <!-- AI 生成入口 -->
    <div class="group">
      <div class="grow-row tappable" @click="openAI">
        <div class="ai-icon">
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3l1.7 4.6L18.3 9l-4.6 1.7L12 15l-1.7-4.3L5.7 9l4.6-1.4z"/>
            <path d="M18.5 15l.9 2.3 2.1.7-2.1.7-.9 2.3-.9-2.3-2.1-.7 2.1-.7z"/>
          </svg>
        </div>
        <div class="grow">
          <div style="font-size: 15.5px; font-weight: 600;">AI 帮我想菜</div>
          <div class="small text-2">输入手头的食材，让大模型生成新食谱</div>
        </div>
        <span class="chevron">›</span>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="loading"><span class="spinner"></span></div>

    <!-- 食谱列表（iOS 分组列表 · 分页） -->
    <div class="group list" v-if="recipes.length">
      <div v-for="r in recipes" :key="r.id" class="grow-row tappable" @click="$router.push(`/recipes/${r.id}`)">
        <div class="grow">
          <div class="recipe-name">
            {{ r.name }}
            <span v-if="r.is_ai_generated" class="tag tag-purple" style="margin-left: 4px;">AI</span>
          </div>
          <div class="small text-2 recipe-sub">
            {{ r.category }}{{ r.tags.length ? ' · ' + r.tags.slice(0, 2).join(' · ') : '' }} · {{ Math.round(r.calories) }} 千卡/份
          </div>
        </div>
        <span class="chevron">›</span>
      </div>
    </div>

    <!-- 翻页器 -->
    <div v-if="totalPages > 1" class="pager">
      <button class="nav-circle" :disabled="page <= 1" @click="goPage(page - 1)">‹</button>
      <span class="page-ind">{{ page }} / {{ totalPages }} 页 · 共 {{ total }} 道</span>
      <button class="nav-circle" :disabled="page >= totalPages" @click="goPage(page + 1)">›</button>
    </div>

    <div v-if="!loading && !recipes.length" class="empty">
      <div class="empty-icon">🍳</div>
      没有找到食谱，试试别的关键词
    </div>

    <!-- 编辑/新建弹层 -->
    <div v-if="edit.show" class="sheet-mask" @click.self="edit.show = false">
      <div class="sheet">
        <div class="grabber"></div>
        <div class="sheet-header">
          <button class="sheet-close" style="font-weight: 400;" @click="edit.show = false">取消</button>
          <span>{{ edit.form.id ? '编辑食谱' : '新建食谱' }}</span>
          <button class="sheet-close" style="font-weight: 700;" :disabled="!edit.form.name || edit.saving" @click="saveEdit">保存</button>
        </div>
        <div class="sheet-body">
          <div class="field"><label>菜名 *</label><input v-model="edit.form.name" class="input" placeholder="例如：番茄炒蛋" /></div>
          <div class="row">
            <div class="field grow"><label>分类</label>
              <select v-model="edit.form.category" class="select">
                <option v-for="c in ['家常菜','荤菜','素菜','汤羹','甜点']" :key="c">{{ c }}</option>
              </select>
            </div>
            <div class="field grow"><label>菜系</label><input v-model="edit.form.cuisine" class="input" placeholder="家常" /></div>
          </div>
          <div class="field"><label>简介</label><input v-model="edit.form.description" class="input" placeholder="一句话介绍" /></div>
          <div class="field">
            <label>食材（每行一项：名称,用量）</label>
            <textarea v-model="edit.ingredientsText" class="textarea" placeholder="番茄,2个&#10;鸡蛋,3个"></textarea>
          </div>
          <div class="field">
            <label>步骤（每行一步）</label>
            <textarea v-model="edit.stepsText" class="textarea" placeholder="鸡蛋打散&#10;热油炒蛋"></textarea>
          </div>
          <div class="nutri-inputs">
            <div class="field"><label>热量 kcal</label><input v-model.number="edit.form.calories" type="number" class="input" /></div>
            <div class="field"><label>蛋白 g</label><input v-model.number="edit.form.protein" type="number" class="input" /></div>
            <div class="field"><label>脂肪 g</label><input v-model.number="edit.form.fat" type="number" class="input" /></div>
            <div class="field"><label>碳水 g</label><input v-model.number="edit.form.carbs" type="number" class="input" /></div>
          </div>
          <div class="field"><label>标签（逗号分隔）</label><input v-model="edit.tagsText" class="input" placeholder="快手菜,下饭" /></div>
        </div>
      </div>
    </div>

    <!-- AI 生成弹层 -->
    <div v-if="ai.show" class="sheet-mask" @click.self="ai.show = false">
      <div class="sheet">
        <div class="grabber"></div>
        <div class="sheet-header">
          <span>AI 生成食谱</span>
          <button class="sheet-close" @click="ai.show = false">完成</button>
        </div>
        <div class="sheet-body">
          <div class="field">
            <label>食材或想法</label>
            <textarea v-model="ai.prompt" class="textarea" placeholder="例如：冰箱里有西兰花、虾仁，想做清淡点的&#10;或者：适合小朋友的菜"></textarea>
            <div class="help">需要先在「设置」页配置大模型</div>
          </div>
          <div class="field">
            <label>生成数量</label>
            <select v-model.number="ai.count" class="select">
              <option :value="1">1 道</option>
              <option :value="2">2 道</option>
              <option :value="3">3 道</option>
            </select>
          </div>
          <button class="btn btn-primary btn-block" :disabled="!ai.prompt.trim() || ai.loading" @click="runAI">
            <span v-if="ai.loading" class="spinner" style="border-color: rgba(255,255,255,.35); border-top-color: #fff;"></span>
            {{ ai.loading ? '生成中，约需 10-30 秒…' : '开始生成' }}
          </button>
          <div v-if="ai.error" class="error-banner mt-16" style="margin-left:0; margin-right:0;">{{ ai.error }}</div>
          <div v-if="ai.done.length" class="ok-banner mt-16" style="margin-left:0; margin-right:0;">
            已生成：{{ ai.done.map(r => r.name).join('、') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'

const route = useRoute()

const recipes = ref([])
const categories = ref([])
const q = ref('')
const category = ref('')
const loading = ref(false)
const error = ref('')
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)
const PAGE_SIZE = 10

const edit = reactive({ show: false, saving: false, form: {}, ingredientsText: '', stepsText: '', tagsText: '' })
const ai = reactive({ show: false, prompt: '', count: 1, loading: false, error: '', done: [] })

let searchTimer = null

async function load(targetPage = page.value) {
  loading.value = true
  error.value = ''
  try {
    const res = await api.listRecipes(q.value.trim(), category.value, targetPage, PAGE_SIZE)
    recipes.value = res.items
    total.value = res.total
    totalPages.value = Math.max(1, res.total_pages)
    page.value = Math.min(targetPage, totalPages.value)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function goPage(p) {
  if (p < 1 || p > totalPages.value || p === page.value) return
  load(p)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => load(1), 250)
}

function setCategory(c) {
  category.value = c
  load(1)
}

onMounted(async () => {
  load()
  try { categories.value = await api.listCategories() } catch { /* 忽略 */ }
  // 从详情页跳转过来编辑指定食谱
  if (route.query.edit) {
    try {
      const r = await api.getRecipe(route.query.edit)
      openEdit(r)
    } catch { /* 忽略 */ }
  }
})

function openEdit(recipe) {
  if (recipe) {
    edit.form = { ...recipe }
    edit.ingredientsText = (recipe.ingredients || []).map(i => `${i.name},${i.amount}`).join('\n')
    edit.stepsText = (recipe.steps || []).join('\n')
    edit.tagsText = (recipe.tags || []).join(',')
  } else {
    edit.form = { name: '', category: '家常菜', cuisine: '家常', description: '', calories: 0, protein: 0, fat: 0, carbs: 0 }
    edit.ingredientsText = ''
    edit.stepsText = ''
    edit.tagsText = ''
  }
  edit.show = true
}

async function saveEdit() {
  edit.saving = true
  try {
    const payload = {
      ...edit.form,
      ingredients: edit.ingredientsText.split('\n').filter(s => s.trim()).map(line => {
        const [name, amount = ''] = line.split(',')
        return { name: name.trim(), amount: amount.trim() }
      }),
      steps: edit.stepsText.split('\n').map(s => s.trim()).filter(Boolean),
      tags: edit.tagsText.split(/[,，]/).map(s => s.trim()).filter(Boolean),
    }
    if (edit.form.id) await api.updateRecipe(edit.form.id, payload)
    else await api.createRecipe(payload)
    edit.show = false
    await load(1)
    try { categories.value = await api.listCategories() } catch { /* 忽略 */ }
  } catch (e) {
    error.value = e.message
  } finally {
    edit.saving = false
  }
}

function openAI() {
  ai.show = true
  ai.error = ''
  ai.done = []
}

async function runAI() {
  ai.loading = true
  ai.error = ''
  ai.done = []
  try {
    ai.done = await api.aiGenerateRecipes(ai.prompt.trim(), ai.count)
    await load(1)
  } catch (e) {
    ai.error = e.message
  } finally {
    ai.loading = false
  }
}
</script>

<style scoped>
.pager {
  display: flex; align-items: center; justify-content: center; gap: 14px;
  padding: 4px 16px 6px;
}
.page-ind { font-size: 14px; color: var(--label2); font-variant-numeric: tabular-nums; }
.recipe-name { font-size: 15.5px; font-weight: 600; }
.recipe-sub { margin-top: 2px; }
.ai-icon {
  width: 30px; height: 30px; border-radius: 7px; flex-shrink: 0;
  background: rgba(175, 82, 222, 0.13); color: var(--purple);
  display: flex; align-items: center; justify-content: center;
}
.nutri-inputs { display: grid; grid-template-columns: 1fr 1fr; gap: 0 10px; }
</style>
