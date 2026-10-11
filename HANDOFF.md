````markdown
# HANDOFF.md

> 最后更新：2026-10-01  
> 项目：AI Video Production Workspace  
> 仓库：`D:\GitHub_kyandi-i\AI_Web`  
> 当前阶段基线：Phase 9 COMPLETE / Phase 10 NOT STARTED

---

# 1. 现状速览

这是一个 **Local-first AI Video Production Workspace**，用于管理 AI 视频项目的 Project → Script → Scene → Shot → Asset / CharacterState → Prompt → Storyboard → Video Result 工作流，本身当前不直接调用图片/视频生成 API。

**Phase 0～9 已完成；当前真实数据库 revision 为 `0009_storyboards`，最新提交为 `baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2`（`feat: add storyboard workflow`）。**

下一步是 **Phase 10 — Video Result**：先审计 `PROJECT_PLAN.md` 和 `docs/PHASE_9_STATUS.md` 冻结 VideoResult 边界，再实现 Video Result 的 Asset 关系、版本、Selected、来源关系、Shot Workspace UI、测试和安全 migration；**不得提前进入 Phase 11，也不得接入真实视频生成 API。**

---

# 2. 目标与约束

## 2.1 最终产品目标

产品定位：

```text
Local-first AI Video Production Workspace
```

它是：

```text
AI 视频生产项目管理与生产上下文工作台
```

不是：

```text
AI 聊天工具
SaaS 营销 Dashboard
图片生成器
视频生成器
Premiere 式视频编辑器
```

最终业务链路：

```text
Project
→ Script
→ Scene
→ Shot
→ Character / CharacterState
→ Reference Assets
→ Structured Shot Requirements
→ Prompt Template
→ AI Prompt Generation
→ Prompt History / Version
→ 外部图片/视频平台
→ Storyboard 导回
→ Storyboard Version / Selected
→ Video Result 导回
→ Video Version / Selected
→ Shot DONE
```

当前已经做到：

```text
Project
→ Script
→ Scene
→ Shot
→ Asset
→ Character / CharacterState
→ Shot Workspace
→ Prompt Template
→ AI Prompt Generation
→ Prompt Versioning
→ Storyboard Workflow
```

下一步：

```text
Phase 10

Shot
+
Storyboard / Prompt provenance
+
VIDEO Asset
↓
Video Result
↓
V1 / V2 / V3
↓
Selected
```

---

## 2.2 MVP 边界

MVP 负责：

```text
项目管理
剧本结构
Scene
Shot

统一 Asset Library

Character
CharacterState

Shot Workspace

Prompt Template
AI Prompt Generation
Prompt History / Version

Storyboard Workflow

Video Result

Project Export

Recycle Bin 基础
```

MVP 当前不负责：

```text
用户注册 / 登录
多人实时协作
云同步
聊天

Premiere 式时间轴
在线视频编辑

复杂版本分支
审批流
权限系统

SaaS 计费
插件市场
```

当前图片 / 视频直接生成 API：

```text
不做
```

未来架构可以增加：

```text
GenerationProvider
GenerationJob
IMAGE / VIDEO
```

但不能破坏当前：

```text
Prompt
→ 外部平台
→ Result 导回 Workspace
```

的主业务模型。

---

## 2.3 技术栈

### Frontend

```text
React
TypeScript
Vite
Tailwind CSS
shadcn/ui
React Router
TanStack Query
Zod
lucide-react
```

React Hook Form 是否仍是当前实际依赖：

```text
必须以 frontend/package.json 为准
```

不要凭旧设计文档猜测。

### Backend

```text
Python
FastAPI
SQLAlchemy
Alembic
Pydantic
SQLite
```

### Storage

```text
Managed Local Storage
```

### AI

第一版：

```text
OpenAI-compatible unified provider
```

架构：

```text
Route
↓
AIService
↓
AIProvider
↓
OpenAICompatibleProvider
```

业务代码不得散落：

```text
if provider == OpenAI
if provider == DeepSeek
...
```

---

## 2.4 已知精确版本

以下版本在对话/阶段报告中有明确记录：

| 依赖 / 环境 | 已知精确版本 | 说明 |
|---|---:|---|
| Python | `3.12.11` | 早期环境审计明确记录 |
| lucide-react | `0.468.0` | UI Foundation 资源审计明确记录 |
| Pillow | `12.3.0` | Phase 3 引入，图片 metadata / thumbnail |
| PyAV | `18.1.0` | Phase 3 引入，视频解析 / 首帧 |

以下当前精确版本**没有在本对话中逐字保存**：

```text
React
React DOM
Vite
TypeScript
Tailwind CSS
React Router
TanStack Query
Zod

FastAPI
SQLAlchemy
Alembic
Pydantic
```

新 AI 接手第一轮必须直接读取：

```text
D:\GitHub_kyandi-i\AI_Web\frontend\package.json
lockfile

backend\pyproject.toml
或当前实际 dependency config
```

输出实际版本。

**禁止根据当前网上最新版、模型记忆或旧文档猜版本号。**

---

## 2.5 运行环境

当前环境：

```text
Windows 11

Local Development

Browser UI

Local FastAPI Backend

SQLite

Managed Local Storage

非 Docker 强依赖
非 CI-only
非容器优先
```

实际仓库：

```text
D:\GitHub_kyandi-i\AI_Web
```

注意，曾经错误写成：

```text
D:\GitHub\_kyandi-i\AI_Web
```

这是错误路径。

正确：

```text
D:\GitHub_kyandi-i\AI_Web
```

已知端口：

```text
完整应用 / FastAPI:
http://127.0.0.1:8765

Vite Development:
http://127.0.0.1:5173
```

---

## 2.6 启动命令与测试命令

### 已确定 Alembic 验证模式

隔离数据库：

```powershell
alembic upgrade head
alembic downgrade
alembic upgrade head
alembic check
alembic current
```

生产数据库：

```text
只允许 upgrade
```

禁止：

```text
production downgrade
```

### 当前正式 Frontend / Backend 启动与测试命令

本次对话没有逐字保存当前：

```text
frontend startup command
backend startup command

frontend lint command
frontend build command

backend pytest command
browser production command
browser development command
Ruff command
```

因此新 AI **不得猜**：

```powershell
npm run dev
pnpm dev
uv run ...
pytest ...
```

接手后必须读取：

```text
README.md
frontend/package.json
lockfile
backend dependency config
browser test scripts
docs/PHASE_9_STATUS.md
```

恢复当前仓库的精确命令。

这是交接中明确的“需现场恢复事实”，不是允许自行选择新命令。

---

## 2.7 Production Workspace

唯一 authoritative production Workspace：

```text
D:\AI-Video-Workspace
```

真实 DB：

```text
D:\AI-Video-Workspace\data\workspace.db
```

Workspace 概念结构：

```text
D:\AI-Video-Workspace\
├── data\
│   └── workspace.db
├── storage\
│   ├── assets\
│   ├── thumbnails\
│   └── temp\
├── exports\
└── backups\
```

实际目录以代码现状为准。

数据库正式 Asset 路径必须使用 Workspace-relative path，例如：

```text
storage/assets/5b/<uuid>.png
```

禁止把：

```text
D:\Downloads\character.png
```

这种原始绝对路径作为正式 Asset storage path。

---

## 2.8 Bootstrap Config

当前共享 Bootstrap Config：

```text
D:\AI-Video-Workspace-Config\config.json
```

Current User 环境变量：

```text
AVW_BOOTSTRAP_CONFIG_PATH
```

必须指向：

```text
D:\AI-Video-Workspace-Config\config.json
```

概念内容：

```json
{
  "workspace_root": "D:\\AI-Video-Workspace"
}
```

目标解析：

```text
Normal Windows
        │
        ├─ AVW_BOOTSTRAP_CONFIG_PATH
        │
Codex   │
        ↓
D:\AI-Video-Workspace-Config\config.json
        ↓
D:\AI-Video-Workspace
        ↓
D:\AI-Video-Workspace\data\workspace.db
```

`initialize_workspace()`：

```text
不再自动 bootstrap.save(fallback)
```

只有显式用户动作：

```text
Settings
→ set_workspace_root()

PUT /api/settings/workspace
```

才能持久化 Bootstrap Config。

禁止恢复旧行为：

```text
config missing
→ fallback C
→ bootstrap.save(C)
```

---

## 2.9 C 盘空 Workspace

仍可能存在：

```text
C:\Users\Lenovo\AI-Video-Workspace
```

历史诊断：

```text
0 business rows
无独有真实数据
属于 fallback 后新建的空 Workspace
Safe to delete
```

但用户没有授权 Agent 删除。

因此：

```text
禁止自动删除
禁止 C → D copy
禁止 merge
禁止用 C DB 覆盖 D DB
```

---

## 2.10 Production 数据安全铁约束

真实 DB：

```text
D:\AI-Video-Workspace\data\workspace.db
```

绝对禁止：

```text
alembic downgrade production

drop database
drop table

reset
recreate

SQL DELETE 清生产数据

测试数据覆盖生产数据
```

每个需要修改真实 schema 的新 Phase：

```text
1. 所有自动化通过
2. Production hashes before/after 一致
3. 创建真实 DB backup
4. SHA-256 source == backup
5. 只执行 alembic upgrade head
6. 验证 revision
7. integrity_check
8. foreign_key_check
9. 验证旧业务数据
```

---

## 2.11 自动化测试隔离

所有：

```text
Backend Tests
Browser Tests
Migration Tests
Fixtures
```

必须使用隔离：

```text
Bootstrap Config
Workspace Root
Database
Assets
Thumbnails
```

不能因为系统有：

```text
AVW_BOOTSTRAP_CONFIG_PATH
```

就继承真实 production Workspace。

标准安全顺序：

```text
1. 成功读取 production hash baseline

2. 确认测试 Workspace 隔离

3. 运行自动化

4. 再读取 production hashes

5. before == after
```

如果 baseline 获取失败：

```text
STOP
```

不能像 Phase 7 第一轮那样继续启动测试。

如果测试后 production hash 改变：

```text
STOP
```

---

## 2.12 架构硬约束

业务：

```text
Route
↓
Service
↓
Repository
```

Storage：

```text
StorageService
↕
StorageProvider
```

AI：

```text
AIService
↕
AIProvider
```

Asset：

```text
Asset
↕
ProjectAssetLink
ShotAssetLink
CharacterAssetLink
CharacterStateAssetLink
Storyboard
future VideoResult
```

禁止未经确认：

```text
Route 直接 SQL

SQLite → PostgreSQL

Redis
Celery
Event Bus
CQRS
微服务

Docker 强制化

Next.js 替换现有前端

Electron/Tauri 作为当前主形态

大型 binary 写 SQLite BLOB

大型 Base64 放 API JSON
```

---

## 2.13 ID 与删除

核心实体：

```text
UUID
```

默认删除：

```text
Soft Delete
deleted_at
```

流程：

```text
Delete
→ Soft Delete
→ Restore
```

永久删除：

```text
必须再次明确确认
```

Asset 被有效业务引用：

```text
ASSET_IN_USE
```

---

## 2.14 UI 风格

固定：

```text
Premium Black Workspace
Professional
Compact
High information density
Production Tool

Dark default
Light supported

Cyan / Green Accent
```

Dark token：

```text
Background  #111517
Panel       #191F23
Card        #20272C
Accent      #53D9B0
```

Light token：

```text
Background  #F2F5F6
Panel       #FFFFFF
Card        #F7F9FA
Accent      #087B61
```

禁止：

```text
Marketing Landing Page
Huge Hero
巨量留白
紫色主 Accent
Gaming Neon

Coming Soon / Phase X
作为正式产品内容
```

---

## 2.15 图标约束

只使用：

```text
lucide-react
```

禁止：

```text
react-icons
FontAwesome
Material Icons
Heroicons
Icon CDN
Remote Icon API
```

Phase 9 已经发生过 Playwright：

```text
getByRole("img")
```

把 Lucide SVG 一起识别为 img-like accessible element 的问题。

以后 Browser test 不要使用模糊：

```text
getByRole("img")
.first()
nth(0)
```

来掩盖歧义。

优先：

```text
meaningful accessible name
scoped locator
exact role + name
```

---

## 2.16 用户协作硬规则

用户明确要求：

> 任何存在疑问、歧义、缺失需求，或者会影响架构、数据模型、功能边界、交互逻辑、后续扩展的选择，都必须先确认，不能 Agent 自己补需求。

禁止：

```text
自行改变数据模型

自行换技术栈

自行扩大当前 Phase

自行提前实现下一 Phase

自行增加“以后可能需要”的功能

自行做存在争议的核心 UX 决策
```

每个 Phase：

```text
实现
→ 测试
→ migration regression
→ production safety
→ 文档
→ commit
→ Phase-owned git clean
→ 报告
→ STOP
→ 等用户确认下一 Phase
```

不得自动连续进入下一 Phase。

---

## 2.17 Failure-stop Rule

项目严格使用：

```text
Failure-stop
```

出现：

```text
existing regression fail

pytest collection fail

browser regression fail

migration fail

production hash change

production backup hash mismatch

production data anomaly

secret leak

phase boundary violation
```

立即：

```text
STOP
```

禁止：

```text
跳过失败测试

删除 assertion

修改 expected 掩盖生产回归

process.exit(0) 假装正常结束

hard reset 用户文件

直接 SQL 修 Production
```

已多次按此规则正确停止并恢复。

---

# 3. 已被否决的方案及原因

## 3.1 纯 IndexedDB

否决：

```text
React + IndexedDB only
```

最终：

```text
React Web
+
FastAPI
+
SQLite
+
Managed Local File Storage
```

原因：

```text
4K 图片 / 视频量大

浏览器容量与自动清理不适合长期生产资料

备份和迁移较差

未来 PostgreSQL + object storage 更自然
```

---

## 3.2 Asset 只记录用户绝对路径

否决：

```text
D:\项目\SPF\人物.png
```

直接作为正式 Asset path。

原因：

```text
移动原文件后失效
备份困难
导出困难
未来云化困难
```

最终：

```text
Import
→ UUID
→ Copy into Managed Storage
→ Workspace-relative path
```

---

## 3.3 Global Asset / Project Asset 两套实体

否决。

最终：

```text
Asset
↕
ProjectAssetLink
```

和：

```text
Asset
↕
ShotAssetLink
CharacterAssetLink
CharacterStateAssetLink
Storyboard
```

原因：

```text
同一真实素材应该复用
不能复制真实文件
长期素材库应统一
```

---

## 3.4 AssetType 使用 CHARACTER_IMAGE / SCENE_IMAGE / PROP_IMAGE

否决。

当前：

```text
IMAGE
VIDEO
STORYBOARD_6GRID
OTHER
```

原因：

```text
人物 / 场景 / 道具是业务用途
不是底层文件类型

同一 Asset 可用于多个业务角色
```

---

## 3.5 删除 ScriptNode，只保留 Script → Scene → Shot

否决。

当前：

```text
Script
└── ScriptNode(type=SCENE)
    └── Scene
        └── Shot
```

UI：

```text
Script → Scene → Shot
```

未来：

```text
Script
└── Chapter
    └── Sequence
        └── Scene
```

不需要重构现有 Scene。

---

## 3.6 等功能全部结束再整改 UI

否决。

原因：

旧 UI：

```text
营销式 SaaS Dashboard
```

目标：

```text
专业生产工作台
```

因此已完成：

```text
Phase 1.5 UI Foundation
Phase 2.5 UX Fix
```

---

## 3.7 Dark Mode only

否决。

当前：

```text
Dark default
+
Light supported
+
Theme persistence
```

---

## 3.8 紫色 / 蓝紫 Accent

否决。

用户选择：

```text
黑色高级感
+
青绿色 Accent
```

---

## 3.9 动态图标 API / CDN

否决。

原因：

```text
破坏 Local-first
依赖联网
延迟
外部服务故障风险
没有必要
```

---

## 3.10 多图标库并存

否决。

继续：

```text
lucide-react only
```

---

## 3.11 当前就做 Electron / Tauri

暂不采用。

当前：

```text
Local-first Web Application
Browser UI
Local FastAPI
```

Desktop wrapper 仅未来可能性。

---

## 3.12 MVP 直接接图片 / 视频生成

否决为当前主线。

当前：

```text
需求
→ Prompt
→ 复制
→ 外部生成平台
→ 导回结果
```

未来可以：

```text
GenerationProvider
GenerationJob
```

但当前 Phase 10 仍不能提前做。

---

## 3.13 Redis / Celery / CQRS / Event Bus / 微服务

否决。

原因：

```text
个人本地工具
当前规模不需要
增加维护成本
拖慢 MVP
```

---

## 3.14 Character = 图片

否决。

当前：

```text
Character
= 角色身份

CharacterState
= 某阶段具体视觉状态

Asset
= 实际媒体素材
```

---

## 3.15 给 Character 固定大量人物属性

未采用：

```text
age
gender
height
race
hair_color
eye_color
...
```

原因：

```text
AI 视频角色描述高度自由
过早结构化会限制生产需求
```

当前：

```text
name
description
notes
```

为主。

---

## 3.16 Shot 只保留 creative_requirement 大文本

不再作为主输入。

Legacy：

```text
creative_requirement
```

继续保留。

Phase 5 新增：

```text
main_action
key_constraints
negative_constraints
free_notes
```

原因：

```text
为 AI Prompt 提供稳定结构化生产上下文
```

---

## 3.17 Shot Workspace 复杂 Autosave

否决。

当前：

```text
explicit Save
dirty state
leave protection
```

原因：

```text
生产场景长文本多
明确保存状态更可靠
```

---

## 3.18 PromptTemplate 使用 Jinja / Handlebars / 可执行模板语言

否决。

当前：

```text
{{placeholder}}
+
固定白名单
+
deterministic text substitution
```

禁止：

```text
eval
if
loop
macro
function
attribute traversal
arbitrary expression
```

---

## 3.19 PromptTemplate 拆 system_prompt / user_prompt

否决。

当前 Template：

```text
template_content
```

原因：

```text
模板层保持 provider-neutral
AIService 决定 request packaging
```

---

## 3.20 PromptTemplate 继承 / Override

否决。

当前：

```text
GLOBAL
PROJECT
```

两套独立模板。

仅：

```text
Copy Global → Project
```

复制后独立。

---

## 3.21 selected PromptTemplate 永久绑 Shot

否决。

没有：

```text
shot.prompt_template_id
ShotPromptTemplateLink
```

实际事实记录在：

```text
PromptRecord.template_id
```

---

## 3.22 Workspace Root 源码硬编码到 D

否决。

禁止：

```python
workspace_root = Path("D:/AI-Video-Workspace")
```

D 是当前机器配置，不是产品源码默认值。

正确：

```text
Bootstrap Config
+
AVW_BOOTSTRAP_CONFIG_PATH
```

---

## 3.23 依赖两份 `%APPDATA%` Bootstrap Config

已踩坑并否决。

曾出现：

```text
Normal Windows %APPDATA%
→ C:\Users\Lenovo\AppData\Roaming

Codex redirected %APPDATA%
→ D:\WpSystem\...\LocalCache\Roaming
```

导致 config 分叉。

最终：

```text
AVW_BOOTSTRAP_CONFIG_PATH
→ D:\AI-Video-Workspace-Config\config.json
```

---

## 3.24 Missing config 时 fallback + 自动 save

否决并修复。

旧行为：

```text
config missing
→ fallback ~/AI-Video-Workspace
→ initialize
→ bootstrap.save(root)
```

新行为：

```text
config missing
→ 可使用 default in-memory / fallback
→ initialize
→ 不自动写 config
```

只有：

```text
set_workspace_root()
```

才保存。

---

## 3.25 Browser test 挂起时 `process.exit(0)`

否决。

Phase 6 曾出现：

```text
测试全部 assertion PASS
但 sandbox 无法正常回收进程
```

最终定位：

```text
sandbox process-reaping permission issue
```

在获准环境：

```text
exit code 0
```

禁止：

```text
process.exit(0)
```

掩盖 teardown / 环境问题。

---

## 3.26 Phase 7 为测试目录加入 `backend/tests/__init__.py`

尝试后撤销。

问题：

```text
backend/tests/__init__.py
```

改变 pytest module resolution。

导致：

```text
backend/tests/test_shot_workspace.py
```

无法按旧方式导入：

```text
test_characters
```

完整 backend collection：

```text
FAIL
exit 2
```

最终：

```text
移除 backend/tests/__init__.py

共享 Fake Provider / E2E 支持迁移到：
backend/test_support
```

保留旧测试组织、导入和断言。

---

## 3.27 Phase 8 为 Clipboard CRLF/LF 修改业务文本

未采用。

Windows Clipboard：

```text
LF
→ CRLF
```

浏览器测试最初：

```text
Expected LF
Received CRLF
```

确认逻辑文本完全一致后：

```text
只在测试比较时规范：
\r\n → \n
```

没有修改：

```text
Prompt 正文
数据库持久化
Copy 业务逻辑
```

禁止：

```text
trim()
collapse whitespace
```

掩盖真实格式问题。

---

## 3.28 Storyboard 删除时自动回收 ShotAssetLink / ProjectAssetLink

否决。

当前冻结：

```text
Storyboard relation

ProjectAssetLink

ShotAssetLink
```

是独立关系。

Storyboard import 只是：

```text
一个 convenience transaction
```

一次建立多种关系。

后续没有 ownership 生命周期。

---

## 3.29 Storyboard 只关联 Asset，不自动建立 Project/Shot Link

未采用。

旧产品规格要求 Storyboard import：

```text
Link Project
Link Shot
```

因此当前实现：

```text
import Asset
→ ensure ProjectAssetLink
→ ensure ShotAssetLink
→ create Storyboard
```

但后续关系独立维护。

---

## 3.30 为 Storyboard 给 ShotAssetLink 加 source / owner / purpose

否决。

不新增：

```text
ShotAssetLink.source
ShotAssetLink.owner
ShotAssetLink.purpose
StoryboardOwnedAssetLink
```

原因：

```text
同一 Asset 可手工绑定
也可被多个 Storyboard 版本复用

无法简单定义“谁拥有 Link”

会引入不必要引用计数/ownership 系统
```

---

## 3.31 Phase 9 Browser 用 `.first()` / `nth(0)` 绕过 Lucide locator

否决。

实际修复采用：

```ts
v1.getByRole("img", {
  name: "Storyboard V1 thumbnail",
  exact: true,
})
```

和：

```ts
detail.getByRole("img", {
  name: "Storyboard V1 original",
  exact: true,
})
```

原因：

```text
测试必须表达真正用户目标
而不是“页面第一个 img-like element”
```

---

## 3.32 Phase 9 修改旧 Asset 删除文案

回归后撤销。

Phase 0–8 兼容文案：

```text
请先解除绑定
```

Phase 9 曾改成：

```text
请先解除引用
```

production Browser regression：

```text
Expected: 请先解除绑定
Received: 请先解除引用
```

最终：

```text
恢复 请先解除绑定
```

同时保留：

```text
Storyboard reference count
ASSET_IN_USE
Asset type change protection
```

没有修改旧测试 expected。

---

# 4. 当前具体状态

## 4.1 Phase 总览

```text
Phase 0      ✅ Project Initialization

Phase 1      ✅ Database / Alembic / Workspace / Storage

Phase 1.5    ✅ UI Foundation

Phase 2      ✅ Project / Script / Scene / Shot

Phase 2.5    ✅ UX Fix

Phase 3      ✅ Asset Library

Phase 3.1    ✅ Workspace Migration

Phase 4      ✅ Character / CharacterState

Phase 5      ✅ Shot Workspace

Phase 5.1    ✅ Workspace Root Recovery & Hardening

Phase 6      ✅ Prompt Template

Phase 7      ✅ AI Prompt Generation

Phase 8      ✅ Prompt Versioning

Phase 9      ✅ Storyboard Workflow

Phase 10     ⬜ Video Result

Phase 11     ⬜ Export / Recycle Bin / UX
```

当前没有进行中的未提交 Phase。

---

## 4.2 已知 Commit

### Phase 1.5

```text
bf2113b
UI Foundation
```

### Phase 2

```text
71d25ba
Project / Script / Scene / Shot
```

### Phase 2.5

```text
commit hash 未在当前对话逐字记录
```

禁止猜。

从 Git 历史恢复。

### Phase 3

```text
50cd7c9
feat: complete Phase 3 unified asset library
```

### Phase 3.1

```text
6456839
fix: support safe workspace migration
```

### Phase 4

```text
627ab09
feat: add character and character state management
```

### Phase 5

```text
f1128b9
feat: add shot production workspace
```

### Phase 5.1

```text
79a3589
fix: harden workspace bootstrap configuration
```

### Phase 6

```text
14ecab0
feat: add prompt template management
```

完整 hash 可从 Git 获取。

### Phase 7

```text
15b9607e0ee785595792c93d9ba4774aae71620d
feat: add AI prompt generation
```

### Phase 8

```text
ef9b8a9732678a427d33a1db5ee61a6f9ae5bcea
feat: add prompt versioning
```

### Phase 9

```text
baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2
feat: add storyboard workflow
```

当前 HEAD 应为：

```text
baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2
```

Phase 10 开工前必须再次确认。

---

## 4.3 当前 Migration

明确：

```text
0004_characters
0005_shot_workspace
0006_prompt_templates
0007_prompt_generation
0008_prompt_versioning
0009_storyboards
```

当前 production：

```text
0009_storyboards
```

`0009_storyboards`：

```text
down revision:
0008_prompt_versioning
```

更早 migration ID 若需要完整链：

```text
直接读取 backend/app/migrations/versions/
```

不要猜。

---

## 4.4 Phase 6 — Prompt Template ✅

Commit：

```text
14ecab0
feat: add prompt template management
```

最终：

```text
Backend                 201/201 PASS
Phase 6 Browser             7/7 PASS
Browser production         43/43 PASS
Browser development        45/45 PASS
lint/build/Ruff            PASS
isolated Alembic           PASS
```

Production：

```text
0006_prompt_templates
```

阶段完成时自动化：

```text
6/6 protected files hashes unchanged
```

指定两个短模板：

```text
create
edit
preview
refresh
restart
```

全部通过。

---

## 4.5 Phase 7 — AI Prompt Generation ✅

Commit：

```text
15b9607e0ee785595792c93d9ba4774aae71620d
feat: add AI prompt generation
```

实现：

```text
AI Provider Settings

AIProvider Protocol
→ OpenAICompatibleProvider

AIService

Shot Context Assembly

复用 Phase 6 Renderer

Prompt Generation

Prompt generation persistence

Settings API

Shot preview / generate / latest

Prompt detail

Shot Workspace:
Rendered Input
Generate
Generating
Error/Retry
Result
Copy
```

Prompt generation record Phase 7 语义字段至少包括：

```text
UUID

Shot FK
PromptTemplate FK

template snapshot

prompt type

context snapshot

rendered_input

input_hash

generated_content

provider
model

created_at
updated_at
```

Phase 7 没有：

```text
version
selected/final
Prompt history UI
Storyboard
Video Result
```

这些由后续 Phase 扩展。

最终：

```text
Backend full              253/253 PASS
Phase 7 Backend             52/52 PASS
Phase 7 Browser              7/7 PASS
Browser production          50/50 PASS
Browser development         52/52 PASS

Frontend lint/build         PASS
Ruff check/format           PASS

isolated Alembic            PASS
```

Production：

```text
0007_prompt_generation
```

Phase 7 backup：

```text
D:\AI-Video-Workspace\backups\
before-phase7-20260925-154932.db
```

source / backup SHA-256：

```text
ba3a55ad8ea6e3881cd3b40261c0923e614902e01527faea33bc66851525f44c
```

旧业务：

```text
17 张旧业务表逐行不变

integrity_check = ok
foreign_key_check = 0
```

S13 Fake acceptance：

```text
PASS
```

使用真实 SPF 数据的隔离副本。

没有向 production 写 Fake Prompt。

真实外部 AI：

```text
PENDING USER EXPLICIT APPROVAL
```

---

## 4.6 Phase 8 — Prompt Versioning ✅

Commit：

```text
ef9b8a9732678a427d33a1db5ee61a6f9ae5bcea
feat: add prompt versioning
```

核心语义：

### Manual Edit

```text
只写 edited_content
```

保持：

```text
generated_content
template snapshot
context snapshot
rendered_input
input_hash
provider/model
```

不变。

有效显示：

```text
edited_content ?? generated_content
```

### Regenerate

```text
创建新的 PromptRecord
创建新的 version
不覆盖旧记录
```

### Version

```text
同 Shot + Prompt Type

V1
V2
V3
...
```

数据库：

```text
positive integer
```

### Selected

```text
same Shot
+
same Prompt Type
→ at most one Selected
```

由：

```text
Service transaction
+
DB unique index
```

共同保护。

版本历史、编辑、复制、Regenerate、Selected、重启持久化均完成。

最终：

```text
Phase 8 Backend             33/33 PASS
Backend full               286/286 PASS

Phase 8 Browser              6/6 PASS
Browser production          56/56 PASS
Browser development         58/58 PASS

lint/build                  PASS
Ruff                        PASS

isolated Alembic            PASS
populated migration         PASS
```

Production：

```text
0008_prompt_versioning
```

Phase 8 backup：

```text
D:\AI-Video-Workspace\backups\
before-phase8-20260929-231526.db
```

source / backup SHA-256：

```text
f1ccc50edb6457e2884dae36eb8745eab025c39616df7afab7c626980f582b36
```

Production：

```text
18 张旧表数据不变
integrity_check = ok
foreign_key_check = 0
```

S13 isolated Fake versioning：

```text
PASS
```

Production 没有 Fake Prompt。

---

## 4.7 Phase 9 — Storyboard Workflow ✅

Commit：

```text
baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2
feat: add storyboard workflow
```

Migration：

```text
0009_storyboards
```

Storyboard final schema：

```text
id UUID

shot_id FK

asset_id FK

source_prompt_record_id FK nullable

storyboard_type = GRID_6

version positive INTEGER

is_selected BOOLEAN

notes nullable

created_at
updated_at
deleted_at
```

约束：

```text
Shot + version UNIQUE

active Selected:
same Shot
→ at most one
```

版本：

```text
per Shot
V1, V2, V3...

soft-deleted version 不复用
```

Selected：

```text
first Storyboard
→ selected

new Storyboard
→ selected
→ previous selected cleared

delete selected
→ no automatic fallback
```

Prompt relation：

```text
source_prompt_record_id nullable

非空：
PromptRecord.shot_id == Storyboard.shot_id
```

source 保存的是：

```text
具体 PromptRecord ID
```

不是：

```text
当前 selected Prompt
PromptTemplate
Prompt 文本复制
```

### Storyboard / Asset

媒体唯一事实：

```text
Storyboard.asset_id
→ Asset
```

Storyboard 不存：

```text
binary
base64
file path
thumbnail path
```

真实文件继续由 Asset 管。

Storyboard Asset 必须：

```text
asset_type = STORYBOARD_6GRID
```

### Storyboard import

同一事务：

```text
Managed Storage Asset

→ ensure ProjectAssetLink

→ ensure ShotAssetLink

→ create Storyboard
```

已有 Link：

```text
reuse
```

不重复。

### 独立生命周期

创建后：

```text
Storyboard relation

ProjectAssetLink

ShotAssetLink
```

独立维护。

删除 Storyboard：

```text
保留 Asset
保留 ProjectAssetLink
保留 ShotAssetLink
```

解绑 Shot Reference：

```text
删除 ShotAssetLink

Storyboard 继续存在
Asset 继续存在
thumbnail/original 继续可用
```

同一 Asset 可：

```text
Storyboard V1
Storyboard V2
ProjectAssetLink
ShotAssetLink
其他合法业务关系
```

不跟踪谁“拥有” Link。

### Asset protection

active Storyboard：

```text
delete Asset
→ ASSET_IN_USE
```

兼容用户文案：

```text
请先解除绑定
```

active Storyboard 期间：

```text
禁止把 Asset 类型改离 STORYBOARD_6GRID
```

### API

已实现：

```http
GET  /api/shots/{shot_id}/storyboards
POST /api/shots/{shot_id}/storyboards

POST /api/shots/{shot_id}/storyboards/import

GET  /api/storyboards/{id}

POST /api/storyboards/{id}/select

DELETE /api/storyboards/{id}

POST /api/storyboards/{id}/restore
```

### UI

Shot Workspace 已包含：

```text
Storyboard section

Import Storyboard

Use Existing Asset

History

V1/V2/...

Selected

View thumbnail

View original

Select

Delete
```

### Browser accessible names

最终使用：

```text
Storyboard V1 thumbnail
Storyboard V1 original
```

测试定位必须保持精确。

最终：

```text
Phase 9 Backend             28/28 PASS
Backend full               314/314 PASS

Phase 9 Browser              6/6 PASS
Browser production          62/62 PASS
Browser development         64/64 PASS

Frontend lint/build         PASS
Ruff check                  PASS
Ruff format --check         PASS
97 files

isolated Alembic CLI        PASS
populated migration         PASS
```

独立 Alembic：

```text
upgrade
downgrade
upgrade
check
current
→ PASS

head = 0009_storyboards
```

Populated migration：

```text
0008
→ 0009
→ 0008
→ 0009
PASS
```

Phase 0–8 数据保持。

Production backup：

```text
D:\AI-Video-Workspace\backups\
before-phase9-20260930-192304.db
```

source / backup SHA-256：

```text
6bcbefa34fd56937a7b315a76a4613bb73b64a73197a23d05b9070d7fc1778c5
```

生产升级后 DB hash：

```text
54da9298e132c8857763ba8761073111895167f329bf6b187ad179145c0df64c
```

Production revision：

```text
0009_storyboards
```

Integrity：

```text
integrity_check = ok
foreign_key_check = 0
```

Phase 0–8：

```text
18 张表逐列逐行保持
```

S13 isolated Storyboard acceptance：

```text
PASS
```

包括：

```text
V1
V2
Selected switch
refresh
new backend process restart
source Prompt persistence
thumbnail
original
```

Reference unlink acceptance：

```text
PASS
```

Asset delete acceptance：

```text
PASS
```

Production Fake Storyboard：

```text
NO
```

---

## 4.8 当前 Production 状态

Production Workspace：

```text
D:\AI-Video-Workspace
```

Production DB：

```text
D:\AI-Video-Workspace\data\workspace.db
```

Current revision：

```text
0009_storyboards
```

Phase 9 migration 后已知 DB hash：

```text
54da9298e132c8857763ba8761073111895167f329bf6b187ad179145c0df64c
```

注意：

这个 hash 只是 Phase 9 完成时的事实。

如果用户之后正常使用应用写入真实数据：

```text
DB hash 变化是正常的
```

新 Agent 不得因为它与这里不同就直接认定 corruption。

应该先：

```text
确认是否有用户正常业务写入
```

---

## 4.9 当前 SPF 真实业务数据

Phase 9 完成时确认：

```text
Project:
SPF 屏障设施培训视频
```

S13：

```text
shot_code:
S13

title:
风淋

duration_seconds:
10

scene:
风淋室
```

四项需求：

```text
main_action:
人物从二更进入风淋室，入口门关闭后完成风淋，风淋结束后出口门开启，人物进入核心区。

key_constraints:
两扇门严格互锁。人物保持自然连续步态。人物不得正对镜头。

negative_constraints:
禁止两门同时开启。禁止黄色脚套呈鞋形。禁止设备位置漂移。

free_notes:
以场景固定约束和已绑定角色状态为准。
```

Character：

```text
SPF培训女员工
```

CharacterState：

```text
基础状态
发帽+口罩
黄色 PPE
黄色 PPE+第一层手套
黄色 PPE+双层手套
退出状态
```

S13：

```text
→ SPF培训女员工
→ 黄色 PPE + 双层手套
```

Phase 9 production 验证时：

```text
Prompt history / Selected 实际值：
0 / 0
```

这不是 bug。

不要为了测试向 Production 人工添加 Prompt / Storyboard。

---

## 4.10 当前 Known Limitations

### AI Key

当前：

```text
独立本机配置文件
明文保存
```

安全保证：

```text
GET/PUT 不回显 Key
不进入业务 DB
不进入 Git
不进入普通日志
Project Export 默认不得带出
```

当前阶段不要顺手引入：

```text
DPAPI
Windows Credential Manager
keyring
encryption framework
```

除非用户单独批准安全强化。

---

### AI wait lock

当前：

```text
AI 等待期间持现有 Workspace lock / read transaction
```

暂作为 known limitation。

不要为了 Phase 10 引入：

```text
Celery
Redis
queue worker
event bus
```

---

### Remote retry

远端请求：

```text
不保证 idempotent
```

timeout retry：

```text
可能重复计费
```

不要实现无界自动重试。

---

### Storyboard history

当前：

```text
未分页
```

不阻塞 Phase 10。

---

### Storyboard restore

当前：

```text
后端已有 restore API
前端无完整 restore UX
```

不阻塞 Phase 10。

---

### SQLite

```text
single writer
```

属于当前 Local-first 架构已知限制。

---

### Real external AI

```text
PENDING USER EXPLICIT APPROVAL
```

到目前为止没有调用真实收费 AI。

---

## 4.11 当前 Git 状态

Phase 9-owned：

```text
clean
```

历史上一直保留用户原有：

```text
M HANDOFF.md
```

在 Phase 9 最终报告时旧 HANDOFF hash：

```text
c42d15ff745ea67b90d10a1be80e652151deed57e805259698f424963b763a25
```

**重要：用户现在明确要求生成新的 HANDOFF.md。**

如果用户将本文件保存覆盖仓库中的：

```text
HANDOFF.md
```

那么：

```text
M HANDOFF.md
```

和上述 SHA-256 变化是预期用户动作。

新 AI 不要把“用户保存新版 HANDOFF”误判为 Phase 10 自己造成的未知修改。

但 Phase 10 Agent：

```text
仍不得把 HANDOFF.md 自动 stage / commit
```

除非用户明确要求把交接文档提交进 Git。

---

## 4.12 当前待办 ⬜

### Phase 10 — Video Result

尚未开始。

现有总体规划：

```text
Video Result

V1
V2
V3

notes

is_selected
```

但 **最终数据模型尚未在本次对话中冻结**。

Phase 10 开工前必须先检查：

```text
PROJECT_PLAN.md

docs/PHASE_9_STATUS.md

Storyboard current model

Asset current model

Shot Workspace current UI
```

再确定：

```text
VideoResult ↔ Shot

VideoResult ↔ Asset(VIDEO)

VideoResult ↔ source Storyboard

是否还需要 source PromptRecord

version scope

Selected semantics

import/link lifecycle

delete semantics
```

如果仓库文档没有明确且存在会影响长期模型的歧义：

```text
先问用户
```

不要自己补。

---

# 5. 关键决策记录

## 5.1 产品不是 AI Generator

核心价值：

```text
组织
关联
生产上下文
版本
Prompt workflow
素材
生成结果管理
```

不是：

```text
在 Workspace 内直接生成一切
```

因此 Phase 10：

```text
Video Result 导回
```

不是：

```text
Video Generation API
```

---

## 5.2 Script / Scene

固定：

```text
Script
└── ScriptNode(type=SCENE)
    └── Scene
        └── Shot
```

ScriptNode：

```text
tree
parent
order
future Chapter / Sequence
```

Scene：

```text
business scene data
constraints
description
```

UI 不需要暴露 ScriptNode。

---

## 5.3 Asset 是统一媒体事实

统一：

```text
Asset
```

AssetType：

```text
IMAGE
VIDEO
STORYBOARD_6GRID
OTHER
```

业务实体引用 Asset。

不要让：

```text
Storyboard
VideoResult
Character
```

各自再做一套文件管理。

---

## 5.4 Character / CharacterState

```text
Character
= identity

CharacterState
= concrete visual state

Asset
= media reference
```

Project：

```text
1:N Character
```

Shot：

```text
N:N CharacterState
```

same Shot + same Character：

```text
one active CharacterState
```

---

## 5.5 Shot Context

Phase 5 后：

```text
Scene

CharacterState

Character Assets

CharacterState Assets

Shot Assets

Duration

Main Action

Key Constraints

Negative Constraints

Free Notes
```

构成 Prompt 上下文。

---

## 5.6 PromptTemplate

Scope：

```text
GLOBAL
PROJECT
```

Category：

```text
STORYBOARD_6GRID
VIDEO_GENERATION
CHARACTER_IMAGE
SCENE_IMAGE
IMAGE_REFERENCE
START_END_FRAME
OTHER
```

Placeholder：

```text
{{variable_name}}
```

固定白名单。

---

## 5.7 Placeholder 白名单

```text
{{shot_code}}

{{shot_title}}

{{shot_description}}

{{duration_seconds}}

{{main_action}}

{{key_constraints}}

{{negative_constraints}}

{{free_notes}}

{{scene_name}}

{{scene_description}}

{{scene_fixed_constraints}}

{{scene_negative_constraints}}

{{characters_context}}

{{reference_assets_context}}

{{shot_context}}
```

也接受：

```text
{{ shot_code }}
```

未知 placeholder：

```text
INVALID_TEMPLATE_PLACEHOLDER
```

Preview：

```text
deterministic substitution only
No AI call
```

---

## 5.8 AI Provider

当前只：

```text
OpenAI-compatible
```

Settings：

```text
API Base URL
API Key
Model
```

业务必须通过：

```text
AIService
↓
AIProvider
```

Route 不直接请求外部 AI。

---

## 5.9 Prompt generation fact 不可变

PromptRecord 的原始生成事实：

```text
template snapshot

context snapshot

rendered_input

input_hash

generated_content

provider

model
```

人工 Edit：

```text
不得覆盖这些字段
```

只写：

```text
edited_content
```

---

## 5.10 Prompt Versioning

```text
Regenerate
→ new PromptRecord
→ new version
```

而不是覆盖旧版本。

Manual Edit：

```text
same PromptRecord.edited_content
```

Copy：

```text
edited_content ?? generated_content
```

Selected：

```text
same Shot + Prompt Type
→ at most one
```

---

## 5.11 Retry 与 Regenerate

Retry：

```text
一次失败 generation operation
没有成功 record
再次尝试
```

Regenerate：

```text
已有成功 record
用户主动生成新 version
```

不要混淆。

---

## 5.12 Storyboard 是业务结果实体，不是文件系统

Storyboard：

```text
Shot
+
Asset
+
optional source PromptRecord
+
version
+
selected
```

真实文件：

```text
Asset
```

---

## 5.13 Storyboard source 固定历史来源

```text
Storyboard V1
→ PromptRecord V2
```

即使以后：

```text
Prompt V3 selected
```

Storyboard V1 source 仍是原 V2。

---

## 5.14 Storyboard Asset lifecycle 独立

导入：

```text
Asset
+
ProjectAssetLink
+
ShotAssetLink
+
Storyboard
```

在一个事务中建立。

但：

```text
transactional creation
≠
shared lifecycle ownership
```

之后独立维护。

---

## 5.15 Storyboard Selected

```text
one Shot
→ many Storyboards
→ at most one selected
```

新版本：

```text
auto selected
```

删除 selected：

```text
不自动 fallback
```

---

## 5.16 Storyboard version

```text
Shot
V1
V2
V3
```

软删除：

```text
version number 不复用
```

---

## 5.17 VideoResult 设计应优先复用 Storyboard 成熟模式

Phase 10 尚未冻结 schema。

但设计时应优先检查 Storyboard 已验证模式：

```text
业务结果实体
→ Asset

version positive integer

Selected unique

来源关系固定

新结果创建新 version

删除结果不自动删除 Asset
```

不要无理由另造完全不同的版本系统。

若 Video 特性确实需要不同模型：

```text
先依据文档/用户需求确认
```

---

# 6. 下一步明确指令

# 任务 1 — Phase 10 接手审计与 Scope Freeze

## 在哪里做

```text
D:\GitHub_kyandi-i\AI_Web
```

重点读取：

```text
README.md

DEVELOPMENT_STATUS.md

PROJECT_PLAN.md

docs/PHASE_9_STATUS.md
docs/PHASE_8_STATUS.md

frontend/package.json
backend dependency config

current Storyboard model/service/routes/schema
current Asset model/service
current Shot Workspace frontend
current browser tests

backend/app/migrations/versions/
```

执行：

```powershell
cd D:\GitHub_kyandi-i\AI_Web

git status --short

git log --oneline -10

git show --name-status baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2
git show --stat baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2
```

## 做什么

确认：

```text
HEAD == baab8a2...

working tree 中哪些修改属于用户新版 HANDOFF.md

Production Bootstrap path

Production Workspace

Production DB

DB revision == 0009_storyboards
```

从仓库恢复本交接中未逐字保留的：

```text
当前所有依赖精确版本

正式启动命令

正式测试命令

Phase 7/8 精确 Prompt API

Phase 9 26 个 modified-file 完整清单
```

然后冻结 Phase 10：

```text
IN
OUT
```

必须明确：

```text
VideoResult 是否独立 entity

VideoResult → Shot

VideoResult → Asset(VIDEO)

source Storyboard 是否 required/nullable

是否还保存 source PromptRecord

version scope

Selected 规则

import / existing Asset

delete lifecycle

Asset in-use behavior
```

## 验收标准

能提交一份明确的 Phase 10 scope：

```text
IN Phase 10

OUT of Phase 10
```

且：

```text
没有 Phase 11 Export/Recycling 偷跑

没有 video generation API

没有 GenerationJob

没有审批/协作/时间线
```

任何会影响数据模型且文档无法解决的歧义：

```text
STOP
→ 问用户
```

---

# 任务 2 — 实现 VideoResult Domain / Migration / Backend

## 在哪里做

以真实仓库结构为准，概念上：

```text
backend/app/models/
backend/app/repositories/
backend/app/services/
backend/app/api/
backend/app/schemas/
backend/app/migrations/versions/
```

## 做什么

在 Phase 10 scope 冻结后：

```text
创建 0010_* migration

新增 VideoResult entity

复用 Asset(VIDEO)

实现 version

实现 Selected

实现 source relation

实现 import existing Video Asset

实现 Storage import

实现 delete / restore（若 scope）
```

核心原则：

```text
VideoResult 不存 binary/base64/file path

媒体事实继续由 Asset 管
```

优先复用 Storyboard 已验证模式：

```text
version uniqueness

active Selected uniqueness

transaction

Asset in-use

independent Asset link lifecycle
```

但具体 relation 必须以冻结后的 Phase 10 scope 为准。

## 验收标准

Backend tests 至少验证：

```text
create V1

create V2

version unique

Selected unique

switch Selected

source relation valid

wrong source rejected

VIDEO Asset accepted

non-VIDEO Asset rejected

Asset in-use

transaction rollback

migration upgrade/downgrade/populated migration
```

所有 Phase 0–9 backend regression 继续 PASS。

---

# 任务 3 — Shot Workspace Video Result UI / API

## 在哪里做

当前：

```text
Shot Workspace frontend
VideoResult routes/service
Asset upload/reuse UI
```

## 做什么

Phase 10 scope 确认后增加：

```text
Video Result section

Current Selected

V1/V2/V3 history

Import Video

Use Existing Video Asset

Preview / playback

notes

Select

Delete / Restore（若 scope）
```

媒体预览：

```text
使用 Asset file endpoint
```

不要：

```text
base64 video

全部历史 video autoplay

列表加载大型二进制
```

保持：

```text
Premium Black Workspace
compact
high information density
Dark/Light
lucide-react only
```

## 验收标准

隔离 Workspace 中：

```text
Shot
→ import Video V1
→ Selected

→ import V2
→ V1 remains
→ V2 Selected

→ switch V1
→ only V1 Selected

→ refresh
→ restart backend
→ history/selection persists
```

所有旧 Storyboard / Prompt UI browser tests继续 PASS。

---

# 任务 4 — Phase 10 完整安全回归

## 在哪里做

全部自动化必须使用隔离 Workspace。

Production：

```text
D:\AI-Video-Workspace
```

只用于 hash、backup 和最终 upgrade。

## 做什么

顺序：

```text
1. production hash baseline

2. Phase 10 backend tests

3. backend full

4. frontend lint

5. frontend build

6. Ruff check

7. Ruff format --check

8. Phase 10 browser

9. Browser production full

10. Browser development full

11. isolated Alembic:
    upgrade
    downgrade
    upgrade
    check
    current

12. populated migration

13. production hash after

14. compare
```

然后使用 SPF production 的隔离副本做 VideoResult 业务验收。

不要向 production 写 fake Video Result。

## 验收标准

```text
所有命令 exit 0

所有测试 PASS

production before == after

fake production records = NO
```

---

# 任务 5 — Production Migration / Docs / Commit

## 在哪里做

Production DB：

```text
D:\AI-Video-Workspace\data\workspace.db
```

Docs：

```text
README.md

DEVELOPMENT_STATUS.md

PROJECT_PLAN.md

docs/PHASE_10_STATUS.md
```

## 做什么

所有自动化完全 PASS 后：

```text
backup production DB

SHA-256 source == backup

alembic upgrade head only

verify revision

integrity_check

foreign_key_check

verify SPF old data

verify Prompt/Storyboard history
```

然后文档更新。

Git 检查：

```powershell
git status --short
git diff
git diff --cached
```

禁止提交：

```text
HANDOFF.md
```

除非用户明确要求。

禁止提交：

```text
API Key
ai-provider.json
workspace.db
backup DB
test DB
fixture media
test-results
trace
dist
```

## 验收标准

```text
Phase 10 COMPLETE

Phase 11 NOT STARTED

Phase 10-owned working tree clean

user-owned HANDOFF.md preserved
```

并有单一清晰 commit。

---

# 7. 原始产物附录

# 7.1 Core Domain

```text
Workspace
│
├── Project
│   │
│   ├── Script
│   │   └── ScriptNode
│   │       └── Scene
│   │           └── Shot
│   │
│   ├── Character
│   │   └── CharacterState
│   │
│   ├── ProjectAssetLink
│   │
│   └── Project Prompt Templates
│
├── Asset
│
├── Tag
│
├── PromptTemplate
│
├── PromptRecord
│
├── Storyboard
│
└── future VideoResult
```

Shot：

```text
Shot
├── Scene Context
├── Shot Assets
├── CharacterStates
│   ├── Character Assets
│   └── CharacterState Assets
├── Structured Requirements
├── PromptRecords
├── Storyboards
└── future VideoResults
```

---

# 7.2 Project

已知核心字段：

```text
id UUID

name

description

status

created_at
updated_at
deleted_at
```

Status：

```text
DRAFT
ACTIVE
PAUSED
COMPLETED
ARCHIVED
```

---

# 7.3 Script

```text
id UUID

project_id

name

description

created_at
updated_at
deleted_at
```

---

# 7.4 ScriptNode

```text
id UUID

script_id

parent_id nullable

node_type

title

description

order_index

created_at
updated_at
deleted_at
```

node_type：

```text
CHAPTER
SEQUENCE
SCENE
OTHER
```

当前 UI 主要：

```text
SCENE
```

---

# 7.5 Scene

```text
id UUID

project_id

script_node_id UNIQUE

name

description

fixed_constraints

negative_constraints

created_at
updated_at
deleted_at
```

约束：

```text
Scene.script_node.node_type == SCENE

Scene.Project
==
ScriptNode.Script.Project
```

Scene create 必须同事务：

```text
check Project

check Script belongs Project

calculate order

create ScriptNode(type=SCENE)

create Scene

commit
```

失败：

```text
rollback
```

不得产生 orphan ScriptNode。

---

# 7.6 Shot

当前至少：

```text
id UUID

project_id

scene_id

shot_code

title

description

duration_seconds

order_index

status

creative_requirement
// legacy retained

main_action

key_constraints

negative_constraints

free_notes

created_at
updated_at
deleted_at
```

唯一：

```text
project_id + shot_code
```

Status：

```text
DRAFT

ASSET_PREPARING

STORYBOARD_PROMPT_READY

STORYBOARD_READY

VIDEO_PROMPT_READY

VIDEO_GENERATING

REVIEW

DONE
```

UI label：

```text
Draft
Asset Preparing
Storyboard Prompt Ready
Storyboard Ready
Video Prompt Ready
Video Generating
Review
Done
```

---

# 7.7 Asset

Phase 3 基础语义：

```text
id UUID

name

asset_type

original_filename

stored filename / relative storage path

mime_type

file_size

width nullable

height nullable

duration_seconds nullable

created_at
updated_at
deleted_at
```

AssetType：

```text
IMAGE
VIDEO
STORYBOARD_6GRID
OTHER
```

Storage：

```text
Original:
storage/assets/<前两位>/<UUID>.<ext>

Thumbnail:
storage/thumbnails/<UUID>.jpg
```

Thumbnail：

```text
max long edge:
512px
```

Phase 3 limits：

```text
单文件 <= 512 MiB

解码尺寸 <= 40,000,000 pixels
```

依赖：

```text
Pillow 12.3.0

PyAV 18.1.0
```

---

# 7.8 Tag

关系：

```text
Asset
N:N
Tag
```

不做：

```text
nested tag
tag group
tag hierarchy
```

---

# 7.9 Character

```text
id UUID

project_id

name

description

notes nullable

created_at
updated_at
deleted_at
```

唯一：

```text
project_id + name
```

---

# 7.10 CharacterState

```text
id UUID

character_id

name

description

order_index

created_at
updated_at
deleted_at
```

唯一：

```text
character_id + name
```

---

# 7.11 Character Links

```text
CharacterAssetLink

character_id
+
asset_id
UNIQUE
```

```text
CharacterStateAssetLink

character_state_id
+
asset_id
UNIQUE
```

```text
ShotCharacterStateLink

shot_id

character_state_id

character_id
```

核心：

```text
one Shot
+
same Character
→ one active CharacterState
```

---

# 7.12 PromptTemplate

数据模型方向：

```text
id UUID

scope

project_id nullable

name

description nullable

category

template_content

created_at
updated_at
deleted_at
```

Scope：

```text
GLOBAL
PROJECT
```

GLOBAL：

```text
project_id = NULL
```

PROJECT：

```text
project_id required
```

禁止：

```text
GLOBAL + project_id

PROJECT + NULL
```

---

# 7.13 PromptTemplate Category

```text
STORYBOARD_6GRID

VIDEO_GENERATION

CHARACTER_IMAGE

SCENE_IMAGE

IMAGE_REFERENCE

START_END_FRAME

OTHER
```

UI friendly labels：

```text
Storyboard 6-Grid
Video Generation
Character Image
Scene Image
Image Reference
Start / End Frame
Other
```

---

# 7.14 Placeholder 白名单

```text
{{shot_code}}

{{shot_title}}

{{shot_description}}

{{duration_seconds}}

{{main_action}}

{{key_constraints}}

{{negative_constraints}}

{{free_notes}}

{{scene_name}}

{{scene_description}}

{{scene_fixed_constraints}}

{{scene_negative_constraints}}

{{characters_context}}

{{reference_assets_context}}

{{shot_context}}
```

合法：

```text
{{main_action}}

{{ main_action }}
```

非法：

```text
{{main_aciton}}

{{foo.bar}}

{{characters[0]}}

{{__class__}}

{% if %}

{% for %}
```

错误：

```text
INVALID_TEMPLATE_PLACEHOLDER
```

---

# 7.15 Prompt Template 示例

```text
【镜头信息】
编号：{{shot_code}}
标题：{{shot_title}}
时长：{{duration_seconds}} 秒

【场景】
{{scene_name}}
{{scene_description}}

【角色】
{{characters_context}}

【主要动作】
{{main_action}}

【关键约束】
{{key_constraints}}

【负面约束】
{{negative_constraints}}

【补充说明】
{{free_notes}}
```

注意：

```text
这是模板系统示例
不等于正式 Seedance 模板
```

用户实际视频 Prompt 常使用：

```text
【参考指令】

【分镜序列】

【全局风格与运镜】

【声音设计】

【负面约束】
```

Template Editor 必须保持：

```text
中文

换行

全角标点

长段落

复制格式稳定
```

---

# 7.16 PromptRecord

Phase 7 初始 generation fact 明确语义：

```text
id UUID

shot_id

template_id

template snapshot

prompt_type

context snapshot

rendered_input

input_hash

generated_content

provider

model

created_at
updated_at
```

Phase 8 新增/冻结：

```text
version

edited_content

is_selected
```

确切 SQLAlchemy 字段名、索引名和所有列：

```text
必须从当前 PromptRecord model
和 docs/PHASE_8_STATUS.md 读取
```

因为本对话没有逐字贴出完整最终 SQL schema。

不可变生成事实：

```text
generated_content

template snapshot

context snapshot

rendered_input

input_hash

provider/model
```

人工可编辑：

```text
edited_content
```

effective：

```text
edited_content ?? generated_content
```

---

# 7.17 Storyboard

Phase 9 final schema：

```text
id UUID

shot_id FK

asset_id FK

source_prompt_record_id FK nullable

storyboard_type = GRID_6

version INTEGER > 0

is_selected BOOLEAN

notes nullable

created_at

updated_at

deleted_at
```

Constraints：

```text
Shot + version UNIQUE

same active Shot
→ at most one selected
```

Source：

```text
source_prompt_record_id != NULL

→ PromptRecord.shot_id == Storyboard.shot_id
```

Asset：

```text
asset_type == STORYBOARD_6GRID
```

---

# 7.18 Storyboard API

```http
GET  /api/shots/{shot_id}/storyboards

POST /api/shots/{shot_id}/storyboards

POST /api/shots/{shot_id}/storyboards/import

GET  /api/storyboards/{id}

POST /api/storyboards/{id}/select

DELETE /api/storyboards/{id}

POST /api/storyboards/{id}/restore
```

---

# 7.19 Workspace Settings API

```http
GET /api/settings/workspace

PUT /api/settings/workspace
```

Response 至少用于显示：

```text
workspace root

database path
```

---

# 7.20 Projects API

```http
GET    /api/projects

POST   /api/projects

GET    /api/projects/{id}

PATCH  /api/projects/{id}

DELETE /api/projects/{id}
```

Create 示例：

```json
{
  "name": "SPF屏障设施培训视频",
  "description": "实验动物屏障设施新员工培训",
  "status": "DRAFT"
}
```

---

# 7.21 Scripts API

```http
GET    /api/projects/{project_id}/scripts

POST   /api/projects/{project_id}/scripts

GET    /api/scripts/{id}

PATCH  /api/scripts/{id}

DELETE /api/scripts/{id}
```

---

# 7.22 Scenes API

```http
GET    /api/projects/{project_id}/scenes

POST   /api/projects/{project_id}/scenes

GET    /api/scenes/{id}

PATCH  /api/scenes/{id}

DELETE /api/scenes/{id}
```

概念 Create：

```json
{
  "script_id": "<uuid>",
  "name": "风淋室",
  "description": "二更与核心区之间的风淋空间",
  "fixed_constraints": "两扇门位于前后两端，喷嘴位置固定",
  "negative_constraints": "两门不得同时开启"
}
```

---

# 7.23 Shots API

```http
GET    /api/projects/{project_id}/shots

GET    /api/scenes/{scene_id}/shots

POST   /api/scenes/{scene_id}/shots

GET    /api/shots/{id}

PATCH  /api/shots/{id}

DELETE /api/shots/{id}
```

Shot Workspace：

```http
GET /api/shots/{id}/workspace

PUT /api/shots/{id}/character-states
```

Phase 5 PATCH：

```json
{
  "main_action": "...",
  "key_constraints": "...",
  "negative_constraints": "...",
  "free_notes": "..."
}
```

---

# 7.24 Assets API

以下均带 `/api` 前缀：

```http
GET    /assets

POST   /assets/upload

GET    /assets/{id}

PATCH  /assets/{id}

DELETE /assets/{id}

POST   /assets/{id}/restore

GET    /assets/{id}/file

GET    /assets/{id}/thumbnail

GET    /tags

POST   /tags

POST   /assets/{id}/tags/{tag_id}

DELETE /assets/{id}/tags/{tag_id}

POST   /projects/{id}/assets

DELETE /projects/{id}/assets/{asset_id}

POST   /shots/{id}/assets

DELETE /shots/{id}/assets/{asset_id}
```

---

# 7.25 Character API

均带 `/api`：

```http
GET  /projects/{project_id}/characters

POST /projects/{project_id}/characters

GET    /characters/{id}

PATCH  /characters/{id}

DELETE /characters/{id}

POST /characters/{id}/restore

GET  /characters/{id}/states

POST /characters/{id}/states

GET    /character-states/{id}

PATCH  /character-states/{id}

DELETE /character-states/{id}

POST /character-states/{id}/restore

POST /character-states/{id}/move

POST   /characters/{id}/assets

DELETE /characters/{id}/assets/{asset_id}

POST   /character-states/{id}/assets

DELETE /character-states/{id}/assets/{asset_id}

GET  /shots/{shot_id}/character-states

POST /shots/{shot_id}/character-states

DELETE /shots/{shot_id}/character-states/{state_id}
```

---

# 7.26 PromptTemplate API

Phase 6 已完成。

本对话没有逐字保存最终完整 endpoint 路径。

实际 API 必须从：

```text
docs/PHASE_6_STATUS.md

FastAPI /openapi.json

当前 templates route
```

恢复。

已确认能力：

```text
list

create

get

update

soft delete

restore

duplicate

copy global → project

placeholder definitions

preview
```

Query：

```text
scope
project_id
category
search
```

不要根据早期 Agent Prompt 猜 endpoint。

---

# 7.27 Phase 7 / 8 Prompt API

已知能力：

```text
AI Provider Settings GET/PUT

Shot actual input preview

Generate

Latest

Prompt detail

History

Edit

Regenerate

Select
```

但本对话没有逐字保存最终所有 endpoint path。

权威来源：

```text
docs/PHASE_7_STATUS.md

docs/PHASE_8_STATUS.md

FastAPI /openapi.json

当前 prompt routes
```

新 AI 必须现场读取。

---

# 7.28 Error Schema

统一：

```json
{
  "code": "ERROR_CODE",
  "message": "Human readable message",
  "details": {}
}
```

已知：

```text
PROJECT_NOT_FOUND

SCRIPT_NOT_FOUND

SCENE_NOT_FOUND

SHOT_NOT_FOUND

SHOT_CODE_CONFLICT

INVALID_PROJECT_RELATION

ASSET_IN_USE

CHARACTER_NOT_FOUND

CHARACTER_STATE_NOT_FOUND

CHARACTER_NAME_CONFLICT

CHARACTER_STATE_NAME_CONFLICT

CHARACTER_STATE_IN_USE

SHOT_CHARACTER_STATE_CONFLICT

WORKSPACE_INVALID

BOOTSTRAP_INVALID

FILE_NOT_FOUND

PROMPT_TEMPLATE_NOT_FOUND

PROMPT_TEMPLATE_NAME_CONFLICT

INVALID_TEMPLATE_SCOPE

INVALID_TEMPLATE_CATEGORY

INVALID_TEMPLATE_PLACEHOLDER
```

Phase 9 还存在 Storyboard-specific errors，精确 code 名称必须读取当前实现。

前端不得只显示：

```text
500 Internal Server Error

IntegrityError

raw traceback
```

---

# 7.29 当前相关目录 / 文件路径

## Repo

```text
D:\GitHub_kyandi-i\AI_Web
```

## Frontend

```text
D:\GitHub_kyandi-i\AI_Web\frontend

D:\GitHub_kyandi-i\AI_Web\frontend\package.json

D:\GitHub_kyandi-i\AI_Web\frontend\components.json

D:\GitHub_kyandi-i\AI_Web\frontend\src\components\ui\button.tsx
```

当前 Prompt / Storyboard / Shot Workspace 精确 feature 文件：

```text
必须从 git show 与仓库读取
```

## Backend

```text
D:\GitHub_kyandi-i\AI_Web\backend

D:\GitHub_kyandi-i\AI_Web\backend\app

D:\GitHub_kyandi-i\AI_Web\backend\tests

D:\GitHub_kyandi-i\AI_Web\backend\test_support

D:\GitHub_kyandi-i\AI_Web\backend\app\services\workspace.py

D:\GitHub_kyandi-i\AI_Web\backend\app\models\assets.py

D:\GitHub_kyandi-i\AI_Web\backend\tests\test_workspace.py

D:\GitHub_kyandi-i\AI_Web\backend\tests\test_workspace_bootstrap.py

D:\GitHub_kyandi-i\AI_Web\backend\tests\test_bootstrap.py

D:\GitHub_kyandi-i\AI_Web\backend\tests\test_shot_workspace.py

D:\GitHub_kyandi-i\AI_Web\backend\tests\test_characters.py
```

Migration：

```text
D:\GitHub_kyandi-i\AI_Web\
backend\app\migrations\versions\
```

当前 head：

```text
0009_storyboards
```

## Docs

```text
D:\GitHub_kyandi-i\AI_Web\README.md

D:\GitHub_kyandi-i\AI_Web\DEVELOPMENT_STATUS.md

D:\GitHub_kyandi-i\AI_Web\PROJECT_PLAN.md

D:\GitHub_kyandi-i\AI_Web\docs\PHASE_3_1_STATUS.md

D:\GitHub_kyandi-i\AI_Web\docs\PHASE_4_STATUS.md

D:\GitHub_kyandi-i\AI_Web\docs\PHASE_5_STATUS.md

D:\GitHub_kyandi-i\AI_Web\docs\PHASE_5_1_STATUS.md

D:\GitHub_kyandi-i\AI_Web\docs\PHASE_6_STATUS.md

D:\GitHub_kyandi-i\AI_Web\docs\PHASE_7_STATUS.md

D:\GitHub_kyandi-i\AI_Web\docs\PHASE_8_STATUS.md

D:\GitHub_kyandi-i\AI_Web\docs\PHASE_9_STATUS.md
```

旧完整规格：

```text
D:\GitHub_kyandi-i\AI_Web\
AI Video Workspace · MVP v0.1 开发规格.md
```

Phase 9 曾引用其中：

```text
第 27 节附近
Storyboard import
→ Link Project
→ Link Shot
```

## Production

```text
D:\AI-Video-Workspace
```

Config：

```text
D:\AI-Video-Workspace-Config\config.json
```

DB：

```text
D:\AI-Video-Workspace\data\workspace.db
```

Backups：

```text
D:\AI-Video-Workspace\backups\
```

---

# 7.30 修改文件记录

## 重要说明

用户要求：

> 对每个被修改过的文件，注明修改了什么、为什么改、当前是否通过测试。

但本次对话并没有把 Phase 7/8/9 的完整 `git show --name-status` 内容逐字贴入聊天。

已知：

```text
Phase 7:
35 个修改文件

Phase 8:
20 个修改文件

Phase 9:
26 个修改文件
```

完整清单存在本机：

```text
docs/PHASE_7_STATUS.md

docs/PHASE_8_STATUS.md

docs/PHASE_9_STATUS.md
```

以及对应 Git commits。

因此：

**禁止在 HANDOFF 中编造 81 个文件名。**

新 AI 第一轮必须运行：

```powershell
git show --name-status 15b9607e0ee785595792c93d9ba4774aae71620d

git show --name-status ef9b8a9732678a427d33a1db5ee61a6f9ae5bcea

git show --name-status baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2
```

并读取对应状态文档。

### 已明确知道的修改/相关文件

| 文件 | 修改 / 原因 | 当前结果 |
|---|---|---|
| `backend/app/services/workspace.py` | Phase 5.1 移除 initialize 时 silent `bootstrap.save(fallback)` | PASS；Phase 9 全量 Backend 314/314 |
| `backend/tests/test_workspace.py` | Phase 5.1 Workspace root/config safety 回归 | PASS |
| `backend/tests/test_workspace_bootstrap.py` | Phase 5.1 Bootstrap Config 回归 | PASS |
| `backend/tests/test_bootstrap.py` | Phase 6 新增 `prompt_templates` 表后更新旧 expected table list | PASS；Phase 6 之后全量持续通过 |
| `backend/tests/__init__.py` | Phase 7 曾新增，导致 pytest import regression | **最终已删除，不应重新添加** |
| `backend/test_support/...` | Phase 7 将共享 Fake Provider / E2E support 移出 tests package，避免改变 pytest module resolution | PASS；Phase 7–9 全量回归通过 |
| `backend/app/models/assets.py` | Asset/Link model；Phase 9 Storyboard Asset 生命周期审计的重要现有文件 | Phase 9 PASS |
| `README.md` | 多 Phase 更新功能/运行状态 | Phase 9 最终状态已更新 |
| `DEVELOPMENT_STATUS.md` | 多 Phase 更新阶段与验证结果 | Phase 9 最终状态已更新 |
| `PROJECT_PLAN.md` | 多 Phase 更新 roadmap / phase boundary | Phase 9 最终状态已更新 |
| `docs/PHASE_5_1_STATUS.md` | Workspace Config hardening 记录 | PASS |
| `docs/PHASE_6_STATUS.md` | Prompt Template 最终验收 | Phase 6 COMPLETE |
| `docs/PHASE_7_STATUS.md` | AI Prompt Generation、两次 Failure-stop 与最终验收 | Phase 7 COMPLETE |
| `docs/PHASE_8_STATUS.md` | Prompt Versioning、CRLF/LF recovery 与最终验收 | Phase 8 COMPLETE |
| `docs/PHASE_9_STATUS.md` | Storyboard Workflow、3 次 Recovery/Failure-stop、最终验收 | Phase 9 COMPLETE |
| `HANDOFF.md` | 用户自己维护的交接文件；不属于 Phase commit | 用户当前正在生成新版，Agent 不得擅自提交 |

Phase 9 Storyboard 的具体：

```text
model
repository
service
routes
schemas
migration
frontend panel
browser tests
Asset lifecycle integration
```

完整路径必须：

```text
git show --name-status baab8a2...
+
docs/PHASE_9_STATUS.md
```

恢复。

所有 Phase 9-owned 文件在 commit `baab8a2...` 后已通过：

```text
Backend 314/314

Browser production 62/62

Browser development 64/64

lint/build/Ruff

Alembic

populated migration
```

---

# 7.31 已解决问题 / 报错原文与排除项

## A. Select Hover / Row Height

原用户问题：

> “鼠标悬停在选项处会出现如图遮挡选项的问题，而且选中状态与实际的选项栏目每一行行高不一样”

修复：

```text
Select Trigger / Item 36px

indicator 独立留位

padding/alignment

friendly enum labels
```

排除：

```text
不是后端 CRUD

不是图标 CDN

不是多个图标库冲突
```

Phase 2.5 已回归通过。

---

## B. Workspace 回到 C 盘

症状：

```text
Workspace Root:
C:\Users\Lenovo\AI-Video-Workspace

Database:
C:\Users\Lenovo\AI-Video-Workspace\data\workspace.db
```

根因：

```text
Normal Windows 和 Codex 使用不同 APPDATA config

+

missing config fallback 会自动 save(C)
```

修复：

```text
AVW_BOOTSTRAP_CONFIG_PATH
→ D:\AI-Video-Workspace-Config\config.json

initialize_workspace
不再 silent save
```

已排除：

```text
不是 UI 显示错误

不是 D DB 数据丢失

不是 Phase 4/5 数据写到了 C

不是 C DB 比 D DB 更新
```

D 一直是完整真实业务数据。

---

## C. Phase 6 Backend Regression

失败位置：

```text
backend/tests/test_bootstrap.py:54
```

原因：

```text
旧 expected table list
没有 prompt_templates
```

不是：

```text
PromptTemplate domain 本身失败
```

因为 Phase 6 新 Backend tests：

```text
44/44 PASS
```

修复后：

```text
Backend 201/201 PASS
```

---

## D. Browser tests 显示 PASS 但进程挂起

中间现象：

```text
新增浏览器用例均显示通过
但进程收尾不退出
```

最终定位：

```text
sandbox process reaping / process cleanup permission issue
```

获准环境：

```text
exit code 0
```

排除：

```text
不是 assertion failure

不是 Phase 6 UI 失败
```

禁止通过：

```text
process.exit(0)
```

掩盖。

---

## E. `backend\.workspace` ACL

偶发：

```text
backend\.workspace
```

由：

```text
CodexSandboxOffline
```

留下 restrictive ACL / deny entries。

影响：

```text
pytest temp dirs
```

曾被阻断。

禁止：

```text
takeown

icacls reset

remove deny ACE
```

除非用户明确授权单独处理。

---

## F. Phase 7 第一次开工 `WinError 5`

报告原文关键：

```text
WinError 5
```

发生于：

```text
pytest fixture 初始化
临时目录访问失败
```

沙箱外隔离 Asset 测试：

```text
30/30 PASS
```

后续完整正常环境：

```text
Backend 201/201 PASS
```

因此已排除：

```text
不是 Phase 0-6 backend baseline 逻辑失败
```

属于：

```text
sandbox/temp permission environment issue
```

注意：

第一次生产 hash baseline 读取失败后仍启动测试，是一次已确认的执行顺序错误。

以后：

```text
production hash baseline fail
→ STOP
```

---

## G. Phase 7 `backend/tests/__init__.py` Regression

新增：

```text
backend/tests/__init__.py
```

导致：

```text
test_shot_workspace.py
```

无法导入：

```text
test_characters
```

完整 pytest：

```text
collection error
exit 2
```

排除：

```text
不是 AIProvider 业务失败

不是 PromptRecord schema 失败

不是 Shot Workspace assertion failure
```

最终修复：

```text
删除 backend/tests/__init__.py

共享 Fake Provider / E2E support
→ backend/test_support
```

最终：

```text
Backend 253/253 PASS
```

---

## H. Phase 8 Clipboard CRLF/LF

Browser Failure：

```text
Clipboard actual:
CRLF
\r\n

Expected:
LF
\n
```

验证：

```text
字符内容相同
段落相同
logical lines 相同
```

排除：

```text
不是 edited_content 复制错误

不是 generated_content 选择错误

不是 DB 文本被修改

不是 Prompt 换行损坏
```

最终：

```text
只在测试：
\r\n → \n
```

再做严格全文比较。

最终 Phase 8 Browser：

```text
6/6 PASS
```

---

## I. Phase 9 Thumbnail Locator

原测试：

```ts
v1.getByRole("img")
```

同时匹配：

```text
Storyboard thumbnail

3 个按钮中的 Lucide SVG
```

Playwright：

```text
strict-mode error
```

排除：

```text
不是 thumbnail 加载失败

不是 Asset file endpoint 错误

不是 Lucide 业务问题
```

最终：

```ts
v1.getByRole("img", {
  name: "Storyboard V1 thumbnail",
  exact: true,
})
```

---

## J. Phase 9 Detail Original Locator

原测试：

```ts
detail.getByRole("img")
```

同时匹配：

```text
Storyboard V1 original

关闭按钮内 Lucide X
```

排除：

```text
不是 original image 加载失败

不是错误 Asset

不是详情业务失败
```

最终：

```ts
detail.getByRole("img", {
  name: "Storyboard V1 original",
  exact: true,
})
```

---

## K. Phase 9 Asset 删除文案回归

Production Browser：

```text
Expected:
请先解除绑定

Received:
请先解除引用
```

两个旧 Asset Library：

```text
dark
light
```

用例失败。

原因：

```text
Phase 9 同时修改：

Backend AssetService error message

Frontend Asset Detail delete copy
```

排除：

```text
不是旧测试 outdated

不是 Storyboard in-use protection 应删除

不是只需修改 expected
```

最终：

```text
恢复：
请先解除绑定
```

同时保留：

```text
Storyboard reference count

ASSET_IN_USE

Asset type protection
```

最终 Browser：

```text
production 62/62
development 64/64
```

---

# 7.32 Production Backups

已明确记录：

```text
D:\AI-Video-Workspace\backups\
before-phase4-20260923.db
```

```text
D:\AI-Video-Workspace\backups\
before-phase5-20260923.db
```

```text
D:\AI-Video-Workspace\backups\
before-workspace-config-fix-20260924-161401.db
```

Phase 6：

```text
创建过同 SHA-256 backup
```

但文件名未在聊天逐字记录。

不要猜，列目录确认。

Phase 7：

```text
D:\AI-Video-Workspace\backups\
before-phase7-20260925-154932.db
```

SHA：

```text
ba3a55ad8ea6e3881cd3b40261c0923e614902e01527faea33bc66851525f44c
```

Phase 8：

```text
D:\AI-Video-Workspace\backups\
before-phase8-20260929-231526.db
```

SHA：

```text
f1ccc50edb6457e2884dae36eb8745eab025c39616df7afab7c626980f582b36
```

Phase 9：

```text
D:\AI-Video-Workspace\backups\
before-phase9-20260930-192304.db
```

SHA：

```text
6bcbefa34fd56937a7b315a76a4613bb73b64a73197a23d05b9070d7fc1778c5
```

---

# 7.33 最新测试基线

截至 Phase 9 COMPLETE：

```text
Phase 9 Backend:
28/28 PASS

Backend FULL:
314/314 PASS

Phase 9 Browser:
6/6 PASS

Browser production:
62/62 PASS

Browser development:
64/64 PASS

Frontend lint:
PASS

Frontend build:
PASS

Ruff check:
PASS

Ruff format --check:
PASS
97 files

Isolated Alembic CLI:
upgrade
downgrade
upgrade
check
current
PASS

Populated migration:
0008 → 0009 → 0008 → 0009
PASS
```

这就是 Phase 10 开工前的 regression baseline。

Phase 10 不得通过修改旧 expected 来降低此基线。

---

# 7.34 Browser 测试原则

已确认 Browser 测试必须：

```text
正常 exit code 0
```

不能只看：

```text
x/x passed
```

如果测试运行修改 Git-managed screenshots：

```text
测试后恢复纯测试产物
```

不要提交：

```text
test-results

trace

临时截图

dist
```

除非它们是明确版本控制 fixture。

---

# 7.35 当前用户要求的 Phase 流程

未来继续严格：

```text
用户说：
开始 Phase 10

→ Phase 10 audit/scope

→ implement

→ test

→ failure-stop if any fail

→ recovery

→ all green

→ production backup

→ production upgrade

→ acceptance

→ docs

→ commit

→ report

→ STOP

→ 等用户：
开始 Phase 11
```

不得自动：

```text
Phase 10 完成
→ 直接做 Phase 11
```

---

# 7.36 新 AI 最低接手检查顺序

第一件事：

```powershell
cd D:\GitHub_kyandi-i\AI_Web

git status --short

git log --oneline -10
```

确认：

```text
HEAD
==
baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2
```

如果用户刚保存了新版 HANDOFF.md：

```text
M HANDOFF.md
```

是预期。

然后：

```powershell
git show --name-status baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2

git show --stat baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2
```

读取：

```text
README.md

DEVELOPMENT_STATUS.md

PROJECT_PLAN.md

docs/PHASE_9_STATUS.md

docs/PHASE_8_STATUS.md

frontend/package.json

backend dependency config
```

检查 runtime：

```text
Bootstrap:
D:\AI-Video-Workspace-Config\config.json

Workspace:
D:\AI-Video-Workspace

DB:
D:\AI-Video-Workspace\data\workspace.db

Revision:
0009_storyboards
```

不满足：

```text
STOP
```

不要直接开 Phase 10。

---

# 7.37 Phase 10 铁约束

开始 Phase 10 后：

```text
禁止提前 Phase 11 Export / Recycle Bin 总收尾

禁止 Video Generation API

禁止 GenerationJob

禁止后台队列

禁止视频编辑 Timeline

禁止审批流

禁止多人协作
```

媒体必须继续走：

```text
Asset
```

不要：

```text
VideoResult binary in DB

base64 video JSON
```

测试：

```text
Fake / imported local video fixture
```

不要调用真实收费生成服务。

Production：

```text
只 schema upgrade
```

不要插 fake VideoResult 做验收。

验收：

```text
production data isolated copy
```

优先。

---

# 7.38 Project Export 最终目标

Phase 11 最终至少：

```text
Project
→ Export
→ <ProjectName>.zip
```

至少：

```text
project.json

assets/

prompts/

metadata/
```

包含：

```text
Project

Script

Scenes

Shots

Asset metadata

Project Assets

Shot Assets

Characters

CharacterStates

PromptTemplates

PromptRecords

Storyboards

VideoResults

Notes

Tags

实际引用文件
```

API Key：

```text
默认不导出
```

Import 可后置。

Export 格式：

```text
必须具备未来可恢复性
```

**Phase 10 不要提前实现这一块。**

---

# 7.39 资源 / 性能原则

素材库未来大量：

```text
4K images
videos
```

保持：

```text
Grid uses thumbnails

不要列表加载原始 4K

视频不要全部 autoplay

不要 binary into SQLite

不要 large Base64 in JSON
```

旧资源 baseline：

```text
frontend/node_modules ≈ 184.90 MiB

backend/.venv ≈ 69.64 MiB
```

这些不是当前精确大小。

不要因为 bundle warning 现在就做复杂 code splitting。

---

# 7.40 UI 常规验收

每 Phase 至少检查：

```text
Dark
Light

1024px
1280px
```

检查：

```text
horizontal overflow

long title

long enum

Select

Dialog / Sheet

Sidebar

main workspace

loading

empty

error
```

当前不要求完整 Mobile UX。

---

# 8. 自我审查

一个完全没有此前对话记忆的新 AI，仅凭本文应能准确复述：

```text
1. 这是 Local-first AI Video Production Workspace

2. Phase 0～9 已完成

3. 最新 commit 是：
   baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2

4. 当前 Production DB revision：
   0009_storyboards

5. Production Workspace：
   D:\AI-Video-Workspace

6. Bootstrap Config：
   D:\AI-Video-Workspace-Config\config.json

7. Prompt generation / versioning 已完成

8. Storyboard V1/V2、Selected、Asset/Prompt provenance 已完成

9. 当前完整测试基线：
   Backend 314/314
   Browser prod 62/62
   Browser dev 64/64

10. 下一步是 Phase 10 Video Result

11. Phase 10 尚未冻结最终数据模型

12. 不能提前做 Video Generation API / Phase 11

13. 自动化测试绝不能写 Production Workspace

14. 真实 DB 只能 upgrade，不能 downgrade

15. 任何影响模型的歧义先问用户

16. Failure-stop 必须继续执行
```

本次交接仍有几项必须从仓库现场恢复、不能靠本文猜测：

```text
当前 React / Vite / FastAPI / SQLAlchemy 等精确版本

当前正式 startup commands

当前正式 test commands

Phase 2.5 commit hash

Phase 6 完整 modified-file list

Phase 7 35 个文件完整列表

Phase 8 20 个文件完整列表

Phase 9 26 个文件完整列表

Phase 6 PromptTemplate 最终 endpoint 全路径

Phase 7/8 Prompt Generation / Versioning 最终 endpoint 全路径

Phase 7/8 PromptRecord 精确 SQLAlchemy 完整字段名与索引名
```

这些不是“可以自由决定”的空白。

必须通过：

```text
git show

package.json

lockfile

backend dependency config

FastAPI /openapi.json

docs/PHASE_6_STATUS.md

docs/PHASE_7_STATUS.md

docs/PHASE_8_STATUS.md

docs/PHASE_9_STATUS.md
```

恢复。

不要编造。

---

如果以上信息与用户新提供的内容有矛盾，请先向用户确认，不要自行假设或编造缺失的细节。
````