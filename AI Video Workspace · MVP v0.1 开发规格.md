# AI Video Workspace

版本：MVP v0.1  
产品形态：Local-first Web Application  
当前阶段：单用户本地版  
核心目标：尽快投入真实 AI 视频制作，同时保证后续多人协作、云存储和生成 API 的可扩展性。

---

# 1. 产品定位

AI Video Workspace 不是 AI 视频生成平台。

它是一个面向 AI 视频制作流程的：

**项目管理 + 剧本管理 + 场景管理 + 镜头管理 + 资产库 + Storyboard + Prompt 模板 + Prompt 生成 + Prompt 版本 + 视频结果管理工作台。**

当前 AI 图片和 AI 视频仍主要通过外部平台生成。

本应用负责：

```text
需求整理
→ 资产组织
→ 分镜管理
→ Prompt 生成
→ Prompt 版本管理
→ 外部生成
→ 生成结果重新导入
→ 资产关联
→ 镜头完成
```

后期可以逐步接入图像和视频生成 API。

---

# 2. MVP 核心原则

## 2.1 Local-first

所有核心数据默认保存在用户本机。

数据库：

```text
SQLite
```

图片、视频和附件：

```text
Managed Local Storage
```

数据库只保存文件元数据和路径，不把大型二进制文件直接写进 SQLite。

---

## 2.2 单用户优先，多用户可扩展

MVP 不实现：

```text
用户注册
登录
权限
多人实时协作
云同步
```

但数据模型中避免依赖“永远只有一个用户”的假设。

未来应允许扩展：

```text
Workspace
User
Team
ProjectMember
Role
Permission
```

---

# 3. 技术栈

## Frontend

```text
React
TypeScript
Vite
Tailwind CSS
shadcn/ui
```

建议：

```text
React Router
TanStack Query
Zod
React Hook Form
```

状态管理优先使用局部状态和 Query Cache。

除非确实出现复杂跨页面状态，否则 MVP 不优先引入大型全局状态管理库。

---

## Backend

```text
Python
FastAPI
SQLAlchemy
Alembic
Pydantic
```

---

## Database

```text
SQLite
```

SQLAlchemy 层必须保持 PostgreSQL 可迁移性。

禁止大量依赖 SQLite 特有语法。

---

# 4. 本地运行方式

应用启动方式：

```text
启动本地服务
↓
FastAPI Backend
↓
Vite / Build 后的 React Frontend
↓
自动打开浏览器
↓
http://localhost:<port>
```

第一版仍然是 Web 应用，不制作 Electron/Tauri Desktop Shell。

未来如有需要可以再增加 Desktop Wrapper。

---

# 5. Workspace 存储

用户在 Settings 中设置 Workspace Root。

例如：

```text
D:\AI-Video-Workspace\
```

系统负责自动建立内部目录。

推荐：

```text
AI-Video-Workspace/
├── data/
│   └── workspace.db
│
├── storage/
│   ├── assets/
│   ├── thumbnails/
│   └── temp/
│
├── exports/
│
└── backups/
```

不得要求用户手动维护内部 storage 结构。

---

# 6. 文件导入策略

采用 Managed Storage。

用户拖入：

```text
D:\Downloads\character.png
```

系统必须：

```text
读取文件
→ 计算基本元数据
→ 生成 UUID
→ 复制到 Workspace Storage
→ 创建 Asset 数据
→ 生成缩略图（适用时）
→ 返回 Asset
```

导入后不再依赖原始路径。

即使用户删除 Downloads 中的原文件，也不能影响应用中的 Asset。

---

# 7. UUID

所有核心实体使用 UUID。

包括：

```text
Project
Script
ScriptNode
Scene
Shot
Asset
Character
CharacterState
PromptTemplate
PromptRecord
Storyboard
VideoResult
Note
Tag
```

数据库内部禁止使用业务意义上的自增数字 ID 作为实体主键。

`S01`、`S15A` 等属于 `shot_code`，不是主键。

---

# 8. 核心领域模型

整体关系：

```text
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
```

Shot 为最核心制作单元：

```text
Shot

├── Assets
├── CharacterStates
├── Storyboards
├── PromptRecords
├── VideoResults
└── Notes
```

---

# 9. Project

Project 表示一个完整 AI 视频项目。

核心字段：

```text
id UUID

name
description

status

created_at
updated_at
deleted_at
```

状态 MVP 可以采用：

```text
DRAFT
ACTIVE
PAUSED
COMPLETED
ARCHIVED
```

---

# 10. Script

一个 Project 可以拥有一个或多个 Script。

核心字段：

```text
id

project_id

name
description

created_at
updated_at
```

---

# 11. ScriptNode

为了将来支持复杂视频结构，不直接把 Script 写死成：

```text
Script → Scene → Shot
```

底层使用树形 ScriptNode。

字段：

```text
id

script_id

parent_id nullable

node_type

title

description

order_index

created_at
updated_at
```

`node_type` 预留：

```text
CHAPTER
SEQUENCE
SCENE
OTHER
```

MVP 前端暂时主要展示：

```text
Script
→ Scene
→ Shot
```

未来可以增加：

```text
Script
→ Chapter
→ Sequence
→ Scene
→ Shot
```

而不需要重新设计数据库。

---

# 12. Scene

Scene 表示实际视频制作中的业务场景。

例如：

```text
一更
二更
风淋室
核心区连接走廊
缓冲区
```

Scene 不是单独一张图片。

字段建议：

```text
id

project_id
script_node_id nullable

name
description

fixed_constraints
negative_constraints

order_index

created_at
updated_at
deleted_at
```

其中：

`fixed_constraints`

用于保存：

```text
镜子位置
设备位置
门的位置
空间布局
固定设施
```

`negative_constraints`

用于保存：

```text
不可改变的内容
禁止出现的内容
```

---

# 13. Shot

Shot 是整个系统最重要的实体。

字段：

```text
id

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
```

`shot_code` 示例：

```text
S01
S02
S15A
S15B
```

状态：

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

---

# 14. 统一 Asset Library

所有资产进入统一 Asset Library。

不把 Asset 分成：

```text
Global Asset
Project Asset
```

而是：

```text
Asset
↕
ProjectAssetLink
↕
Project
```

同一个 Asset 可以用于多个 Project。

同一个 Asset 也可以用于多个 Shot。

---

# 15. Asset

字段建议：

```text
id

name

asset_type

description

storage_path
thumbnail_path

mime_type

file_size

width nullable
height nullable
duration_seconds nullable

checksum nullable

created_at
updated_at

deleted_at
```

---

# 16. AssetType

MVP 至少支持：

```text
CHARACTER_REFERENCE

CHARACTER_STATE_REFERENCE

SCENE_REFERENCE

PROP

EQUIPMENT

COSTUME

STORYBOARD_6GRID

STORYBOARD_OTHER

START_FRAME

END_FRAME

STYLE_REFERENCE

VIDEO_RESULT

OTHER
```

未来必须允许扩充 Asset Type，而不重构核心逻辑。

---

# 17. ProjectAssetLink

表示项目使用某个 Asset。

字段：

```text
id

project_id
asset_id

created_at
```

建立唯一约束：

```text
project_id + asset_id
```

---

# 18. ShotAssetLink

Shot 和 Asset 为多对多。

字段：

```text
id

shot_id
asset_id

role

order_index

created_at
```

`role` 示例：

```text
CHARACTER_REFERENCE

SCENE_REFERENCE

PROP_REFERENCE

STORYBOARD

START_FRAME

END_FRAME

STYLE_REFERENCE

OTHER
```

---

# 19. Character

Character 是业务实体，不等于图片 Asset。

例如：

```text
女员工
客户代表
实验员A
```

字段：

```text
id

name
description

created_at
updated_at
deleted_at
```

Character 可以绑定多个基础参考 Asset。

---

# 20. CharacterState

一个角色可以拥有很多状态。

例如：

```text
基础服装

发帽+口罩

黄色PPE

黄色PPE+双层手套

退出状态
```

字段：

```text
id

character_id

name
description

appearance_constraints

created_at
updated_at
deleted_at
```

CharacterState 可以关联多个参考 Asset。

---

# 21. ShotCharacterStateLink

一个 Shot 可以出现多个角色。

一个角色可以使用特定 CharacterState。

所以：

```text
Shot
N:N
CharacterState
```

字段：

```text
id

shot_id
character_state_id

order_index

created_at
```

---

# 22. Storyboard

Storyboard 是业务实体。

Storyboard 图片本身仍然是 Asset。

字段：

```text
id

shot_id
asset_id

storyboard_type

source_prompt_record_id nullable

version

is_selected

created_at
```

类型：

```text
GRID_6
GRID_9
SEQUENCE
SINGLE_FRAME
OTHER
```

MVP 最重要的是：

```text
GRID_6
```

六宫格默认绑定单个 Shot。

---

# 23. PromptTemplate

Prompt Template 必须支持：

```text
全局模板
项目专属模板
```

字段：

```text
id

name

scope

project_id nullable

category

description

template_content

created_at
updated_at
deleted_at
```

scope：

```text
GLOBAL
PROJECT
```

category：

```text
STORYBOARD_6GRID

VIDEO_GENERATION

CHARACTER_IMAGE

SCENE_IMAGE

IMAGE_REFERENCE

START_END_FRAME

OTHER
```

---

# 24. 六宫格 Prompt 工作流

用户进入 Shot。

填写结构化信息：

```text
人物

CharacterState

Scene

动作目标

镜头时长

关键约束

负面约束

Reference Assets

自由补充
```

之后选择：

```text
Prompt Template
```

系统将：

```text
结构化字段
+
Shot 信息
+
Scene 约束
+
CharacterState
+
Asset Description
+
用户自由补充
+
Template
```

发送给 AI。

AI 输出完整六宫格 Prompt。

---

# 25. PromptRecord

Prompt 不允许只保存最终文本。

必须保存整个生成过程。

字段：

```text
id

shot_id

template_id nullable

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
```

prompt_type：

```text
STORYBOARD_6GRID

IMAGE_REFERENCE

SCENE_IMAGE

CHARACTER_IMAGE

START_END_FRAME

VIDEO_GENERATION

OTHER
```

---

# 26. Prompt Version

同一个 Shot 的同类 Prompt 可以拥有多个版本。

例如：

```text
Storyboard Prompt

V1
V2
V3 ★
```

用户可以：

```text
查看
编辑
复制
重新生成
设为最终采用
```

必须提供高优先级按钮：

```text
复制 Prompt
```

以及：

```text
复制最终 Prompt
```

---

# 27. 六宫格图片导入

外部工具生成六宫格之后，用户可直接拖回应用。

系统自动执行：

```text
导入图片

→ Copy to Managed Storage

→ Create Asset

asset_type =
STORYBOARD_6GRID

→ Link Project

→ Link Shot

→ Create Storyboard

→ optionally link source PromptRecord
```

这样系统知道：

```text
哪个 Prompt
→ 生成了
→ 哪张六宫格
```

---

# 28. VideoResult

MVP 不需要记录复杂的视频生成参数。

当前只需要：

```text
id

shot_id
asset_id

version

note

is_selected

created_at
```

示例：

```text
V1
人物走路异常

V2
门方向错误

V3 ★
最终采用
```

视频本身作为：

```text
Asset
asset_type = VIDEO_RESULT
```

---

# 29. Note

MVP 支持 Shot Note。

字段：

```text
id

shot_id

content

created_at
updated_at
```

以后可以把 Note 抽象为多实体备注。

MVP 不必过度设计。

---

# 30. Tags

Asset 支持 Tag。

例如：

```text
PPE
风淋
一更
角色
人物
门
镜子
Seedance
六宫格
```

表：

```text
tags

asset_tags
```

必须支持：

```text
按名称搜索
按类型筛选
按 Tag 筛选
```

---

# 31. Soft Delete

所有重要实体优先使用 Soft Delete。

例如：

```text
deleted_at
```

删除操作：

```text
Delete
↓
Recycle Bin
↓
Restore

或者

Permanent Delete
```

永久删除必须再次确认。

---

# 32. Asset Permanent Delete

删除 Asset 时必须检查引用。

例如 Asset 被：

```text
Project
Shot
Storyboard
CharacterState
VideoResult
```

引用时，不允许静默物理删除。

必须显示引用情况。

永久删除确认后：

```text
删除业务关系
↓
删除数据库 Asset
↓
删除 storage 文件
↓
删除 thumbnail
```

---

# 33. Project Export / Backup

MVP 必须支持 Project Export。

入口：

```text
Project
→ Export
```

输出：

```text
<ProjectName>.zip
```

ZIP 至少包含：

```text
project.json

assets/
prompts/
metadata/
```

或者其他等价的可恢复格式。

导出格式必须包含：

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
```

以及当前项目实际引用的本地文件。

---

# 34. Project Import

如果时间允许，MVP 末期实现 Import。

如果第一阶段开发进度受到影响，可以先完成 Export，再在后续 Phase 补 Import。

但 Export 数据格式必须从第一天按未来可 Import 的方向设计。

---

# 35. AI Provider

禁止在业务代码中散落具体模型 API 调用。

统一：

```text
AIProvider
```

业务层调用：

```text
AIService
```

例如：

```text
generate_prompt()

rewrite_prompt()

fill_template()
```

---

# 36. OpenAI-Compatible Provider

MVP 第一版支持 OpenAI-compatible 接口。

Settings：

```text
API Base URL

API Key

Model
```

例如可以适配：

```text
OpenAI
DeepSeek compatible endpoint
其他 OpenAI-compatible API
```

业务层禁止判断具体厂商名称。

---

# 37. AI Key 安全

API Key 不应该明文写入普通项目数据导出。

MVP 可以使用本地配置存储。

在 UI 中：

```text
sk-••••••••••••
```

提供：

```text
更新
测试连接
```

Export Project 时默认不导出 API Key。

---

# 38. Image Generation Future Extension

MVP 不实现图片生成。

但未来必须支持：

```text
PromptRecord
↓
Image Generation
↓
Asset
```

未来接口建议：

```text
GenerationProvider
```

类型：

```text
IMAGE
VIDEO
```

未来可增加：

```text
GenerationJob
```

字段方向：

```text
id

generation_type

prompt_record_id

provider

model

status

output_asset_id

created_at
completed_at
```

MVP 暂时可以不创建该表，但不要设计出阻碍它加入的代码结构。

---

# 39. 页面信息架构

全局导航：

```text
Dashboard

Projects

Asset Library

Characters

Prompt Templates

Settings
```

---

# 40. Project 页面

进入一个 Project 后：

```text
Overview

Script

Scenes

Shots

Assets

Prompt Templates
```

---

# 41. Dashboard

MVP Dashboard 只需要：

```text
最近项目

项目状态

最近修改的 Shot

当前项目进度
```

禁止第一版做复杂数据分析 Dashboard。

---

# 42. Assets 页面

要求：

```text
Grid View

List View

Search

Asset Type Filter

Tag Filter

Preview
```

支持：

```text
拖入图片

拖入视频

批量导入
```

点击 Asset 打开 Detail Panel。

Detail 至少显示：

```text
Preview

Name

Type

Description

Tags

Used By Projects

Used By Shots

File metadata
```

---

# 43. Characters 页面

展示：

```text
Character

→ Character States
```

例如：

```text
女员工

├── 基础状态
├── 二更状态
├── PPE状态
└── 退出状态
```

点击 State 可以查看所有关联参考 Asset。

---

# 44. Script 页面

第一版 UI：

```text
Script

Scene

Shot
```

支持排序。

支持：

```text
新增 Scene

新增 Shot

编辑

删除

拖动排序
```

如果拖动排序开发复杂，可以先提供：

```text
上移
下移
```

然后后期加 DnD。

---

# 45. Shots 页面

提供 Shot 列表。

显示：

```text
Shot Code

Title

Scene

Duration

Status

Storyboard Status

Video Status
```

支持：

```text
Search

Scene Filter

Status Filter
```

点击进入：

```text
Shot Workspace
```

---

# 46. Shot Workspace

这是 MVP 最重要页面。

必须优先保证易用。

推荐布局：

```text
Header

S13 风淋
10s
Status
```

主要区域：

```text
Storyboard Preview

Prompt Panel

References

Character / CharacterState

Scene

Assets

Structured Prompt Input

Start Frame

End Frame

Video Results

Notes
```

---

# 47. Structured Prompt Input

六宫格 Prompt 和视频 Prompt 不应只提供一个自由文本框。

至少支持：

```text
Characters

Character States

Scene

Main Action

Duration

Key Constraints

Negative Constraints

Reference Assets

Free Notes
```

这些数据最终保存到：

```text
user_requirement_json
```

自由文本保存到：

```text
raw_user_input
```

---

# 48. Prompt Template 页面

模板支持：

```text
Global

Project
```

支持：

```text
创建

编辑

复制

删除

筛选 Category
```

Template 编辑器至少支持纯文本。

MVP 不做复杂可视化模板编辑器。

变量可以先采用：

```text
{{shot.title}}

{{shot.duration}}

{{scene.constraints}}

{{characters}}

{{references}}

{{user.requirement}}

{{negative_constraints}}
```

实际变量集合在开发中统一定义，禁止页面和后端各自维护一套。

---

# 49. Settings

Settings 至少包含：

```text
Workspace Root

AI Base URL

AI API Key

AI Model

Test Connection
```

Workspace Root 修改必须进行路径合法性检查。

修改 Workspace Root 时，不得静默丢失已有 Workspace。

第一版推荐：

```text
修改 Root = 切换 Workspace
```

而不是自动移动全部文件。

如果用户要求迁移 Workspace，应提供独立迁移功能，MVP 可暂不实现。

---

# 50. Frontend 推荐结构

```text
frontend/

src/
├── app/
│   ├── router/
│   └── providers/
│
├── components/
│   ├── ui/
│   ├── layout/
│   └── common/
│
├── features/
│   ├── projects/
│   ├── scripts/
│   ├── scenes/
│   ├── shots/
│   ├── assets/
│   ├── characters/
│   ├── prompts/
│   ├── templates/
│   └── settings/
│
├── api/
│
├── hooks/
│
├── lib/
│
├── types/
│
└── main.tsx
```

按 feature 划分，不要建立巨大：

```text
components/
```

然后把所有业务组件都扔进去。

---

# 51. Backend 推荐结构

```text
backend/

app/
├── main.py
│
├── api/
│   ├── dependencies.py
│   └── routes/
│
├── core/
│   ├── config.py
│   ├── database.py
│   └── exceptions.py
│
├── models/
│
├── schemas/
│
├── repositories/
│
├── services/
│   ├── storage/
│   ├── ai/
│   ├── export/
│   └── assets/
│
├── migrations/
│
└── tests/
```

严格避免：

```text
route
→ 直接SQL
→ 直接文件操作
→ 直接AI调用
```

应该：

```text
Route
↓
Service
↓
Repository / Provider
```

---

# 52. Storage 抽象

必须存在：

```text
StorageProvider
```

接口方向：

```text
save_file()

delete_file()

move_file()

get_file()

exists()

create_thumbnail()
```

第一版：

```text
LocalStorageProvider
```

未来：

```text
S3StorageProvider

MinIOStorageProvider

OSSStorageProvider
```

业务逻辑不能拼接具体磁盘绝对路径。

---

# 53. Repository

数据库访问尽量通过 Repository。

例如：

```text
ProjectRepository

AssetRepository

ShotRepository

PromptRepository
```

目的不是为了过度架构，而是避免 API Route 和 SQLAlchemy 紧密耦合。

---

# 54. API 初步规划

推荐 REST API。

例如：

```text
/api/projects

/api/scripts

/api/scenes

/api/shots

/api/assets

/api/characters

/api/character-states

/api/prompt-templates

/api/prompts

/api/video-results

/api/settings
```

---

# 55. Asset API

至少：

```text
POST /assets/upload

GET /assets

GET /assets/{id}

PATCH /assets/{id}

DELETE /assets/{id}

POST /assets/{id}/restore

DELETE /assets/{id}/permanent
```

---

# 56. Shot API

至少：

```text
GET /shots

POST /shots

GET /shots/{id}

PATCH /shots/{id}

DELETE /shots/{id}
```

以及：

```text
POST /shots/{id}/assets

DELETE /shots/{id}/assets/{asset_id}
```

---

# 57. Prompt API

至少：

```text
POST /shots/{shot_id}/prompts/generate

GET /shots/{shot_id}/prompts

GET /prompts/{id}

PATCH /prompts/{id}

POST /prompts/{id}/select
```

重新生成应创建新 PromptRecord Version。

不要覆盖历史版本。

---

# 58. Export API

例如：

```text
POST /projects/{id}/export
```

返回生成后的 ZIP。

---

# 59. 错误处理

所有 API 错误统一返回可读错误结构。

例如：

```json
{
  "code": "ASSET_IN_USE",
  "message": "Asset is currently referenced by 3 shots.",
  "details": {}
}
```

前端不能只弹：

```text
500 Internal Server Error
```

---

# 60. MVP 非目标

第一版不要开发：

```text
用户系统

多人协作

实时同步

在线聊天

在线图片生成

在线视频生成

Premiere式时间轴

在线视频编辑

复杂版本分支

评论系统

审批流

权限系统

移动端适配优先

插件市场

SaaS计费
```

---

# 61. 开发 Phase

| Phase | 内容 | 验收标准 |
|---|---|---|
| 0 | 项目初始化 | 前后端均能启动 |
| 1 | DB + Alembic + Storage 抽象 | SQLite Schema 可迁移，文件可安全存储 |
| 2 | Project / Script / Scene / Shot | 可以创建完整项目层级 |
| 3 | Asset Library | 可拖入图片/视频、复制存储、预览和搜索 |
| 4 | Character / CharacterState | 可以建立角色状态并绑定 Asset |
| 5 | Shot Workspace | 能在一个页面完整管理单个 Shot |
| 6 | Prompt Template | Global / Project Template 可管理 |
| 7 | AI Prompt Generation | 结构化需求可以生成 Prompt |
| 8 | Prompt Versioning | 可查看、编辑、复制、采用不同版本 |
| 9 | Storyboard Workflow | 六宫格可导入并关联来源 Prompt |
| 10 | Video Result | 视频可导入、版本化、备注和最终采用 |
| 11 | Export / Recycle Bin / UX | 可以实际长期使用 |

---

# 62. 第一可用版本

不要等 Phase 11 才开始使用。

当：

```text
Phase 5
```

完成时，就应该使用真实 AI 视频项目测试。

之后采用：

```text
开发
→ 实际使用
→ 发现问题
→ 修正
```

的方式继续。

---

# 63. Agent 开发规则

Agent 每次只完成当前 Phase。

不要提前一次性实现整个系统。

每完成一个 Phase 必须：

```text
运行项目

运行测试

检查数据库迁移

检查已有功能没有破坏

更新 README

更新 CHANGELOG 或 DEVELOPMENT_STATUS
```

---

# 64. Agent 禁止事项

未经确认禁止：

```text
更换技术栈

加入 Next.js

加入 Electron

加入 Docker 作为强制运行条件

将 SQLite 改成 PostgreSQL

改变 Storage 策略

删除 Repository / Service 边界

把文件存进数据库

自行加入用户系统

自行加入云服务

自行加入图片或视频生成 API
```

---

# 65. 可扩展性原则

MVP 的“可扩展”不是加入大量未来功能。

而是保持清晰边界：

```text
AIService
↔ AIProvider

StorageService
↔ StorageProvider

Business Service
↔ Repository

Asset
↔ Project / Shot relation

Prompt
↔ Template

Prompt
↔ future GenerationJob
```

---

# 66. 第一阶段真正要优化的体验

优先级最高的是：

```text
快速找到资产

快速绑定资产到 Shot

快速填写镜头需求

快速生成六宫格 Prompt

快速复制 Prompt

快速导入六宫格

快速生成视频 Prompt

快速复制视频 Prompt

快速导入结果

快速切换到下一个 Shot
```

任何不能改善这些动作的功能，在 MVP 中都属于低优先级。

---

# 67. MVP 成功标准

当用户能够完成下面全过程时，MVP 达成：

```text
创建 AI 视频项目

→ 创建 Script

→ 创建 Scene

→ 创建 Shot

→ 导入人物 / 场景资产

→ 建 CharacterState

→ 绑定 Shot

→ 填写六宫格需求

→ 调用 LLM 生成六宫格 Prompt

→ 一键复制 Prompt

→ 外部生成六宫格

→ 拖回系统

→ 六宫格自动成为 Storyboard Asset

→ 生成视频 Prompt

→ 一键复制视频 Prompt

→ 外部生成视频

→ 视频拖回系统

→ 保存 V1/V2/V3

→ 填写备注

→ 选择最终版本

→ Shot 标记 DONE
```

完成这一闭环后，再考虑更多功能。

---

# 68. 当前决策状态

以下内容已经冻结：

```text
Local-first Web Application

React
TypeScript
Vite

FastAPI
SQLAlchemy
Alembic

SQLite

Tailwind CSS
shadcn/ui

Managed Local Storage

可修改 Workspace Root

UUID

统一 Asset Library

Project / Asset 多对多

Shot / Asset 多对多

CharacterState

Script → Scene → Shot UI

底层预留 Chapter / Sequence

Global + Project Prompt Templates

结构化 Prompt Input

六宫格 Prompt Generation

Prompt History

Prompt Versioning

Storyboard Asset

OpenAI-Compatible AI Provider

Recycle Bin / Soft Delete

Project ZIP Export

未来 Image / Video API 扩展接口
```

除非真实使用过程中发现明显问题，否则 Agent 不应修改这些核心决策。