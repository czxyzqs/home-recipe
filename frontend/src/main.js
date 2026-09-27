import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Today from './views/Today.vue'
import Recipes from './views/Recipes.vue'
import RecipeDetail from './views/RecipeDetail.vue'
import Plan from './views/Plan.vue'
import Analysis from './views/Analysis.vue'
import Settings from './views/Settings.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'today', component: Today },
    { path: '/recipes', name: 'recipes', component: Recipes },
    { path: '/recipes/:id', name: 'recipe-detail', component: RecipeDetail },
    { path: '/plan', name: 'plan', component: Plan },
    { path: '/analysis', name: 'analysis', component: Analysis },
    { path: '/settings', name: 'settings', component: Settings },
  ],
})

createApp(App).use(router).mount('#app')
