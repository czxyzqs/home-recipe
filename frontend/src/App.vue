<template>
  <div class="app-shell">
    <router-view />
    <nav class="tabbar">
      <div class="tabbar-inner">
        <router-link to="/" class="tab-item" replace>
          <span class="tab-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round">
              <circle cx="12" cy="12" r="8.4" />
              <circle cx="12" cy="12" r="4" />
            </svg>
          </span>
          <span>今天</span>
        </router-link>
        <router-link to="/recipes" class="tab-item" replace>
          <span class="tab-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 6.8C10.7 5.4 8.9 4.7 6.7 4.7c-.8 0-1.6.1-2.4.35v12.6c.8-.25 1.6-.35 2.4-.35 2.2 0 4 .7 5.3 2.1 1.3-1.4 3.1-2.1 5.3-2.1.8 0 1.6.1 2.4.35V5.05c-.8-.25-1.6-.35-2.4-.35-2.2 0-4 .7-5.3 2.1z" />
              <path d="M12 6.8v12.6" />
            </svg>
          </span>
          <span>食谱库</span>
        </router-link>
        <router-link to="/plan" class="tab-item" replace>
          <span class="tab-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round">
              <rect x="3.8" y="5" width="16.4" height="15.2" rx="3.5" />
              <path d="M8.2 3v4M15.8 3v4M3.8 10.2h16.4" />
            </svg>
          </span>
          <span>周计划</span>
        </router-link>
        <router-link to="/analysis" class="tab-item" replace>
          <span class="tab-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round">
              <path d="M5 19.2v-6.4M12 19.2V6M19 19.2v-9.6" />
            </svg>
          </span>
          <span>营养</span>
        </router-link>
        <router-link to="/settings" class="tab-item" replace>
          <span class="tab-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round">
              <path d="M4 7.5h8.6M17.4 7.5H20M4 16.5h2.6M11.4 16.5H20" />
              <circle cx="15" cy="7.5" r="2.5" />
              <circle cx="9" cy="16.5" r="2.5" />
            </svg>
          </span>
          <span>设置</span>
        </router-link>
      </div>
    </nav>
  </div>
</template>

<script setup>
</script>

<style scoped>
.app-shell { min-height: 100vh; }
</style>
