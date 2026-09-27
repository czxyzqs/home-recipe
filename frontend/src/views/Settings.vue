<template>
  <div class="page">
    <div class="nav-large">
      <div class="nav-title">设置</div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="message" class="ok-banner">{{ message }}</div>

    <!-- 状态 -->
    <div class="group-header">AI 功能</div>
    <div class="group">
      <div class="grow-row">
        <div class="ic ic-blue">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3l1.7 4.6L18.3 9l-4.6 1.7L12 15l-1.7-4.3L5.7 9l4.6-1.4z"/>
            <path d="M18.5 15l.9 2.3 2.1.7-2.1.7-.9 2.3-.9-2.3-2.1-.7 2.1-.7z"/>
          </svg>
        </div>
        <span class="grow" style="font-size: 16px;">AI 状态</span>
        <span class="status" :class="form.configured ? 'on' : 'off'">
          {{ form.configured ? '已配置' : '未配置' }}
        </span>
      </div>
    </div>

    <!-- 大模型配置 -->
    <div class="group-header">大模型 · OpenAI 兼容接口</div>
    <div class="group" style="padding: 16px;">
      <div class="preset-row">
        <button class="chip" v-for="p in PRESETS" :key="p.name" @click="applyPreset(p)">{{ p.name }}</button>
      </div>

      <div class="field">
        <label>Base URL</label>
        <input v-model="form.base_url" class="input" placeholder="https://open.bigmodel.cn/api/paas/v4" />
      </div>
      <div class="field">
        <label>API Key{{ form.api_key_set ? `（已设置：${form.api_key_masked}）` : '' }}</label>
        <input v-model="form.api_key" class="input" type="password" placeholder="留空表示不修改" />
      </div>
      <div class="field">
        <label>模型名</label>
        <input v-model="form.model" class="input" placeholder="glm-4-flash" />
        <div class="help">服务方提供的模型 ID，如 glm-4-flash / deepseek-chat / gpt-4o-mini / qwen-plus</div>
      </div>
      <div class="field">
        <label>创造性 temperature（0-2，越低越稳定）</label>
        <input v-model.number="form.temperature" type="number" min="0" max="2" step="0.1" class="input" />
      </div>

      <div class="row" style="gap: 10px;">
        <button class="btn btn-primary grow" :disabled="saving" @click="save">保存</button>
        <button class="btn btn-ghost grow" :disabled="testing" @click="test">
          {{ testing ? '测试中…' : '保存并测试' }}
        </button>
      </div>
    </div>

    <!-- 说明 -->
    <div class="group-header">说明</div>
    <div class="group" style="padding: 14px 16px;">
      <div class="small text-2" style="line-height: 1.8">
        任何 OpenAI 协议兼容的服务都可以使用（智谱、DeepSeek、OpenAI、通义千问、Ollama 本地模型等）。<br /><br />
        Ollama 本地部署时 Base URL 填 <code>http://主机IP:11434/v1</code>，API Key 随意填写，模型名如 <code>qwen2.5:7b</code>。<br /><br />
        API Key 仅保存在本机 SQLite 数据库中，不会上传到任何第三方。<br /><br />
        AI 功能：生成周计划、按食材生成食谱、营养分析建议。
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { api } from '../api'

const PRESETS = [
  { name: '智谱 GLM', base_url: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash' },
  { name: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  { name: 'OpenAI', base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  { name: '通义千问', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
]

const form = reactive({
  base_url: '', api_key: '', model: '', temperature: 0.7,
  api_key_set: false, api_key_masked: '', configured: false,
})
const saving = ref(false)
const testing = ref(false)
const error = ref('')
const message = ref('')

onMounted(async () => {
  try {
    Object.assign(form, await api.getLLMSetting())
  } catch (e) {
    error.value = e.message
  }
})

function applyPreset(p) {
  form.base_url = p.base_url
  form.model = p.model
}

async function payload() {
  return {
    base_url: form.base_url.trim(),
    api_key: form.api_key.trim(),
    model: form.model.trim(),
    temperature: form.temperature,
  }
}

async function save() {
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    Object.assign(form, await api.saveLLMSetting(await payload()))
    form.api_key = ''
    message.value = '已保存'
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function test() {
  testing.value = true
  error.value = ''
  message.value = ''
  try {
    const res = await api.testLLM(await payload())
    Object.assign(form, await api.getLLMSetting())
    form.api_key = ''
    message.value = `连接成功！模型回复：「${res.reply}」`
  } catch (e) {
    error.value = e.message
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.ic {
  width: 30px; height: 30px; border-radius: 7px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.ic-blue { background: var(--blue); color: #fff; }
.status { font-size: 15px; font-weight: 500; }
.status.on { color: var(--green); }
.status.off { color: var(--label2); }
.preset-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
code {
  background: var(--fill2); padding: 1px 6px; border-radius: 5px;
  font-size: 12px; font-family: SFMono-Regular, Menlo, monospace;
}
</style>
