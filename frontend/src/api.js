const BASE = ''

async function request(path, options = {}) {
  const resp = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!resp.ok) {
    let msg = `请求失败 (${resp.status})`
    try {
      const data = await resp.json()
      if (data.detail) msg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    } catch { /* ignore */ }
    throw new Error(msg)
  }
  return resp.json()
}

export const api = {
  // 食谱
  listRecipes: (q = '', category = '', page = 1, pageSize = 10) =>
    request(`/api/recipes?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}&page=${page}&page_size=${pageSize}`),
  listCategories: () => request('/api/recipes/categories'),
  getRecipe: (id) => request(`/api/recipes/${id}`),
  createRecipe: (data) => request('/api/recipes', { method: 'POST', body: JSON.stringify(data) }),
  updateRecipe: (id, data) => request(`/api/recipes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteRecipe: (id) => request(`/api/recipes/${id}`, { method: 'DELETE' }),
  aiGenerateRecipes: (prompt, count = 1) =>
    request('/api/recipes/ai-generate', { method: 'POST', body: JSON.stringify({ prompt, count }) }),

  // 每日记录
  listMeals: (date) => request(`/api/meals?date=${date}`),
  addMeal: (data) => request('/api/meals', { method: 'POST', body: JSON.stringify(data) }),
  deleteMeal: (id) => request(`/api/meals/${id}`, { method: 'DELETE' }),

  // 营养
  dailyNutrition: (date) => request(`/api/nutrition/daily?date=${date}`),
  rangeNutrition: (start, end) => request(`/api/nutrition/range?start=${start}&end=${end}`),
  aiAnalyze: (startDate, days) =>
    request('/api/nutrition/ai-analyze', { method: 'POST', body: JSON.stringify({ start_date: startDate, days }) }),

  // 计划
  currentPlan: () => request('/api/plans/current'),
  generatePlan: (startDate = null) =>
    request('/api/plans/generate', { method: 'POST', body: JSON.stringify(startDate ? { start_date: startDate } : {}) }),
  createPlan: (startDate) =>
    request('/api/plans', { method: 'POST', body: JSON.stringify({ start_date: startDate }) }),
  addPlanItem: (planId, data) =>
    request(`/api/plans/${planId}/items`, { method: 'POST', body: JSON.stringify(data) }),
  deletePlanItem: (itemId) => request(`/api/plans/items/${itemId}`, { method: 'DELETE' }),
  applyPlanDay: (planId, date) =>
    request(`/api/plans/${planId}/apply-day`, { method: 'POST', body: JSON.stringify({ date }) }),
  deletePlan: (id) => request(`/api/plans/${id}`, { method: 'DELETE' }),

  // 设置
  getLLMSetting: () => request('/api/settings/llm'),
  saveLLMSetting: (data) => request('/api/settings/llm', { method: 'PUT', body: JSON.stringify(data) }),
  testLLM: (data) => request('/api/settings/llm/test', { method: 'POST', body: JSON.stringify(data) }),
}
