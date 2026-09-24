# Phase 6 — Prompt Template 验收

日期：2026-09-24。基线：`79a3589`。**Phase 6 COMPLETE；Phase 7 NOT STARTED。**

## 1. 完成范围

独立 PromptTemplate、Global / Project scope、7 类 Category、CRUD、搜索、范围 / 分类筛选、软删除 / 恢复、Duplicate、Copy Global → Project、统一 Placeholder Registry、后端白名单校验、纯文本 Sample Preview、光标处插入变量、编辑器关闭草稿保护、模板库 / 项目模板页面，以及 Shot Workspace 的轻量 PromptTemplatePicker。未增加依赖。

Route → Service → Repository 保持。Preview 调用纯文本渲染函数，不读写数据库，不调用 AI。无 PromptRecord、Prompt Version、Generate、Streaming 或 Shot 模板外键 / 关联表。

## 2. 数据模型与生命周期

表 `prompt_templates` 复用 BaseModel 的 UUID、UTC timestamp 与软删除语义。

| 字段 | 类型 / 约束 |
| --- | --- |
| id | UUID 主键 |
| scope | GLOBAL / PROJECT，非空，数据库 enum CHECK |
| project_id | nullable UUID，外键 projects.id |
| name | String(255)，trim 后非空 |
| description | nullable TEXT；请求上限 100,000 字符 |
| category | 7 值 enum，非空，数据库 CHECK |
| template_content | 非空 TEXT；请求与数据库上限 100,000 字符；原文保留 |
| created_at / updated_at | UTC timestamp，非空 |
| deleted_at | nullable UTC timestamp |

Service 与 DB CHECK 均保证 GLOBAL → project_id NULL、PROJECT → project_id 非 NULL；Service 校验项目存在且未删除。索引：`ix_prompt_templates_scope`、`ix_prompt_templates_project_id`、`ix_prompt_templates_category`；唯一索引：`uq_template_global_name`（scope=GLOBAL 的 name）、`uq_template_project_name`（project_id + name）。名称精确比较，沿用 Character：软删除仍占用名称，冲突返回 `PROMPT_TEMPLATE_NAME_CONFLICT`。

Project 删除采用父级可见性门控：所属模板在列表、Detail、编辑、Duplicate、Restore 中不可用；Project 恢复后原可用模板重新可用，独立软删除的模板仍保持删除。GLOBAL 不受项目删除影响。不修改既有 Project delete 实现。

## 3. Category 与 UI label

| Enum | Label |
| --- | --- |
| STORYBOARD_6GRID | Storyboard 6-Grid |
| VIDEO_GENERATION | Video Generation |
| CHARACTER_IMAGE | Character Image |
| SCENE_IMAGE | Scene Image |
| IMAGE_REFERENCE | Image Reference |
| START_END_FRAME | Start / End Frame |
| OTHER | Other |

## 4. Placeholder Registry 与校验

唯一事实源：`backend/app/services/template_placeholders.py`。前端从 API 读取 key / label / description / group / example，不另存一份变量清单。

完整白名单：

```text
shot_code
shot_title
shot_description
duration_seconds
main_action
key_constraints
negative_constraints
free_notes
scene_name
scene_description
scene_fixed_constraints
scene_negative_constraints
characters_context
reference_assets_context
shot_context
```

- `{{main_action}}` 与 `{{ main_action }}` 都合法；解析 key 时 trim，存储正文保持中文、全角符号和换行。
- 重复变量、无变量的静态正文合法。未知 key / 属性访问 / 索引 / 函数表达式 / 不配对双花括号返回 `INVALID_TEMPLATE_PLACEHOLDER`，details 含 `unknown_placeholders`；创建、PATCH、Preview 都验证。
- `{{__class__}}`、`{{foo.bar}}` 被拒绝。`{% for %}` 只是普通文本，不执行。没有 eval、exec 或模板语言解释器。
- 名称与正文不接受空白内容；必填字段不接受 null。非法 scope / category enum 沿用统一 `VALIDATION_ERROR`；跨 scope 关联错误使用 `INVALID_TEMPLATE_SCOPE`。

## 5. Preview、复制与 Shot 入口

**Deterministic substitution only. No AI call.** Sample Preview 使用注册表里的固定样例（S13 / 风淋 / 10秒等），未传入 / null 值渲染为空字符串。单次替换不递归解析替换值。模板和预览以普通文本展示，没有 HTML 注入。

Preview 不保存模板、不更新 timestamp、不创建记录。Editor 使用 Textarea selection API 在光标处插入，支持替换所选文本；Save 明确操作，Unsaved / Saving / Saved / Save failed 可见，关闭未保存正文需要确认，浏览器离开也有保护。

Duplicate 在原 scope / project 创建独立记录：`Name Copy`、`Name Copy 2`…，包含软删除名称冲突，并保持 255 字符上限。Copy Global → Project 优先保留原名，目标冲突时使用同一 Copy 后缀策略。目标必须为活跃项目，原模板内容和 timestamp 不变，无继承关系。

Shot Workspace → Prompt Template → Browse Templates：只列 GLOBAL + 当前项目，支持搜索 / scope / category、原文与 Sample Preview、Select Template。选择仅为当前页面内存状态，刷新或离开即清除，不写 Shot。**No prompt generation.**

## 6. API

统一前缀 `/api/prompt-templates`：

| 方法 / 路径 | 行为 |
| --- | --- |
| GET / | 列表；scope / project_id / category / search / include_deleted / include_global |
| POST / | 创建 |
| GET /placeholders | 唯一变量注册表 |
| POST /preview | template_content → rendered_content（固定样例） |
| GET /{id} | 详情；可 include_deleted |
| PATCH /{id} | 编辑；省略字段保留原值 |
| DELETE /{id} | 软删除 |
| POST /{id}/restore | 恢复并验证项目 |
| POST /{id}/duplicate | 原范围内独立复制 |
| POST /{id}/copy-to-project | Global → 活跃项目 |

## 7. 恢复验证与浏览器收尾诊断

首次开发按失败停止规则暂停，未迁移真实 DB。本轮用户明确授权恢复验证。实际复核 model / migration 后，仅将 `test_bootstrap.py` 完整表集合更新为 Phase 5 表 + `prompt_templates`，测试名称同步为 Phase 6，未删除断言、使用子集、skip 或 xfail。单独 `test_bootstrap.py` **4/4 PASS**；随后全量运行未使用 maxfail。

浏览器挂起原因已定位：`DEBUG=pw:webserver` 在全部断言结束后停于 `Terminating the WebServer`；浏览器与测试 worker 已退出，Python 服务仍存活。本机安装的 Playwright Windows webServer teardown 不支持 POSIX gracefulShutdown，使用 taskkill 进程树回收；Codex 沙箱内 `tasklist` 返回 Access denied，因此服务器无法被回收。诊断运行取消，**不计 PASS**。

经批准在非沙箱环境运行相同隔离测试，新增 7 项 **7/7 PASS，进程正常退出 0**（12.2s）。随后 production / development 全量也正常结束；没有修改 harness、注入 process.exit(0)、增加依赖或更改业务实现来绕过问题。现有 npm wrapper 仅传播 Playwright 的退出码。

## 8. 完整质量结果

| 检查 | 结果 |
| --- | --- |
| Full Backend | **201/201 PASS**（157 基线 + 44 新增；50.32s，exit 0） |
| New Browser | **7/7 PASS**（exit 0） |
| Browser production | **43/43 PASS**（36 + 7；51.6s，exit 0） |
| Browser development | **45/45 PASS**（38 + 7；1.2m，exit 0） |
| Frontend lint | PASS |
| Frontend build | PASS |
| Ruff check / format --check | PASS |
| Isolated Alembic CLI | 0005 → head → 0005 → head / check / current PASS |

当前 head：`0006_prompt_templates`，down_revision：`0005_shot_workspace`。Migration 只建表和索引，不 seed。全量后端还覆盖 base 回退回升、metadata / autogenerate，以及已有数据升级保持。Phase 5 Shot Workspace 和 Phase 5.1 bootstrap 全部回归通过。

既有非失败提示仍在：Starlette/httpx 弃用提示、Vite bundle 大小与依赖注释提示。没有安装提示中提及的新依赖。

## 9. Production Workspace Safety

前后均通过真实项目 Settings / WorkspaceService 解析：

```text
bootstrap_config_path = D:\AI-Video-Workspace-Config\config.json
workspace_root        = D:\AI-Video-Workspace
database_path         = D:\AI-Video-Workspace\data\workspace.db
automated tests changed real workspace = false
```

pytest 使用 autouse fixture，加启动进程显式测试环境；Playwright 每次使用 `.workspace/e2e/run-*` 并在 webServer.env 覆盖 workspace / bootstrap；CLI migration 使用 `.workspace/phase6-resume-alembic`。没有继承真实配置来初始化测试库。

所有自动化前后：真实 DB、原图、thumbnail、3 个旧备份共 **6/6 SHA-256 完全一致**，文件集合无增减；共享配置哈希也一致。未碰 C Workspace，未修改用户环境变量、Workspace Root、ACL；未清理 TEMP_WORKSPACE_VERIFY。

全部自动化通过后新增唯一备份：

```text
D:\AI-Video-Workspace\backups\before-phase6-20260924-175114.db
source SHA-256 = backup SHA-256
5c10ad14ea2f8a68311bb220b0f037c4745717c554116a5514dc2125ed5b3464
```

随后真实 DB **仅 upgrade head**，从 0005 到 0006，未 downgrade。逐表比较原有所有业务行完全一致；SPF Project / S13 / Character / 6 States / 黄色 PPE + 双层手套关系 / 四个结构化字段 / Asset 均保持，integrity_check=ok、foreign_key_check 空，新增 prompt_templates 空表。

## 10. 真实定向验收

自动回归结束、备份升级完成后，使用正式界面只创建用户指定的两条记录：

| Scope | 名称 | Category |
| --- | --- | --- |
| GLOBAL | Seedance Video Generation | VIDEO_GENERATION |
| PROJECT（SPF） | SPF 六宫格分镜模板 | STORYBOARD_6GRID |

正文分别为 `测试模板：{{shot_code}}` + `动作：{{main_action}}`，以及 `测试分镜：{{shot_title}}` + `{{shot_context}}`；编辑后追加“仅用于模板验收。”。均少于 200 字符，非正式生产 Prompt。

两条记录均完成 create → edit → Sample Preview → refresh；Preview 前后 API 数据完全相同。关闭服务（进程 45520）后启动全新服务（30548），再次通过页面编辑器与 API 读取，正文 / scope / project / category 保持。最终恰好两条活跃模板。

验收完成后全部旧业务表仍逐行相同；原素材、thumbnail、旧备份、共享配置哈希不变。真实 DB 的预期变化仅为 schema / alembic revision 和两条模板；另新增一份 Phase 6 备份。真实快照、验收辅助脚本与数据只保存在 Git 忽略的审计目录。

## 11. UI 与截图

Dark / Light、1024 / 1280 的创建 / 编辑 / 插入 / 筛选 / 预览 / 保存与页面溢出检查通过；保存按钮可见，编辑器正文和帮助面板可滚动。Picker 在两种主题 1024 验证，全量 Phase 5 覆盖原 Shot 布局。

截图仅使用隔离 fixture，不含真实资产：

- [Template Library · Dark](screenshots/phase6-template-library-dark.png)
- [Editor / Placeholder Panel · Light](screenshots/phase6-template-editor-light.png)
- [Sample Preview · Dark](screenshots/phase6-template-preview-dark.png)
- [Shot Template Picker · 1024](screenshots/phase6-shot-template-picker-1024.png)

## 12. 已知限制与停止边界

- Preview 当前只替换固定 sample，不从真实 Shot 构建上下文，也不生成 Prompt。
- 模板选择不持久化；无历史版本、AI 调用或生成工作流。
- 不提供模板继承或永久删除；项目删除时通过父级状态隐藏其模板。
- 无多标签并发编辑冲突检测、离线草稿恢复；列表暂未分页。
- 此 Windows 沙箱不具备 Playwright 子进程回收所需权限；回归应使用获准的正常进程环境，同时保留显式测试隔离。

README / DEVELOPMENT_STATUS / PROJECT_PLAN 已同步。仅提交源码、测试、文档和 fixture 截图；数据库、备份、共享配置、真实资产、临时输出不进入 Git。**Phase 6 完成后停止；Phase 7 NOT STARTED。**
