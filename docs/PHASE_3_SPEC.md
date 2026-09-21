# Phase 3 用户开发要求

以下保存本轮授权原文。最终实现与验收以 DEVELOPMENT_STATUS.md 为准。

你现在接手项目：

`D:\GitHub_kyandi-i\AI_Web`

目标：**只完成 Phase 3 — Asset Library。**

当前 Phase 0、Phase 1、Phase 1.5、Phase 2、Phase 2.5 已全部完成。Phase 2.5 已完成 UX Fix 并通过验收前测试，现在正式进入 Phase 3。

不要进入 Phase 4，也不要提前实现 Character / CharacterState、Prompt、Storyboard 工作流等后续阶段。

---

# 一、开始前先确认当前仓库真实状态

先执行并阅读，不要直接修改代码：

```powershell
cd D:\GitHub_kyandi-i\AI_Web

git status --short
git log --oneline -10
```

然后阅读：

```text
README.md
DEVELOPMENT_STATUS.md
HANDOFF.md（如果仓库中存在）
frontend/package.json
lockfile
backend 的 pyproject.toml / dependency config
当前 Workspace / Storage 实现
当前 Repository / Service / Route 实现
Phase 2 Project / Scene / Shot 的前后端实现
Phase 2.5 已统一的公共 UI 组件
```

必须以当前仓库实际代码为准。

禁止猜：

* npm script 名称
* Python 包版本
* React / Vite / FastAPI 等具体版本
* 当前文件路径
* Phase 2.5 commit hash

如果文档与当前代码冲突，以：

**当前代码 + migration + tests**

为主要事实来源，同时记录差异。

在修改前确认 Git working tree 状态。

---

# 二、当前项目定位

这是一个：

**Local-first AI Video Production Workspace**

不是：

* SaaS Dashboard
* AI 聊天工具
* 在线图片生成器
* 在线视频生成器
* Premiere 式编辑器

核心业务流程：

```text
Project
→ Script
→ Scene
→ Shot
→ 绑定生产资产
→ 后续 Character / Prompt / Storyboard / Video Result
```

当前 MVP 不直接生成图片和视频。

Phase 3 的职责只是建立后续所有 AI 视频生产功能依赖的统一资产基础设施。

---

# 三、现有架构硬约束

不得擅自修改以下方向：

Frontend：

```text
React
TypeScript
Vite
Tailwind CSS
shadcn/ui
React Router
TanStack Query
Zod
```

Backend：

```text
Python
FastAPI
SQLAlchemy
Alembic
Pydantic
```

Database：

```text
SQLite
```

Storage：

```text
Managed Local Storage
```

所有核心实体：

```text
UUID
```

默认删除：

```text
Soft Delete
deleted_at
```

架构必须继续保持：

```text
Route
↓
Service
↓
Repository
```

Storage 必须继续：

```text
StorageService
↔ StorageProvider
```

禁止：

* Route 直接写 SQL
* 大型图片/视频写入 SQLite BLOB
* 只保存用户原始文件的绝对路径
* SQLite 改 PostgreSQL
* 引入 Redis / Celery / Event Bus / CQRS / 微服务
* 强制 Docker
* 引入 Next.js
* 改成 Electron/Tauri
* 引入新的大型状态管理框架
* 为 Phase 4+ 提前过度设计

---

# 四、Phase 3 已冻结的范围

Phase 3 固定为：

```text
Unified Asset Library
+
Managed Storage Import
+
Thumbnail
+
Grid / List
+
Search
+
Filter
+
Tag
+
Asset DetailSheet
+
ProjectAssetLink
+
ShotAssetLink
```

同时支持：

```text
Drag & Drop Upload
+
Normal File Picker
```

Phase 3 完成后暂停。

**不要自动进入 Phase 4。**

---

# 五、AssetType 已冻结

Phase 3 第一版只使用：

```text
IMAGE
VIDEO
STORYBOARD_6GRID
OTHER
```

不要增加：

```text
CHARACTER_IMAGE
SCENE_IMAGE
PROP_IMAGE
```

原因：

Character / Scene / Prop 属于业务用途，而不是文件的基础 AssetType。

同一个 Asset 后续可能：

* 被 CharacterState 使用
* 被 Shot 使用
* 被 Project 使用
* 作为参考图
* 作为 Storyboard

因此 Phase 3 不要把业务语义硬编码进 AssetType。

后续 Character / CharacterState 属于 Phase 4。

---

# 六、统一 Asset 模型

只建立一套：

```text
Asset
```

禁止设计成：

```text
GlobalAsset
ProjectAsset
ShotAsset
```

这种三套业务实体。

关系应为：

```text
Asset
↕
ProjectAssetLink
↕
Project
```

以及：

```text
Asset
↕
ShotAssetLink
↕
Shot
```

要求：

* 一个 Asset 可绑定多个 Project
* 一个 Asset 可绑定多个 Shot
* 同一个 Asset 不因为绑定不同业务实体而复制实际文件
* Project/Shot 删除不应该直接物理删除 Asset

---

# 七、Asset 字段设计

请先根据当前项目已有 Base Model / Timestamp / Soft Delete 约定设计 migration。

基础 Asset 至少需要支持：

```text
id UUID

name
asset_type

original_filename
stored_filename / storage path 信息

mime_type
file_size

width nullable
height nullable
duration_seconds nullable

created_at
updated_at
deleted_at
```

具体字段命名必须遵守当前项目代码风格。

Managed Storage 中只保存**相对 Workspace 的路径**。

例如概念上：

```text
storage/assets/<uuid>.<ext>
```

不要把：

```text
D:\Downloads\abc.png
```

这种原始绝对路径作为资产正式引用。

可以保存 original_filename。

如果当前系统已有 metadata JSON 的设计方式，可以在确认现有架构后合理复用，但不要为了“未来可能用到”无限扩展字段。

---

# 八、Managed Storage 导入规则

用户选择：

```text
D:\Downloads\character.png
```

系统应该：

```text
读取文件
→ 校验
→ 生成 UUID
→ 复制进入 Workspace Managed Storage
→ 写入 Asset 数据库记录
→ 原文件以后移动或删除，不影响 Asset
```

真实 Workspace 结构继续遵守现有 Workspace / Storage 设计。

不要重新设计 Workspace Root。

当前理念为：

```text
<workspace_root>/
├── data/
│   └── workspace.db
├── storage/
│   ├── assets/
│   ├── thumbnails/
│   └── temp/
├── exports/
└── backups/
```

实际实现请读取当前代码，不要假定目录已经一字不差存在。

---

# 九、上传能力

Phase 3 必须支持：

### 1. 普通文件选择

用户点击：

```text
Import Asset
```

选择图片或视频。

### 2. Drag & Drop

Asset Library 页面允许把文件拖入上传区域。

要求：

* 支持一次导入多个文件
* 显示明确上传/导入状态
* 防止重复提交
* 单个文件失败不应该造成整个页面崩溃
* 错误要使用当前统一 Error UI / Error Schema
* 不得只显示 `500 Internal Server Error`

如果目前 API Error Schema 已存在：

```json
{
  "code": "ERROR_CODE",
  "message": "Human readable message",
  "details": {}
}
```

继续复用。

---

# 十、文件类型处理

至少支持常见：

图片：

```text
png
jpg
jpeg
webp
```

视频：

```text
mp4
mov
webm
```

具体 MIME 判断不要单纯依赖前端扩展名。

后端必须做校验。

禁止假定所有用户文件都正确。

遇到不支持的文件：

* 返回明确错误
* 不写入正式 Asset
* 不留下残缺数据库记录
* 不留下无引用残余文件

---

# 十一、数据库与文件系统一致性

这一点非常重要。

必须认真处理：

```text
文件复制成功 + DB 失败
DB 写入成功 + 文件操作失败
thumbnail 失败
批量导入部分失败
```

不能形成大量 orphan file 或 broken Asset。

优先复用当前 Service transaction / Storage abstraction。

实现时明确设计失败回滚/清理策略。

不要让 Route 自己协调这些业务逻辑。

---

# 十二、Thumbnail

Phase 3 必须有缩略图能力。

IMAGE：

生成合理尺寸的缩略图。

VIDEO：

优先生成视频预览缩略图/首帧。

如果视频缩略图需要额外本地依赖：

**先检查当前机器/项目依赖。**

不要未经确认引入非常重的运行环境。

如果现有依赖不足，请选择最轻量、可维护、Local-first 的方案，并在最终报告明确说明新增依赖及原因。

Thumbnail 存入：

```text
Managed Storage
```

数据库保存相对路径。

禁止保存为 DB BLOB。

原始 Asset 和 Thumbnail 生命周期需要关联。

---

# 十三、Tag 模型

Phase 3 使用简单：

```text
Asset
N:N
Tag
```

Tag 至少：

```text
id UUID
name
created_at
...
```

根据当前项目规范决定是否加入 deleted_at。

需要防止无意义重复 Tag。

例如：

```text
SPF
女员工
人物
风淋室
参考图
客户原图
```

不要实现：

* Tag Group
* Nested Tag
* Tag Hierarchy
* AI Auto Tag
* Tag Permission

这些都不属于 Phase 3。

---

# 十四、Asset Library 页面

新增正式生产页面：

```text
Asset Library
```

UI 必须沿用 Phase 1.5 + Phase 2.5 已完成的设计体系。

视觉：

```text
Premium Black Workspace
Professional
Compact
High information density
Dark default
Light supported
Cyan/Green accent
```

禁止重新出现：

* Landing Page
* 营销 Hero
* 巨量留白
* 紫色主色
* Gaming Neon
* “Phase 3 Coming Soon”式产品页面

Asset Library 至少需要：

```text
Grid View
List View

Search

Asset Type Filter

Tag Filter / Tag UI

Import Asset

Drag & Drop

Loading
Empty
Error
```

Grid/List 切换状态是否持久化，可优先遵循当前应用已有 preference 机制；不要因此引入新复杂架构。

---

# 十五、Asset Card / List Row

Grid 卡片至少应该清楚显示：

```text
thumbnail
asset name
asset type
basic metadata
tags（适量）
```

视频资产应有明显视频识别。

不要在卡片中塞满所有 metadata。

List 模式适合显示更多：

```text
name
type
size
dimensions / duration
tags
updated time
```

长文件名：

```text
truncate
```

Hover 不能产生 layout shift。

复用 Phase 2.5 已经统一好的：

```text
Button
Badge
Select
Input
QueryState
Dialog / Sheet
```

不要复制新的同功能组件体系。

---

# 十六、Asset DetailSheet

点击 Asset 后打开：

```text
DetailSheet
```

尽量复用现有公共 `DetailSheet`。

至少显示：

```text
Preview

Name
Asset Type

Original Filename
File Size
MIME

Width / Height
或
Video Duration

Tags

Created At
Updated At

Projects using this asset
Shots using this asset
```

支持：

```text
Rename / Edit basic metadata
Tag management
Bind / Unbind Project
Bind / Unbind Shot
Soft Delete
```

是否允许修改 AssetType：

谨慎处理。

如果允许，只能修改业务分类字段，不能导致文件真实格式与 metadata 冲突。

不要为了方便直接把 MIME 与 asset_type 强耦合得无法处理 STORYBOARD_6GRID。

---

# 十七、ProjectAssetLink / ShotAssetLink

建立：

```text
ProjectAssetLink
ShotAssetLink
```

所有 ID 使用 UUID。

应该具有合理唯一约束，例如概念：

```text
project_id + asset_id UNIQUE
shot_id + asset_id UNIQUE
```

避免同一个关系重复绑定。

绑定动作需要经过 Service。

删除关系：

只删除/soft delete Link。

不要删除 Asset 本体。

---

# 十八、Asset 删除策略

当前应用统一原则：

```text
Delete
→ Soft Delete / Recycle Bin
```

Phase 3 至少必须实现：

```text
Asset soft delete
```

永久删除不需要提前实现完整 Recycle Bin 页面，那是 Phase 11。

但设计不得破坏未来永久删除。

特别注意：

Asset 被 Project / Shot 使用时：

不得静默物理删除文件。

如果当前产品策略允许 Soft Delete 被引用资产，需要保证引用页面不会因此产生严重 broken state。

如果涉及是否允许“被引用 Asset 直接 soft delete”的 UX 决策，而当前代码/文档没有明确答案：

**不要自行改变数据模型。**

优先采取安全且可恢复的实现，并在最终报告单独说明。

已有错误码规划：

```text
ASSET_IN_USE
```

可以按现有 Error Schema 合理接入。

---

# 十九、API

具体 endpoint 命名必须遵循当前 FastAPI 项目已有 API 风格，不要自行发明另一套 REST 风格。

至少需要覆盖能力：

```text
list assets
get asset
import/upload asset
update asset
soft delete asset

list/create/delete tags relation

bind/unbind Project
bind/unbind Shot
```

支持：

```text
search
asset type filter
tag filter
```

分页方式根据当前项目列表 API 风格决定。

不要为了 Phase 3 引入 GraphQL。

---

# 二十、搜索与筛选

Asset Library 至少支持：

### Search

匹配：

```text
asset name
original filename
```

如 Tag 查询可以自然加入，也可以通过 Tag Filter 单独处理。

### Asset Type Filter

```text
All
Image
Video
Storyboard 6-Grid
Other
```

UI 显示友好文案。

API value 继续：

```text
IMAGE
VIDEO
STORYBOARD_6GRID
OTHER
```

不要在 UI 直接显示：

```text
STORYBOARD_6GRID
```

延续 Phase 2.5 的 enum：

```text
value → label
```

公共映射设计。

---

# 二十一、Storyboard 6-Grid 当前只作为 AssetType

非常重要：

Phase 3 允许：

```text
AssetType = STORYBOARD_6GRID
```

但不要提前实现 Phase 9 的完整：

```text
Storyboard Entity
Storyboard Version
selected storyboard
source_prompt_record_id
```

Phase 3 只是让六宫格图片可以作为特殊资产进入 Library。

完整 Storyboard Workflow 属于 Phase 9。

---

# 二十二、不要实现 Character / CharacterState

Phase 4 才做：

```text
Character
└── CharacterState
```

例如：

```text
女员工
├── 基础状态
├── 发帽+口罩
├── 黄色 PPE
└── 黄色 PPE + 双层手套
```

Phase 3 不要：

* 创建 Character 表
* 创建 CharacterState 表
* 创建 Character Asset Binding
* 给 Asset 强行添加 character_id

Phase 3 要做的是给 Phase 4 提供稳定的 Asset 基础。

---

# 二十三、真实业务验收场景

Phase 3 完成后，必须能够使用真实 SPF AI 视频项目素材进行验证。

示例素材类型：

```text
人物参考图
人物四视图
场景参考图
道具图片
六宫格 Storyboard
AI 生成视频
```

真实业务流程必须能做到：

```text
导入人物图
→ Asset Library 可看到

导入场景图
→ 可 Search

导入道具图
→ 可 Tag

导入视频
→ 可预览/看到视频 metadata

导入六宫格
→ AssetType = STORYBOARD_6GRID

Asset
→ 绑定 SPF Project

Asset
→ 绑定某个 Shot

刷新页面
→ 绑定关系仍存在
```

注意：

自动化测试禁止污染真实 Workspace。

---

# 二十四、测试 Workspace 隔离

现有测试已经有隔离 Workspace 机制。

必须继续保持。

自动化测试产生的：

```text
DB
assets
thumbnails
temp files
```

全部只能存在测试 Workspace。

禁止写入用户真实 Workspace。

如果 Asset tests 会产生实际文件：

测试结束后合理清理。

必须验证测试不会修改真实生产素材。

---

# 二十五、测试要求

Phase 3 不是“页面能打开”就算完成。

至少补齐：

## Backend

测试：

```text
Asset create/import
Asset list
Asset detail
Asset update
Asset soft delete

image metadata
video metadata（如实现）

storage copy

duplicate/bad upload
unsupported file

Tag
AssetTag relation

ProjectAssetLink
ShotAssetLink

search
filters

transaction / cleanup cases
```

## Frontend / Browser

至少覆盖关键用户路径：

```text
open Asset Library

import image

asset appears

switch Grid/List

search

type filter

open DetailSheet

edit name

add/remove tag

bind Project

bind Shot

refresh

relation persists
```

如果浏览器测试不适合验证大视频文件，使用小型 deterministic fixture。

不要引入巨大的测试素材。

---

# 二十六、Migration

新数据库结构必须通过 Alembic。

必须实际验证：

```text
upgrade head
downgrade
upgrade head
```

不能只测试 fresh DB。

同时验证现有 Phase 2 数据升级后不丢失。

不要直接手改生产 workspace.db schema。

---

# 二十七、性能与资源

这是 Local-first 个人生产工具。

Asset Library 未来会出现大量高清图和视频。

因此：

* Grid 不要直接加载原始 4K 图片作为 thumbnail
* 列表不要一次解码所有视频
* Thumbnail 与 original 分离
* 图片预览合理 lazy load
* 视频不要自动全部播放
* 不要把 base64 大文件塞进 API JSON
* 不要把二进制塞数据库

同时不要过早做复杂虚拟列表，除非当前数量已经证明存在性能问题。

---

# 二十八、UI 验收

至少人工验证：

## Dark

```text
Asset Library Grid
Asset Library List
Import / Drop Zone
Asset DetailSheet
Search + Filter
Tags
Project binding
Shot binding
```

## Light

同上关键页面。

同时检查普通笔记本窗口尺寸：

```text
Sidebar
main content
filter bar
cards
DetailSheet
Dialog
long filename
long tag
```

不得出现：

```text
overflow
clipping
hover layout shift
text overlap
Select regression
```

尤其不要破坏 Phase 2.5 已经修好的 Select。

---

# 二十九、代码质量原则

优先：

```text
简单
明确
可维护
符合当前架构
```

不要：

```text
过度抽象
提前实现 Phase 4+
大型重构
更换成熟公共组件
为了“代码漂亮”重写稳定 Phase 2 功能
```

如果必须修改公共基础设施：

说明原因，并确保所有旧页面 regression tests PASS。

---

# 三十、完成后必须运行完整回归

以仓库当前真实脚本为准，至少完成：

```text
frontend lint

frontend build

backend tests

frontend/browser production/build tests

frontend/browser development tests

Alembic upgrade
Alembic downgrade
Alembic upgrade
```

Phase 2.5 最新已知基线：

```text
lint                         PASS
build                        PASS
browser production/build     22/22 PASS
browser development          24/24 PASS
backend                      81/81 PASS
migration regression         PASS
```

Phase 3 可以增加测试数量。

**不得低于已有测试覆盖，并且旧测试不能回归。**

---

# 三十一、文档

Phase 3 完成后更新：

```text
README.md
DEVELOPMENT_STATUS.md
```

记录：

```text
Phase 3 完成内容
Asset model
Managed Storage behavior
supported file types
AssetType
Tag
Project/Shot relation
Thumbnail behavior
运行/测试方式
测试结果
已知限制
```

不要把未来 Phase 4 功能写成已完成。

---

# 三十二、Git

完成前执行：

```text
git status
git diff
```

确保：

* 无临时测试文件
* 无误提交真实素材
* 无 `.env`
* 无 API Key
* 无测试 Workspace 垃圾
* 无用户本地文件
* 无大体积无用 binary

确认测试通过后创建 **一个清晰的 Phase 3 commit**。

Commit message 遵循当前仓库已有风格。

不要猜历史格式，先看：

```text
git log --oneline
```

---

# 三十三、Phase 3 最终验收标准

Phase 3 只有同时满足以下条件才算完成：

```text
✅ Asset Model
✅ AssetType

✅ Managed Storage import
✅ 图片导入
✅ 视频导入
✅ Multi-file import
✅ Drag & Drop
✅ Normal file picker

✅ Metadata
✅ Thumbnail

✅ Grid View
✅ List View

✅ Search
✅ Asset Type Filter

✅ Tag
✅ Asset DetailSheet

✅ ProjectAssetLink
✅ ShotAssetLink

✅ Soft Delete 基础

✅ Dark
✅ Light
✅ Laptop width

✅ Test Workspace isolation

✅ Existing Phase 2 / 2.5 regression PASS

✅ Alembic upgrade/downgrade PASS

✅ README updated
✅ DEVELOPMENT_STATUS updated

✅ Git clean
```

---

# 三十四、最终完成报告格式

完成 Phase 3 后，不要继续开发 Phase 4。

停下来给我报告：

## 1. Phase 3 完成内容

逐项说明实际完成的功能。

## 2. 数据模型

列出：

```text
Asset
Tag
AssetTag / equivalent
ProjectAssetLink
ShotAssetLink
```

以及关键关系。

## 3. Storage

说明：

```text
导入路径
文件命名
相对路径策略
thumbnail
失败回滚/清理
```

## 4. API

列出新增 API。

## 5. Frontend

列出：

```text
Asset Library
Grid/List
Import
DetailSheet
Search
Filter
Tag
Binding
```

## 6. Screenshot / UI 验证

提供关键 Dark / Light 截图或浏览器验证证据。

## 7. Tests

给出实际数字：

```text
lint
build
backend X/X
browser production X/X
browser development X/X
Alembic
```

不要只写“tests passed”。

## 8. 新增依赖

如果新增任何前端/Python/系统依赖：

逐项解释：

```text
名称
版本
用途
为什么需要
体积/运行影响
```

如果没有，写：

```text
No new dependency.
```

## 9. Git

提供：

```text
commit hash
git status
```

要求最终：

```text
working tree clean
```

## 10. 已知限制

只写真实存在的问题。

---

# 最后强调

本次任务只做：

**Phase 3 — Asset Library**

不要自动进入：

```text
Phase 4 Character / CharacterState
Phase 5 Shot Workspace
Phase 6 Prompt Template
Phase 7 AI Generation
Phase 8 Prompt Versioning
Phase 9 Storyboard Workflow
Phase 10 Video Result
Phase 11 Export / Recycle Bin
```

Phase 3 完成、测试全部通过、Git clean 后：

**停止开发，等待用户验收。**
