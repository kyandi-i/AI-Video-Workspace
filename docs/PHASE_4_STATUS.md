# Phase 4 — Character / CharacterState 验收

日期：2026-09-23。基线 `6456839`，开始时 working tree clean。本阶段仅角色身份、视觉状态、参考素材与镜头状态关系；不进入 Phase 5。

## 数据模型

五张表均继承现有 BaseModel：`id UUID`、`created_at`、`updated_at`、`deleted_at`，时间为 UTC。所有关系使用外键并给查询外键加索引。

| 模型 / 表 | 业务字段 | 唯一约束 / 检查 |
| --- | --- | --- |
| Character / characters | project_id、name String(255)、description Text、notes Text nullable | project_id + name；name 非空 |
| CharacterState / character_states | character_id、name String(255)、description Text、order_index Integer | character_id + name；name 非空、order_index >= 0 |
| CharacterAssetLink / character_asset_links | character_id、asset_id | character_id + asset_id |
| CharacterStateAssetLink / character_state_asset_links | character_state_id、asset_id | character_state_id + asset_id |
| ShotCharacterStateLink / shot_character_state_links | shot_id、character_state_id、character_id | shot_id + character_state_id；active 记录的 shot_id + character_id 部分唯一索引 |

ShotCharacterStateLink.character_id 由 Service 从 State 推导，不接受客户端提交；用于数据库兜底同镜头同角色只能有一个 active 状态。Shot 表没有新增单值 character_state_id。UUID、软删除关联和重复绑定幂等沿用 Phase 3。

名称去除首尾空白，区分大小写，已删除名称仍保留占用，与现有 ShotCode 一致。不额外引入 normalized_name、结构化人物属性、封面字段或新 Tag 系统。notes 可显式置 null；其他更新字段显式 null / 未知字段返回现有 422 结构。

## 业务规则与事务

- Character 属于 Project；State 继承 Character 项目范围。搜索匹配 name / description。
- State 创建由服务端追加；移动返回最终顺序，边界移动不变；删除后连续重排，单独恢复追加末尾。
- Shot / State 同项目检查，不同项目返回 `INVALID_PROJECT_RELATION`。同角色不同状态返回 `SHOT_CHARACTER_STATE_CONFLICT`，同状态重复绑定幂等，不同角色可同时绑定。
- 所有写入沿用 atomic savepoint + Workspace session commit/rollback。既有单进程 Workspace lease 将请求串行至提交；关系唯一约束与 active 部分索引提供数据库保护。
- 新增明确错误：`CHARACTER_NOT_FOUND`、`CHARACTER_STATE_NOT_FOUND`、`CHARACTER_NAME_CONFLICT`、`CHARACTER_STATE_NAME_CONFLICT`、`CHARACTER_STATE_IN_USE`、`SHOT_CHARACTER_STATE_CONFLICT`。继续使用 `{code,message,details}`。

## 删除与恢复

| 操作 | 行为 |
| --- | --- |
| 删除 Character | 软删除角色及全部 active 状态；软删除角色 / 状态资产关系和镜头状态关系，不删除 Asset |
| 单独删除 State | 有 active Shot 引用时返回 409 + shots 数量；否则软删除并解除状态资产关系 |
| 删除 Project | 原 Phase 2 业务树级联加角色 / 状态级联；均使用同次删除时间戳 |
| 删除 Script / Scene / Shot | 原行为加软删除对应 ShotCharacterStateLink；不删除 CharacterState |
| 恢复 Character / Project | 只恢复同次删除的角色 / 状态；此前单独删除的状态不会复活 |
| 恢复 State | 必须有 active Character / Project，追加至列表末尾 |
| 恢复关系 | Phase 4 三种 Link 均需显式重新绑定；不会自动恢复过时或冲突引用 |

Phase 3 ProjectAssetLink / ShotAssetLink 的“保留已删除 owner 引用”策略不变。Phase 4 关系遵循本轮明确要求：不保留 active link 指向 deleted Character / State / Shot。两种行为的区别已在 UI 删除说明和本说明中记录。

## Asset Integration

Character 与 State 各自通过 N:N Link 引用统一 Asset，不复制文件、不限制 AssetType。AssetService 软删除引用保护在原 Project / Shot 基础上增加 Character / State；details 含各类数量，详情列出使用者。

AssetPicker 位于 assets feature，支持已有资产搜索、分类、thumbnail、选中状态、确认、加载更多与错误重试；一次选择一项。Character 的第一张 IMAGE 参考可作封面。状态折叠区最多展示 3 张 thumbnail，超出显示 +N，展开后提供绑定、解绑、预览。

Import Asset 复用 Phase 3 ImportAssets → AssetService → Managed Storage，只添加成功回调。导入后绑定失败时清楚提示资产已留在 Library，应从 Bind Asset 重试，不伪装成导入回滚。

## API

以下地址均带 `/api` 前缀：

| 方法 | 路径 | 能力 |
| --- | --- | --- |
| GET / POST | /projects/{project_id}/characters | 列表 / 创建；GET 支持 search、include_deleted |
| GET / PATCH / DELETE | /characters/{id} | 详情 / 更新 / 删除 |
| POST | /characters/{id}/restore | 恢复角色与同次删除状态 |
| GET / POST | /characters/{id}/states | 状态列表 / 创建；GET 支持 include_deleted |
| GET / PATCH / DELETE | /character-states/{id} | 状态详情 / 更新 / 删除 |
| POST | /character-states/{id}/restore | 恢复状态 |
| POST | /character-states/{id}/move | body {direction: up 或 down}，返回服务端顺序 |
| POST | /characters/{id}/assets | body {asset_id} |
| DELETE | /characters/{id}/assets/{asset_id} | 解除角色参考 |
| POST | /character-states/{id}/assets | body {asset_id} |
| DELETE | /character-states/{id}/assets/{asset_id} | 解除状态参考 |
| GET / POST | /shots/{shot_id}/character-states | 列出 / 绑定，POST body {character_state_id} |
| DELETE | /shots/{shot_id}/character-states/{state_id} | 解除镜头状态 |

角色 / 状态详情 GET 同样支持 include_deleted。完整请求与响应见本地 `/api/docs`。

## Frontend 与 UI

- 项目导航与 Overview 加 Characters，移除全局侧栏原不可用的 Characters 占位，保持项目范围。
- Characters Grid、搜索、真实计数 / 时间、创建、详情、编辑、删除和“显示已删除 / 恢复”。
- 完整 Character Detail：Info、角色参考、状态列表。状态编辑、排序、使用镜头数、折叠预览与资产绑定。
- 现有 Shot Detail 增加 Characters 小区块与 Add Character State，支持多个角色、缩略图、冲突反馈、解绑；没有重构 Shot Workspace。
- 复用 PageHeader / WorkspacePanel / MediaCard / EntityForm / DeleteEntity / QueryState / Badge / Button / Input / Select / Dialog / AssetDetailSheet。沿用 36px 控件、32px 小按钮、pending 防重复提交、长文本省略。
- Dark / Light、1024 / 1280 无横向页面溢出；人工看图发现并修复 Picker 搜索框被 Select 挤窄，新增搜索宽度和控件等高断言。

截图均来自独立测试 Workspace 的小型合成素材：

[Dark 列表](screenshots/phase4-list-dark.png) · [Light 列表](screenshots/phase4-list-light.png) · [Dark 1280 详情](screenshots/phase4-detail-dark-1280.png) · [Light 1024 详情](screenshots/phase4-detail-light-1024.png) · [Dark Picker](screenshots/phase4-picker-dark.png) · [Light Picker](screenshots/phase4-picker-light.png) · [Dark 状态表单](screenshots/phase4-state-form-dark.png) · [Light 状态表单](screenshots/phase4-state-form-light.png) · [Dark Shot](screenshots/phase4-shot-dark.png) · [Light Shot](screenshots/phase4-shot-light.png)。

## 验证

| 检查 | 结果 |
| --- | --- |
| Frontend lint / build | PASS / PASS |
| Ruff check / format --check | PASS / PASS，60 个 Python 文件 |
| Backend | 135/135，原111 + 新24 |
| Browser production | 31/31，原28 + 新3 |
| Browser development | 33/33，原30 + 新3 |
| Alembic CLI | upgrade head → downgrade base → upgrade head PASS |
| Alembic current / check | 0004_characters (head) / No new upgrade operations detected |
| Populated migration | 0004 → 0003 → 0004，Phase 2/3 原有行与 Asset 关系逐行一致，foreign_key_check 空 |

新增后端24项覆盖 CRUD、搜索、名称占用、项目隔离、状态顺序、恢复父级要求、重复绑定、不同资产分类、Asset 引用保护、Shot 冲突 / 多角色 / 跨项目、并发与 DB 索引、五类 owner 删除无 active orphan、六状态与应用重启持久化。既有 schema head / 允许表清单同步更新，没有删除既有测试。

新增浏览器3项覆盖两种主题的完整创建 / 编辑 / 排序 / 资产绑定 / Shot绑定 / 刷新 / 友好冲突 / 使用中删除拒绝 / 解绑 / 删除恢复，以及断线重试、重复保存防护和导入自动绑定。

实际命令：

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q --basetemp=.workspace/pytest-phase4-full -o cache_dir=.workspace/pytest-cache
backend/.venv/Scripts/ruff.exe check backend/app backend/tests scripts
backend/.venv/Scripts/ruff.exe format --check backend/app backend/tests scripts
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend test
$env:AVW_E2E_MODE = 'dev'
npm --prefix frontend test
```

Alembic CLI 单独指定 `.workspace/phase4-alembic/config.json` 与 `.workspace/phase4-alembic/workspace`。所有 pytest / E2E 回归使用隔离 Workspace；真实 D 盘初始文件 SHA-256 已记录，人工验收之前再次对比。测试读取锁定依赖，不新增或升级依赖。

首次浏览器失败源于测试在 React Router 导航完成前读取 URL，修正为等待 UUID 详情 URL 后读取。首次构建 / 格式化因 Windows 沙箱 EPERM，授权后完成。保留既有 Starlette 弃用、Vite chunk 与 Zod 注释警告，没有为消除警告改变依赖。

## 真实 SPF 验收

实机只有一张动漫头像；用户本轮明确选择“建立真实角色 / 状态 / S13，暂不绑定无关头像”。因此真实 SPF 图片绑定不作为本轮已验证项；绑定流程由隔离夹具覆盖。

- 所有自动化回归完成后，D Workspace 原有三个文件的 SHA-256 与回归前完全一致。随后备份数据库至 `D:\AI-Video-Workspace\backups\before-phase4-20260923.db`，正常启动应用通过 Alembic 升至 0004；未直接改真实 schema。
- 在原有 `SPF屏障设施培训视频` 项目，通过正式 UI 创建 `SPF培训女员工` 及六个状态：基础状态、发帽 + 口罩、黄色 PPE、黄色 PPE + 第一层手套、黄色 PPE + 双层手套、退出状态。
- 原数据只有 S01 / S09 / S10，未有 S13；按本轮用户确认，通过既有 API 在原剧本新增“风淋”场景及 `S13 · 风淋`，保留全部原有镜头。
- 在正式 Shot UI 绑定 `S13 → SPF培训女员工 → 黄色 PPE + 双层手套`，刷新后保持；关闭进程并重新运行启动器后，浏览器核对六状态及 S13 绑定均保持。
- 重启后数据库：Project 1、Script 1、ScriptNode / Scene 3 / 3、Shot 4、Asset 1、Character 1、CharacterState 6、ShotCharacterStateLink 1；角色 / 状态 AssetLink 均0，符合用户选择。
- 全部迁移前业务行逐行保留；原图和 thumbnail 哈希不变，`integrity_check=ok`，`foreign_key_check` 空。Bootstrap / Storage 架构保持。
- 真实 UUID、验收脚本、数据库快照和实机截图均保存在 Git 忽略的 `.workspace/phase4-audit/`，未提交真实数据或素材。文档截图仅为隔离合成素材。
- 与历史文档的实机差异：本轮授权只读检查未找到 `C:\Users\Lenovo\AI-Video-Workspace`，不能再将其描述为当前已验证存在的安全副本；本轮没有删除、移动或修改该路径。

## 限制与停止

- 删除恢复不自动恢复 Phase 4 的 Link，需明确重新绑定。
- 名称大小写敏感且软删除后保留占用；无 Character 全局共享 / 复制机制。
- Picker 每次确认一项；导入与绑定为两个请求，绑定失败时 Asset 留在 Library。
- 继续沿用单进程 Local-first 服务与 SQLite；未增加新依赖或后台服务。
- Phase 4 完成后停止，不进入 Phase 5 Shot Workspace。
