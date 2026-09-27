# 🍳 家庭食谱系统

一个为家庭设计的自托管食谱管理系统：管理食谱、记录每日饮食、AI 生成一周食谱、营养统计分析。苹果 iOS 风格界面（自适应深色模式），Docker 一键部署。

## 功能

| 模块 | 说明 |
|------|------|
| 🍽️ 今天 | 记录每天吃了什么（不区分餐段，按添加顺序统一列表），实时汇总当日热量与三大营养素 |
| 📖 食谱库 | 食谱 CRUD（食材、步骤、每份营养数据），支持搜索与分类筛选（家常菜/荤菜/素菜/汤羹/甜点）；✨AI 按食材生成新食谱 |
| 🗓️ 周计划 | AI 参考最近两周的历史用餐记录 + 食谱库，生成营养均衡、避免重复的一周三餐计划，可一键把某天记入当日记录 |
| 📊 营养 | 按周查看每日热量条形图与日均营养素，✨AI 输出膳食分析与改进建议 |
| ⚙️ 设置 | 配置大模型（OpenAI 兼容协议），内置智谱 / DeepSeek / OpenAI / 通义预设，支持连通性测试 |

## 技术栈

- **后端**：Python FastAPI + SQLAlchemy + SQLite（数据单文件，零运维）
- **前端**：Vue 3 + Vite + Vue Router，苹果 iOS 设计风格（HIG：系统色板、大标题导航、分组列表、毛玻璃底部 Tab 栏、原生 Sheet 弹层，自动适配深色模式），构建产物由后端托管
- **大模型**：OpenAI 兼容 Chat Completions 协议（智谱 GLM、DeepSeek、OpenAI、通义千问、本地 Ollama 均可）
- **部署**：多阶段 Docker 构建，单一容器，数据通过卷持久化

## 快速开始（Docker，推荐）

```bash
docker compose up -d --build
```

打开 `http://服务器IP:8000`（手机浏览器访问局域网地址即可，可"添加到主屏幕"当 App 用）。

数据保存在 `./data/recipe.db`，备份拷走这个文件即可。

## 本地开发

```bash
# 后端（端口 8000）
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端（端口 5173，已代理 /api 到 8000）
cd frontend
npm install
npm run dev
```

首次启动会自动初始化 SQLite 并写入 18 道家常菜种子数据（家常菜 / 荤菜 / 素菜 / 汤羹）。

## 配置大模型

进入「设置」页，填三项：

| 厂商 | Base URL | 模型名示例 |
|------|----------|-----------|
| 智谱 AI | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Ollama 本地 | `http://主机IP:11434/v1` | `qwen2.5:7b` |

点「保存并测试」通过后即可使用全部 AI 功能。API Key 只存在本机数据库，不经过任何第三方。

## API 一览

```
GET/POST /api/recipes            食谱列表/新建        POST /api/recipes/ai-generate      AI 生成食谱
GET/PUT/DELETE /api/recipes/:id  食谱详情/更新/删除
GET/POST /api/meals?date=        某日记录             DELETE /api/meals/:id
GET /api/nutrition/daily         单日营养汇总         GET /api/nutrition/range           区间每日汇总
POST /api/nutrition/ai-analyze   AI 膳食分析
GET /api/plans/current           当前周计划           POST /api/plans/generate           AI 生成周计划
POST /api/plans/:id/apply-day    计划某天一键记录     DELETE /api/plans/:id
GET/PUT /api/settings/llm        LLM 配置读写         POST /api/settings/llm/test        连通性测试
```

交互式文档：`http://localhost:8000/docs`（FastAPI 自带）。

## 目录结构

```
home-recipe/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口 + SPA 托管
│   │   ├── database.py      # SQLAlchemy 模型（4 张表）
│   │   ├── schemas.py       # Pydantic 请求/响应模型
│   │   ├── config.py        # LLM 设置持久化
│   │   ├── llm.py           # OpenAI 兼容客户端 + JSON 容错解析
│   │   ├── seed.py          # 首启种子食谱（18 道家常菜）
│   │   └── routers/         # recipes / meals / nutrition / plans / settings
│   └── requirements.txt
├── frontend/
│   └── src/views/           # Today / Recipes / RecipeDetail / Plan / Analysis / Settings
├── Dockerfile               # 多阶段：node 构建前端 → python 运行
├── docker-compose.yml       # 端口 8000，数据卷 ./data:/data
└── data/                    # SQLite 数据库（挂载卷）
```
