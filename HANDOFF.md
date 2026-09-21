> 历史交接记录：此文件在 Phase 3 开始时已存在但未跟踪，正文保留。其 Phase 2.5 未完成、历史测试数量和部分路径说明已过期。当前事实请阅读 [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) 与代码 / migration / tests；本轮已获用户正式授权 Phase 3，完成后等待验收，不进入 Phase 4。

# HANDOFF.md

## 1. 现状速览

这是一个 **Local-first AI Video Production Workspace**：用于管理 AI 视频项目、剧本、场景、镜头、资产、角色状态、Storyboard、Prompt 模板/版本和外部生成结果，不在 MVP 内直接生成图片或视频。当前 **Phase 0、1、1.5、2 已完成**，最新业务提交为 `71d25ba`，后端 81/81、浏览器构建模式 17/17、开发模式 19/19 均通过；目前发现一个公共 Select/状态下拉框严重 UI Bug，尚未进入 Phase 3。下一步先执行 **Phase 2.5 UX Fix**，修复 Select、枚举显示和现有 Project/Scene/Shot 表单交互，用户确认后再进入 Phase 3 Asset Library。

---

# 2. 目标与约束

## 2.1 最终目标

构建一个真正用于 AI 视频生产的本地 Web 工作台，核心流程为：

```text
Project
→ Script
→ Scene
→ Shot
→ 绑定角色 / 状态 / 场景 / 道具 / 参考资产
→ 填写结构化镜头需求 + 自由补充
→ 选择 Prompt Template
→ AI 生成六宫格 Prompt
→ 保存 Prompt 历史
→ 复制至外部平台
→ 外部生成六宫格
→ 导回应用成为 Storyboard Asset
→ 基于 Storyboard/镜头需求生成视频 Prompt
→ 复制至外部视频平台
→ 导回视频结果
→ 保存 V1/V2/V3 + 备注
→ 选择最终版本
→ Shot DONE

MVP 完成后应首先服务真实 AI 视频项目，而不是做成一个展示性质的 SaaS Dashboard。

2.2 产品边界

MVP 负责：

项目管理
剧本结构
场景管理
镜头管理
统一资产库
角色 / CharacterState
Storyboard
Prompt Template
Prompt Generation
Prompt History / Version
外部生成结果管理
Project Export

MVP 不负责：

用户注册 / 登录
多人实时协作
云同步
在线聊天
图片直接生成
视频直接生成
Premiere 式时间轴
在线视频编辑
复杂版本分支
评论 / 审批流
权限系统
SaaS 计费
插件市场

后期允许增加 Image / Video Generation API，但不得影响当前业务层设计。

2.3 技术栈

已冻结：

Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- React Router
- TanStack Query
- Zod
- React Hook Form（规划/建议）

Backend
- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

Database
- SQLite

Storage
- Managed Local Storage

Icons
- lucide-react

AI
- OpenAI-compatible unified provider
已知版本
组件	当前已知版本
Python	3.12.11（审计时 uv 共享 Python）
lucide-react	0.468.0
React	对话中未记录精确版本，必须读取 frontend/package.json
React DOM	同上
Vite	同上
TypeScript	同上
Tailwind CSS	同上
FastAPI	对话中未记录精确 PyPI 版本
SQLAlchemy	同上
Alembic	同上
Pydantic	同上

不要猜版本。接手后直接读取当前仓库的 package.json、lockfile、pyproject.toml/后端依赖文件。

2.4 代码运行环境

当前明确为：

Windows 11
Local development
非 CI-only
非 Docker 强依赖
非容器优先

项目路径：

D:\GitHub_kyandi-i\AI_Web

已知运行端口：

FastAPI / 完整应用：
http://127.0.0.1:8765

Vite Development：
http://127.0.0.1:5173

Phase 0 时用户曾通过：

http://127.0.0.1:8765

打开工作台。

已确认测试/迁移操作

Alembic 必须支持：

alembic upgrade head
alembic downgrade
alembic upgrade head

Phase 2 已报告：

lint        PASS
build       PASS
backend     81/81 PASS
browser production/build mode 17/17 PASS
browser development mode 19/19 PASS
Alembic upgrade/downgrade PASS

实际 npm/uv 启动与测试脚本名未在对话里逐字记录，禁止自行猜测；以根目录 README、frontend/package.json 和后端项目配置为准。

2.5 用户协作硬规则

用户明确要求：

任何存在疑问、歧义、缺失需求，或会影响架构、数据模型、功能边界、交互逻辑、后续扩展的选择，都必须先问用户；直到完全理解以后再继续。

因此禁止：

自行补需求
自行改变数据模型
自行更换技术栈
自行增加未来功能
自行决定存在歧义的 UX 行为
2.6 架构硬约束

禁止未经确认：

更换 React/Vite
加入 Next.js
加入 Electron/Tauri 作为当前主形态
要求 Docker 才能运行
SQLite → PostgreSQL
改变 Managed Storage 策略
把大型文件写进 SQLite
删除 Service / Repository 边界
直接让 Route 操作 SQL
在业务代码中散落具体 AI 厂商调用
加入 Redis / Celery / Event Bus / CQRS / 微服务

架构要求：

Route
↓
Service
↓
Repository / Provider

抽象边界：

AIService
↔ AIProvider

StorageService
↔ StorageProvider

Business Service
↔ Repository

Asset
↔ Project / Shot Link

Prompt
↔ Template

Prompt
↔ future GenerationJob
2.7 ID 与删除

所有核心实体统一：

UUID

不得把数据库自增 1,2,3... 当业务实体主键。

默认删除：

Delete
↓
Soft Delete / Recycle Bin
↓
Restore

或

Permanent Delete（必须再次明确确认）

字段：

deleted_at

资产永久删除前必须检查引用。

2.8 Workspace 与存储

采用：

Managed Local Storage

用户导入：

D:\Downloads\character.png

系统：

读取
→ UUID
→ 复制到 Workspace storage
→ 保存相对路径
→ 原文件以后移动/删除不影响 Asset

禁止只保存原始文件绝对路径。

Workspace Root 必须能在 Settings 中修改。

内部结构设计：

<workspace_root>/
├── data/
│   └── workspace.db
├── storage/
│   ├── assets/
│   ├── thumbnails/
│   └── temp/
├── exports/
└── backups/

Bootstrap Config 必须独立于 workspace.db，否则会形成：

不知道 Workspace Root
→ 找不到 DB
→ 需要 DB 才知道 Workspace Root
2.9 UI/UX 硬约束

用户给出的目标参考是：

Premium Black Workspace
高信息密度
专业生产工具
紧凑面板
弱边框
深色高级感
青绿色 Accent

必须：

默认 Dark
支持 Light
Theme Preference 持久化

当前 Token：

Token	Dark	Light
Background	#111517	#F2F5F6
Panel	#191F23	#FFFFFF
Card	#20272C	#F7F9FA
Accent	#53D9B0	#087B61

禁止恢复成：

大面积白底
Landing Page 风格
营销 Hero
巨量留白
“Phase X / 待开发”作为正式产品内容
紫色作为主 Accent
Gaming Neon
2.10 图标原则

图标必须：

单一 lucide-react
SVG Component
具名 import
Vite tree-shaking
本地离线使用

例如：

import {
  Folder,
  Settings,
  Film,
  Image,
} from "lucide-react";

禁止：

远程图标 API
图标 CDN
同时装 react-icons / FontAwesome / Material Icons / Heroicons 等多套库
import 整个 Icons 对象
大量 PNG/JPG 作为 UI 图标

原因：

Local-first
Offline-friendly
避免网络依赖
实际 SVG 体积很小
3. 已被否决的方案及原因
3.1 仅使用 IndexedDB

否决。

曾考虑纯前端：

React + IndexedDB

但最终选择：

React Web
+
FastAPI
+
SQLite
+
Managed Local File Storage

原因：

未来有大量高清图片/视频
IndexedDB 容量/浏览器清理/备份/迁移不理想
本地文件 + SQLite 更适合大资产
未来迁 PostgreSQL + S3/MinIO/OSS 更自然
3.2 Asset 只引用用户原始文件路径

否决。

被否决方案：

数据库记录：
D:\项目\SPF\人物.png

原因：

用户移动文件后所有引用会失效
不利于备份
不利于导出
不利于未来多人/云存储

已选择：

导入
→ Copy into Managed Storage
3.3 Asset 分 Global Asset / Project Asset 两套实体

否决。

最终：

统一 Asset Library

Asset
↕
ProjectAssetLink
↕
Project

同一 Asset 可被多个 Project 和多个 Shot 引用。

原因：

长期真正积累的是角色库、场景库、道具库、Prompt/Storyboard 资产
不应该复制业务实体
3.4 数据库严格 Script → Scene → Shot，不保留 ScriptNode

否决。

最终选项 A：

Script
└── ScriptNode(type=SCENE)
    └── Scene
        └── Shot

职责：

ScriptNode：
树结构、parent、order、未来 Chapter / Sequence

Scene：
业务场景、约束、描述

原因：

未来可扩：

Script
└── Chapter
    └── Sequence
        └── Scene

而不需要重构已有 Scene。

3.5 单纯等所有功能完成后再整改前端

否决。

原因：

当前旧 UI 与目标 UI 不只是配色差异，而是：

营销式 SaaS 首页
vs
专业生产工作台

如果继续做到 Phase 5 再重构，会复制错误的布局和组件体系。

因此新增：

Phase 1.5 UI Foundation

并已完成。

3.6 只做 Dark Mode

否决。

用户明确选择：

B：Dark 默认 + Light 可切换
3.7 紫色 / 蓝紫 Accent

否决。

用户明确更喜欢：

黑色高级感 + 青绿色点缀

当前 Accent：

Dark  #53D9B0
Light #087B61
3.8 动态图标 API / CDN

否决。

原因：

破坏 Local-first
必须联网
存在加载延迟
外部服务可能失效
完全没必要

当前 lucide-react 已符合要求。

3.9 同时安装多个图标库

否决。

资源审计确认当前只有：

lucide-react 0.468.0

应继续保持。

3.10 现在就做 Electron/Tauri

暂不采用。

当前固定：

Local-first Web Application
Browser UI
Local FastAPI backend

Desktop Wrapper 只作为未来可能性。

3.11 MVP 内直接接图片/视频生成

否决为当前阶段功能。

当前只做：

需求
→ Prompt
→ 复制
→ 外部生成
→ 导回

但架构必须允许未来：

PromptRecord
→ GenerationJob
→ Image/Video API
→ Asset
3.12 微服务 / Redis / Celery / CQRS / Event Bus

否决。

原因：

个人本地工具
要求尽快上线
当前复杂度不需要
会增加维护成本
4. 当前具体状态
4.1 已完成 ✅
✅ Phase 0 — 项目初始化

已报告：

React 前端搭建
FastAPI 后端搭建
本地启动入口
构建
代码检查
后端测试
浏览器测试
README
DEVELOPMENT_STATUS

当时服务：

http://127.0.0.1:8765
✅ Phase 1 — Database + Alembic + Storage Infrastructure

已完成基础方向：

SQLite
SQLAlchemy
Alembic
UUID
Timestamp / Soft Delete
Bootstrap Config
Workspace
StorageProvider
LocalStorageProvider
Repository boundary
统一 Error Schema

Phase 2 后 Alembic 升降级仍正常。

✅ Phase 1.5 — UI Foundation

Git commit：

bf2113b

已完成：

Dark default
Light toggle + persistence

Sidebar
Topbar
Tool-style Dashboard

WorkspacePanel
PageHeader
SectionHeader
EmptyState
EntityCard
MediaCard
DetailSheet

统一基础控件

lucide-react only
无远程图标依赖

验证：

lint/build PASS
frontend production 12 tests PASS
frontend development 14 tests PASS
backend 61 tests PASS
Alembic PASS

当时 bundle：

gzip ≈ 198 kB

存在单包体积提示，但当前不视为阻塞问题。

不要为了消除警告提前做复杂拆包。

未来业务模块明显变大以后再考虑 route lazy loading / code splitting。

✅ Phase 2 — Project / Script / Scene / Shot

Git commit：

71d25ba

Git 工作区：

clean

已完成：

Project CRUD

Script CRUD

Scene CRUD

Shot CRUD

排序

搜索

筛选

详情编辑

Scene ↔ ScriptNode 事务一致

Scene 删除：
Scene soft delete
+ ScriptNode soft delete
+ child Shot soft delete

Shot Code 项目内唯一

测试 Workspace 与真实 Workspace 隔离

最新验证：

backend tests                  81/81 PASS
browser production/build      17/17 PASS
browser development           19/19 PASS
lint                           PASS
build                          PASS
Alembic upgrade/downgrade      PASS

README 与：

D:\GitHub_kyandi-i\AI_Web\DEVELOPMENT_STATUS.md

已更新。

✅ 资源占用审计

审计日期：

2026-09-20

注意：这是 Phase 1.5 前的 baseline，后续依赖大小可能已经变化。

当时项目：

D:\GitHub_kyandi-i\AI_Web

256.06 MiB 文件内容
276.72 MiB 文件分配空间

主要：

frontend/node_modules   184.90 MiB
backend/.venv            69.64 MiB

都在 D 盘。

当时运行 RAM：

开发服务 idle       ≈ 260 MiB
首页加载服务        ≈ 302 MiB
独立 Chromium       ≈ 572 MiB
合计                ≈ 874 MiB

未发现重复 dev server。

4.2 当前进行中 / 下一待执行 🔄
🔄 Phase 2.5 — UX Fix

尚未收到完成报告。

触发原因：

Shot 编辑表单的 Status Select 存在明显 UI Bug：

用户原话：

“在状态栏处有很大问题，鼠标悬停在选项处会出现如图遮挡选项的问题，而且选中状态与实际的选项栏目每一行行高不一样，如图选中状态的行高就不一样”

截图表现：

Trigger：
DRAFT

Dropdown：
DRAFT ✓

随后长状态文本发生堆叠/遮挡，例如：

STORYBOARD_PROMPT_READY
STORYBOARD_READY
VIDEO_PROMPT_READY
VIDEO_GENERATING
REVIEW

另外内部机器枚举直接暴露给 UI。

应显示为友好 Label。

4.3 待办 ⬜
⬜ Phase 2.5 UX Fix

必须先完成并让用户看截图确认。

⬜ Phase 3 — Asset Library

Phase 2.5 通过后开始。

目标：

图片 / 视频拖入
→ Managed Storage
→ Asset 建档
→ Thumbnail
→ Grid/List
→ Search
→ Asset Type Filter
→ Tag
→ DetailSheet
→ Project Asset Link
→ Shot Asset Link 基础
⬜ Phase 4 — Character / CharacterState
Character
1:N
CharacterState

State 可绑定多个参考 Asset
Shot N:N CharacterState
⬜ Phase 5 — Shot Workspace

核心生产页面。

完成后必须立即使用真实 AI 视频项目测试。

⬜ Phase 6 — Prompt Template
GLOBAL
PROJECT
⬜ Phase 7 — AI Prompt Generation

结构化输入：

Characters
Character States
Scene
Main Action
Duration
Key Constraints
Negative Constraints
Reference Assets
Free Notes
⬜ Phase 8 — Prompt Versioning
V1
V2
V3 ★

支持：

查看
编辑
复制
重新生成
设为最终
⬜ Phase 9 — Storyboard Workflow

六宫格导入：

AssetType = STORYBOARD_6GRID

默认一个六宫格绑定一个 Shot。

支持来源：

source_prompt_record_id
⬜ Phase 10 — Video Result
V1
V2
V3
note
is_selected
⬜ Phase 11 — Export / Recycle Bin / UX

Project ZIP Export 为 MVP 必需。

Import 可后置，但 Export 格式必须可恢复。

4.4 未确认执行的资源整改 ⬜

资源审计建议过：

Playwright

当时：

C:\Users\Lenovo\AppData\Local\ms-playwright
≈ 1,403.05 MiB

建议以后迁：

D:\study\DO\DevCache\playwright

通过：

PLAYWRIGHT_BROWSERS_PATH

没有收到明确“已迁移完成”的报告，因此禁止假定已经迁移。

真实 Workspace

审计时真实 Workspace：

C:\Users\Lenovo\AI-Video-Workspace

仅：

24 KiB

建议未来素材增长前切到：

D:\AI-Video-Workspace

也没有收到确认已经迁移的报告。

5. 关键决策记录
5.1 Product Model

最终不是：

AI Video Generator

而是：

AI Video Production Workspace

重点在：

组织
关联
版本
可视化
Prompt workflow
5.2 Script / Scene 模型

固定：

Script
└── ScriptNode(type=SCENE)
    └── Scene
        └── Shot

未来：

Script
└── Chapter
    └── Sequence
        └── Scene Node
            └── Scene

UI 当前只暴露：

Script
→ Scene
→ Shot

用户不需要知道 ScriptNode。

5.3 Asset 模型

统一资产库：

Asset

关系：

Project N:N Asset
Shot    N:N Asset

通过：

ProjectAssetLink
ShotAssetLink

禁止复制成 Global / Project 两套实体。

5.4 Character 模型

Character 不是图片。

Character
└── CharacterState

例如：

女员工

├── 基础状态
├── 发帽+口罩
├── 黄色 PPE
├── 黄色 PPE + 双层手套
└── 退出状态

State 自己可以关联参考图片。

5.5 Storyboard

六宫格图片：

Asset
asset_type = STORYBOARD_6GRID

业务上同时建立：

Storyboard

默认：

1 个 Shot
→ 可有多个 Storyboard Version
→ 一个 selected
5.6 Prompt Template

两层：

GLOBAL
PROJECT

Category：

STORYBOARD_6GRID
VIDEO_GENERATION
CHARACTER_IMAGE
SCENE_IMAGE
IMAGE_REFERENCE
START_END_FRAME
OTHER
5.7 Prompt 输入

不是单纯自由文本框。

采用：

结构化字段
+
Free Notes

原因：

稳定
可复用
便于以后自动生成
便于 consistency check
5.8 PromptRecord

必须保存整个过程：

shot_id
template_id
prompt_type
user_requirement_json
raw_user_input
generated_content
edited_content
version
is_selected
provider
model_name
created_at
updated_at

不能只保存最终文本。

5.9 AI Provider

第一版统一：

OpenAI-compatible

Settings：

API Base URL
API Key
Model

业务层只认：

AIProvider / AIService

不根据厂商名写业务逻辑。

5.10 未来生成 API

现在不做。

未来预留：

GenerationProvider

GenerationJob
├── IMAGE
└── VIDEO

目标：

PromptRecord
→ GenerationJob
→ Asset
5.11 Project Export

MVP 必须：

Project
→ Export
→ <ProjectName>.zip

至少包含：

project.json
assets/
prompts/
metadata/

以及：

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

API Key 默认不导出。

6. 下一步明确指令
任务 1 — 修复公共 Select 组件
在哪里做

首先在：

D:\GitHub_kyandi-i\AI_Web\frontend\src\components\ui\

定位当前 shadcn/Radix Select 公共实现。

同时搜索：

Select
SelectTrigger
SelectContent
SelectItem
SelectItemText
SelectItemIndicator

不要只给 Shot 页面单独打 CSS 补丁。

做什么

修复：

hover/focus/selected 文本遮挡
行高不统一
Item Indicator 压住文字
长状态文本堆叠
Trigger 与 Item 尺寸不一致

统一：

height
min-height
line-height
padding-left/right
vertical alignment
indicator reserved width

并在 Dark / Light 下验证。

验收标准
所有 Select Item 行高一致
hover 不遮挡
selected 不遮挡
indicator 不覆盖文字
Trigger 与菜单项视觉高度体系一致
Project / Shot 所有状态 Select 同步修好
lint/build PASS
现有 E2E PASS

必须提供 Dark + Light 截图。

任务 2 — 建立 Enum value → label 层
在哪里做

前端公共 UI/config/helper 层。

具体文件名以当前仓库结构为准，不允许在多个页面复制 mapping。

做什么

至少建立：

DRAFT -> Draft
ASSET_PREPARING -> Asset Preparing
STORYBOARD_PROMPT_READY -> Storyboard Prompt Ready
STORYBOARD_READY -> Storyboard Ready
VIDEO_PROMPT_READY -> Video Prompt Ready
VIDEO_GENERATING -> Video Generating
REVIEW -> Review
DONE -> Done

要求：

UI 显示 Label
API value 保持原枚举值

以后 AssetType / PromptType / TemplateCategory 继续复用同一设计方式。

验收标准

不得再在最终 UI 中看到：

STORYBOARD_PROMPT_READY
VIDEO_PROMPT_READY

但后端提交值仍完全不变。

任务 3 — Phase 2.5 表单与列表一致性回归
在哪里做

当前已实现的：

Projects
Script
Scenes
Shots
Shot Detail
Create/Edit Dialog/Sheet
做什么

统一检查：

Input / Select / Textarea / Button 高度

Dialog/Sheet footer

Cancel / Save 位置

Save loading / disabled

Delete confirmation

List row height

Badge

Search / Filter

Move Up / Move Down

Loading
Empty
Error
验收标准

必须截图：

Dark：
- Status Select
- Project Form
- Scene Form
- Shot List
- Shot Edit

Light：
- Status Select
- Project Form
- Scene Form
- Shot List
- Shot Edit

所有已有 CRUD/E2E 不回归。

任务 4 — Phase 2.5 完成后暂停
在哪里做

整个项目开发流程。

做什么

提交完成报告：

修改内容
公共组件
截图
lint/build
frontend tests
backend tests
browser tests
commit hash
git status
验收标准
Git clean
用户确认 UI 问题已解决

不要自动进入 Phase 3。

任务 5 — 用户确认后开始 Phase 3 Asset Library
在哪里做

预计：

backend/app/models/
backend/app/repositories/
backend/app/services/assets/
backend/app/api/routes/

frontend/src/features/assets/
frontend/src/components/

实际目录以仓库当前结构为准。

做什么

实现：

Asset Model
AssetType
Upload
Managed Storage copy
Metadata
Thumbnail
Grid/List
Search
Type Filter
Tag
DetailSheet
ProjectAssetLink
ShotAssetLink
验收标准

必须能用真实 SPF 项目素材完成：

导入人物图
导入场景图
导入道具图
导入视频
搜索
筛选
预览
绑定 Project
绑定 Shot
刷新后保持

测试数据不得写入真实 Workspace。

7. 原始产物附录
7.1 当前核心领域关系
Workspace

├── Project
│   ├── Script
│   │   └── ScriptNode
│   │       └── Scene
│   │           └── Shot
│   │
│   ├── ProjectAssetLink
│   └── ProjectTemplateLink
│
├── Asset
│
├── Character
│   └── CharacterState
│
├── PromptTemplate
│
└── AIProviderConfig

Shot：

Shot

├── Assets
├── CharacterStates
├── Storyboards
├── PromptRecords
├── VideoResults
└── Notes
7.2 Phase 2 当前核心字段
Project
id UUID

name
description

status

created_at
updated_at
deleted_at

Status：

DRAFT
ACTIVE
PAUSED
COMPLETED
ARCHIVED
Script
id UUID

project_id

name
description

created_at
updated_at
deleted_at
ScriptNode
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

node_type：

CHAPTER
SEQUENCE
SCENE
OTHER
Scene
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

约束：

Scene.script_node must be node_type=SCENE
Scene Project == ScriptNode.Script.Project
Shot
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

created_at
updated_at
deleted_at

Shot Status：

DRAFT
ASSET_PREPARING
STORYBOARD_PROMPT_READY
STORYBOARD_READY
VIDEO_PROMPT_READY
VIDEO_GENERATING
REVIEW
DONE

唯一约束：

project_id + shot_code
7.3 当前 Status UI 映射要求
DRAFT
→ Draft

ASSET_PREPARING
→ Asset Preparing

STORYBOARD_PROMPT_READY
→ Storyboard Prompt Ready

STORYBOARD_READY
→ Storyboard Ready

VIDEO_PROMPT_READY
→ Video Prompt Ready

VIDEO_GENERATING
→ Video Generating

REVIEW
→ Review

DONE
→ Done

后端 value 不得改变。

7.4 当前 Phase 2 API 最低契约

实际实现细节以当前 FastAPI /openapi.json 为最终准绳，但开发规格要求至少存在：

Projects
GET    /api/projects
POST   /api/projects
GET    /api/projects/{id}
PATCH  /api/projects/{id}
DELETE /api/projects/{id}

示例 Create：

{
  "name": "SPF屏障设施培训视频",
  "description": "实验动物屏障设施新员工培训",
  "status": "DRAFT"
}
Scripts
GET    /api/projects/{project_id}/scripts
POST   /api/projects/{project_id}/scripts
GET    /api/scripts/{id}
PATCH  /api/scripts/{id}
DELETE /api/scripts/{id}

示例：

{
  "name": "设施区域进出流程",
  "description": "SPF培训主流程"
}
Scenes
GET    /api/projects/{project_id}/scenes
POST   /api/projects/{project_id}/scenes
GET    /api/scenes/{id}
PATCH  /api/scenes/{id}
DELETE /api/scenes/{id}

创建 Scene 时 Service 必须同一事务：

begin

check Project
check Script belongs Project
calculate order
create ScriptNode(type=SCENE)
create Scene

commit

失败：

rollback

不得产生 orphan ScriptNode。

概念输入：

{
  "script_id": "<uuid>",
  "name": "风淋室",
  "description": "二更与核心区之间的风淋空间",
  "fixed_constraints": "两扇门位于前后两端，喷嘴位置固定",
  "negative_constraints": "两门不得同时开启"
}
Shots
GET    /api/projects/{project_id}/shots
GET    /api/scenes/{scene_id}/shots
POST   /api/scenes/{scene_id}/shots
GET    /api/shots/{id}
PATCH  /api/shots/{id}
DELETE /api/shots/{id}

概念输入：

{
  "shot_code": "S13",
  "title": "风淋",
  "description": "人物从二更进入风淋室并进入核心区",
  "duration_seconds": 10,
  "status": "DRAFT",
  "creative_requirement": "风淋两门严格互锁，人物不得正对镜头"
}

排序：

Move Up / Move Down

由后端维护 order_index，前端不自行决定最终顺序。

7.5 API Error Schema

统一：

{
  "code": "ERROR_CODE",
  "message": "Human readable message",
  "details": {}
}

已规划的重要 code：

PROJECT_NOT_FOUND
SCRIPT_NOT_FOUND
SCENE_NOT_FOUND
SHOT_NOT_FOUND
SHOT_CODE_CONFLICT
INVALID_PROJECT_RELATION
ASSET_IN_USE
WORKSPACE_INVALID
FILE_NOT_FOUND

前端不得只显示：

500 Internal Server Error
7.6 Phase 2.5 完整 UX Fix 清单

以下为最近一次确定的完整 Phase 2.5 范围；其余业务逻辑不变。

1. Select / 枚举组件统一

修复 Status Select：

hover
focus
selected

遮挡、重叠、错位。

要求：

Trigger
Item
Indicator

高度、padding、文字位置稳定。

建立：

value → label

禁止把机器枚举直接显示给用户。

2. Input / Textarea / Select / Button 尺寸体系统一

检查：

Project
Scene
Shot

Create/Edit 表单。

统一：

height
font
radius
padding
focus
disabled

Textarea 使用单独多行规格。

3. Dialog / Sheet 表单布局统一

统一：

Title
Description
Form
Footer

所有：

取消
保存

顺序与位置一致。

保存时：

button disabled
clear loading feedback

避免重复请求。

4. 删除操作统一

Project / Script / Scene / Shot：

统一 confirmation

特别是删除 Scene 时必须明确：

Scene
+
对应 ScriptNode
+
child Shots

会 soft delete。

5. 列表与行高统一

Script / Scenes / Shots：

row height
vertical alignment
Badge
action buttons
long title truncation

不能 hover 后产生 layout shift。

6. Status Badge / Label 统一

建立唯一 config：

label
variant
optional icon

页面不得各自显示不同样式。

7. Loading / Empty / Error

每个异步页面：

Skeleton
EmptyState
ErrorState

不能白屏。

8. Navigation

验证：

Project Overview
→ Script
→ Scene
→ Shot

入口明显。

点击 Entity 行时：

Edit/Delete button

不得误触父级导航。

重点：

从“想到 S13”到“打开 S13”必须足够短。

9. Search / Filter / Order

Shots：

Search
Scene Filter
Status Filter

尺寸统一。

空结果显示 EmptyState。

第一个 Shot：

Move Up disabled

最后一个：

Move Down disabled

排序后 UI 立即稳定反映。

10. Dark / Light + Laptop width

全页面在：

Dark
Light
普通笔记本宽度

检查：

Select overflow
Dialog clipping
long enum
long title
Sidebar/main workspace

暂不要求完整 Mobile UX。

7.7 当前未解决 Bug 原文

用户描述：

“在状态栏处有很大问题，鼠标悬停在选项处会出现如图遮挡选项的问题，而且选中状态与实际的选项栏目每一行行高不一样，如图选中状态的行高就不一样”

没有收到 JS exception / Python traceback。

已有证据

问题表现只发生在下拉菜单渲染/hover/selected：

DRAFT
STORYBOARD_PROMPT_READY
STORYBOARD_READY
VIDEO_PROMPT_READY
VIDEO_GENERATING
REVIEW

Phase 2 同时：

backend 81/81 PASS
CRUD 可用
浏览器 build/dev tests PASS

因此当前首先排查：

frontend common Select / Radix layout CSS

而不是重新修改后端枚举或数据库。

已排除/不应重复排查
不是多个图标库冲突：
审计确认只有 lucide-react

不是远程图标/CDN：
没有相关依赖

不是重复 dev server：
资源审计未发现重复服务

不是整体后端 CRUD 崩溃：
Phase 2 backend 81/81 已通过

尚未证明具体是哪条 CSS 导致，因此接手 AI 必须实际检查 DOM / computed styles。

7.8 当前 UI Token
Dark

Background  #111517
Panel       #191F23
Card        #20272C
Accent      #53D9B0
Light

Background  #F2F5F6
Panel       #FFFFFF
Card        #F7F9FA
Accent      #087B61

设计关键词：

Premium
Dark
Professional
Compact
Focused
Creative
Production
Modern

避免：

Marketing
Cute
Huge White Space
Colorful Dashboard
Gaming Neon
7.9 资源审计 baseline
项目
D:\GitHub_kyandi-i\AI_Web
256.06 MiB content
276.72 MiB allocated
项目内部
frontend/node_modules   184.90 MiB
backend/.venv            69.64 MiB
frontend/dist              0.482 MiB
C 盘主要项
C:\Users\Lenovo\AppData\Local\ms-playwright
≈ 1,403.05 MiB

其中当前项目 Phase 0 版本：

chromium-1243                 431.92 MiB
chromium_headless_shell-1243 270.10 MiB

旧版本：

chromium-1234                 426.69 MiB
chromium_headless_shell-1234 270.75 MiB

旧版本可能属于其他项目，禁止直接删除。

Shared Python
C:\Users\Lenovo\AppData\Roaming\uv\python
≈ 61.54 MiB
当时真实 Workspace
C:\Users\Lenovo\AI-Video-Workspace
24 KiB
已在 D 的缓存
D:\study\DO\DevCache\npm
≈ 907.89 MiB

D:\study\DO\DevCache\uv
≈ 75.32 MiB

D:\study\DO\DevCache\pip
≈ 19.29 MiB

D:\study\DO\DevCache\pnpm-store
≈ 11.56 MiB

这些是多项目共享，不得全部算到 AI_Web。

7.10 图标 / shadcn 审计

Phase 1.5 前：

lucide-react 0.468.0
安装目录 ≈ 27.25 MiB

注意：

这不是生产网页加载 27MB。

当时生产 build：

JS   472.72 KiB
gzip 147.94 KiB

CSS   20.37 KiB
gzip   5.54 KiB

Phase 1.5 后用户报告：

gzip ≈ 198 kB

仍属可接受范围。

当时识别：

≈ 19 个图标定义
34 个 SVG 实例

当前策略正确：

lucide-react
+
named imports
+
tree shaking
+
no CDN/API

shadcn 采用：

源码复制进 frontend/src/components/ui/

不是一整个重型运行时框架。

Phase 1.5 前明确存在：

frontend/src/components/ui/button.tsx
frontend/components.json
7.11 当前相关路径

项目：

D:\GitHub_kyandi-i\AI_Web

已知：

D:\GitHub_kyandi-i\AI_Web\frontend
D:\GitHub_kyandi-i\AI_Web\frontend\node_modules
D:\GitHub_kyandi-i\AI_Web\frontend\dist
D:\GitHub_kyandi-i\AI_Web\frontend\src\components\ui\button.tsx
D:\GitHub_kyandi-i\AI_Web\frontend\components.json
D:\GitHub_kyandi-i\AI_Web\frontend\test-results

D:\GitHub_kyandi-i\AI_Web\backend
D:\GitHub_kyandi-i\AI_Web\backend\.venv
D:\GitHub_kyandi-i\AI_Web\backend\app
D:\GitHub_kyandi-i\AI_Web\backend\tests

D:\GitHub_kyandi-i\AI_Web\.workspace\e2e\workspace\data\workspace.db

D:\GitHub_kyandi-i\AI_Web\README.md
D:\GitHub_kyandi-i\AI_Web\DEVELOPMENT_STATUS.md

测试 Workspace：

D:\GitHub_kyandi-i\AI_Web\.workspace\e2e\workspace

真实 Workspace（审计时）：

C:\Users\Lenovo\AI-Video-Workspace
7.12 被修改文件恢复方式

对话没有包含 bf2113b 和 71d25ba 的完整 Git file list，因此禁止编造“所有被修改文件”。

接手后第一件事执行：

git status --short

git show --name-status bf2113b

git show --name-status 71d25ba

需要进一步理解代码：

git show --stat bf2113b
git show --stat 71d25ba

已知：

文件	修改原因	当前测试状态
README.md	各 Phase 更新运行/开发说明	Phase 2 验证 PASS
DEVELOPMENT_STATUS.md	记录阶段验收、状态	Phase 2 已更新
frontend/src/components/ui/button.tsx	shadcn Button 基础组件（审计明确存在）	Phase 2 frontend PASS
frontend/components.json	shadcn 配置	Phase 2 frontend PASS

其余文件必须通过两个 commit 的 Git history 精确恢复。

7.13 Commit 状态

UI Foundation：

bf2113b

Phase 2：

71d25ba

Phase 2 完成报告明确：

Git working tree clean

Phase 2.5 尚无完成 commit。

7.14 开发阶段顺序

当前严格顺序：

Phase 0      ✅
Phase 1      ✅
Phase 1.5    ✅
Phase 2      ✅

Phase 2.5    ← NEXT

用户验收

Phase 3      Asset Library
Phase 4      Character / CharacterState
Phase 5      Shot Workspace

真实项目投入测试

Phase 6      Prompt Template
Phase 7      AI Prompt Generation
Phase 8      Prompt Version
Phase 9      Storyboard
Phase 10     Video Result
Phase 11     Export / Recycle Bin / UX

每个 Phase 完成：

运行项目
运行测试
检查 Migration
检查 Regression
更新 README
更新 DEVELOPMENT_STATUS
Git clean
报告结果
停止
等待用户确认

禁止自动连续开发下一阶段。

7.15 接手后的最低检查顺序

新的 AI 实例接手后应先：

1. cd D:\GitHub_kyandi-i\AI_Web

2. git status

3. git log --oneline -10

4. git show --name-status bf2113b

5. git show --name-status 71d25ba

6. 阅读：
   README.md
   DEVELOPMENT_STATUS.md
   package.json
   backend dependency config
   current Select component

7. 启动现有项目

8. 手动复现 Status Select bug

9. 检查 computed styles / DOM

10. 只执行 Phase 2.5

不要在复现问题之前重写 Select。

最终风险提示

如果以上信息与用户新提供的内容有矛盾，请先向用户确认，不要自行假设或编造缺失的细节。


资源占用数字来自用户提供的阶段审计报告。:contentReference[oaicite:0]{index=0}