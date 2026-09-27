<template>
  <div class="page">
    <div class="back-row" @click="$router.back()">
      <span class="back-chevron">‹</span>
      <span class="back-text">返回</span>
    </div>

    <div v-if="loading" class="loading"><span class="spinner"></span></div>
    <div v-else-if="!recipe" class="empty"><div class="empty-icon">🤔</div>食谱不存在</div>

    <template v-else>
      <div class="nav-large">
        <div class="nav-title">{{ recipe.name }}</div>
        <div class="nav-sub">
          {{ recipe.category }}<template v-if="recipe.cuisine"> · {{ recipe.cuisine }}</template>
          <template v-if="recipe.tags.length"> · {{ recipe.tags.join(' · ') }}</template>
          <span v-if="recipe.is_ai_generated" class="tag tag-purple" style="margin-left: 6px;">AI 生成</span>
        </div>
      </div>

      <div class="group" style="padding: 18px 16px 14px;">
        <div class="nutri-grid">
          <div class="nutri"><div class="nutri-val">{{ Math.round(recipe.calories) }}</div><div class="nutri-name">千卡/份</div></div>
          <div class="nutri"><div class="nutri-val">{{ Math.round(recipe.protein) }}g</div><div class="nutri-name">蛋白质</div></div>
          <div class="nutri"><div class="nutri-val">{{ Math.round(recipe.fat) }}g</div><div class="nutri-name">脂肪</div></div>
          <div class="nutri"><div class="nutri-val">{{ Math.round(recipe.carbs) }}g</div><div class="nutri-name">碳水</div></div>
        </div>
        <div v-if="recipe.description" class="desc">{{ recipe.description }}</div>
      </div>

      <div class="group-header">食材</div>
      <div class="group">
        <div v-if="!recipe.ingredients.length" class="grow-row" style="color: var(--label2); font-size: 14px;">暂无</div>
        <div v-for="(ing, i) in recipe.ingredients" :key="i" class="grow-row">
          <span class="grow">{{ ing.name }}</span>
          <span class="text-2">{{ ing.amount }}</span>
        </div>
      </div>

      <div class="group-header">做法</div>
      <div class="group" style="padding: 8px 16px;">
        <div v-if="!recipe.steps.length" class="grow-row" style="color: var(--label2); font-size: 14px;">暂无</div>
        <div v-for="(step, i) in recipe.steps" :key="i" class="step-row">
          <span class="step-no">{{ i + 1 }}</span>
          <span>{{ step }}</span>
        </div>
      </div>

      <div v-if="error" class="error-banner">{{ error }}</div>

      <div class="group-header">记录到今天</div>
      <div class="group">
        <div class="grow-row tappable" @click="logMeal">
          <span class="grow" style="font-size: 16px;">🍽️ 记入今日用餐</span>
          <span class="chevron">›</span>
        </div>
      </div>

      <div class="group" style="padding: 0;">
        <button class="btn btn-danger-ghost btn-block" style="border-radius: 0; min-height: 50px;" @click="remove">删除食谱</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { fmtDate } from '../utils'

const route = useRoute()
const router = useRouter()
const recipe = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    recipe.value = await api.getRecipe(route.params.id)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

async function logMeal() {
  try {
    await api.addMeal({ date: fmtDate(new Date()), recipe_id: recipe.value.id, servings: 1 })
    router.push('/')
  } catch (e) {
    error.value = e.message
  }
}

async function remove() {
  if (!confirm(`确定删除「${recipe.value.name}」？相关记录将变成自定义菜名。`)) return
  try {
    await api.deleteRecipe(recipe.value.id)
    router.push('/recipes')
  } catch (e) {
    error.value = e.message
  }
}
</script>

<style scoped>
.back-row {
  display: inline-flex; align-items: center; gap: 2px;
  padding: 10px 8px 2px 16px; cursor: pointer; color: var(--blue);
}
.back-row:active { opacity: 0.4; }
.back-chevron { font-size: 26px; font-weight: 500; line-height: 1; margin-top: -2px; }
.back-text { font-size: 16px; }

.nutri-grid { display: flex; text-align: center; }
.nutri { flex: 1; }
.nutri-val { font-size: 20px; font-weight: 700; color: var(--blue); font-variant-numeric: tabular-nums; }
.nutri-name { font-size: 12px; color: var(--label2); margin-top: 2px; }
.desc { font-size: 14px; color: var(--label2); text-align: center; margin-top: 14px; }

.step-row { display: flex; gap: 12px; padding: 10px 0; font-size: 15px; align-items: flex-start; }
.step-row + .step-row { border-top: 0.5px solid var(--sep-soft); }
.step-no {
  flex-shrink: 0; width: 22px; height: 22px; border-radius: 50%;
  background: rgba(0, 122, 255, 0.12); color: var(--blue);
  font-size: 12.5px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  margin-top: 1px;
}
</style>
