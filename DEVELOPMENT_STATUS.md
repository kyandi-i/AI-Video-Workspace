# 开发状态

更新日期：2026-09-21

## 当前阶段

**Phase 2 · Project / Script / Scene / Shot：已完成。** 本轮用户明确授权 Phase 2；实现止于项目层级核心工作流。Phase 3 尚未开始。

依据：[计划索引](PROJECT_PLAN.md)、[Phase 2 范围与实现约定](docs/PHASE_2_SPEC.md)、[MVP v0.1 规格](<AI Video Workspace · MVP v0.1 开发规格.md>)。历史验收：[Phase 0](docs/PHASE_0_STATUS.md)、[Phase 1](docs/PHASE_1_STATUS.md)、[Phase 1.5](docs/PHASE_1_5_STATUS.md)。

## 本阶段实现

- 新增 projects / scripts / script_nodes / scenes / shots，全部沿用 UUIDMixin、TimestampMixin、SoftDeleteMixin；正式迁移 `0002_core_workflow`，保留 app_settings。
- 五个 Repository 与四个业务 Service；Route 只解析请求并调用 Service。SQLite / Local-first / Managed Storage 边界保持，没有依赖 create_all，没有改动 StorageProvider 或接入 AI。
- Scene 创建在事务内同时产生 SCENE 节点。节点外键唯一，Service 检查项目归属和节点类型。Scene 独立维护内容，SCENE 节点的 title / description 留空；场景顺序只在 ScriptNode 中维护。
- Project / Script / Scene / Shot CRUD、include_deleted、restore，项目真实统计；镜头编号项目内唯一、时长验证、后端上移 / 下移排序、项目级搜索 / 场景 / 状态过滤。
- 删除 Project / Script 级联软删除后代；**删除 Scene 同步软删除对应 ScriptNode 和有效 Shot**，从所有正常列表及详情隐藏，没有物理删除。恢复只恢复同次删除的后代，保留此前单独删除的状态；批次时间在现有删除时间之后，避免时钟精度与回拨造成误恢复。
- 镜头编号 trim 后区分大小写，软删除后仍占用编号，恢复不会遇到被新记录抢占的问题；恢复场景 / 单个镜头追加到末尾，顺序连续。
- `/projects`、Project Overview、Script、Scenes、Shots 和基础 Shot Detail 页面，实际数据库 CRUD。Script 展示可折叠的剧本 → 场景 → 镜头层级，用户不需要接触 ScriptNode。
- 项目卡片、真实数量、紧凑镜头表格、组合搜索筛选、编辑、排序、删除确认、Dark / Light。Shot Detail 仅基础信息与编辑，没有 Prompt / Storyboard UI。
- Dialog 即时验证、保存期间禁用字段 / 保存 / 关闭、API 错误、成功 Toast、Skeleton。404 不自动重试；缓存按受影响项目、场景、镜头刷新，级联删除清除已打开的镜头详情缓存。
- 四个 Feature 各有 api.ts / hooks.ts / types.ts，统一 Query Key Factory。业务页面懒加载；Dashboard 最近更新项目读取数据库。没有业务 localStorage 或虚构记录。
- 健康 API 的 `phase` 更新为 2。README、计划索引与状态文档已更新，Phase 1.5 验收归档。

## 验收结果

| 检查 | 最终结果 |
| --- | --- |
| ESLint | 通过，无错误 / 警告 |
| TypeScript + Vite build | 通过 |
| 后端 pytest | **81/81 通过，无跳过** |
| Ruff check / format | 通过，42 个文件格式符合要求 |
| 前端 / 浏览器测试：构建模式 | **17/17 通过，无跳过** |
| 前端 / 浏览器测试：Vite 开发模式 | **19/19 通过，无跳过** |
| Alembic CLI upgrade → downgrade 0001 → upgrade | 通过，独立 `.workspace/phase2-migration` |
| Alembic current / check | `0002_core_workflow (head)`；无 metadata 差异 |
| 完整 downgrade base → upgrade / autogenerate | pytest 临时数据库通过 |
| 带业务数据回退 / 已有 Phase 1 设置保留 | 通过；外键检查通过 |
| 事务回滚 / 1:1 / 跨项目关系 | 通过，注入 Scene 写入失败后无孤立节点 |
| 并发创建 / 唯一编号 / 连续排序 | 通过，8 个并发请求及同编号冲突验证 |
| 恢复 / 重复恢复 / 时钟精度 | 通过，之前独立删除的子项不会被误恢复 |
| 刷新与服务重启持久化 | 浏览器刷新与 FastAPI 重建分别通过 |
| 页面布局与主题 | 两主题核心流程；1920 / 1280 / 1024 / 390px 无页面水平溢出，表格独立滚动 |
| 既有功能 | 主题持久化、跨标签、受限存储、连接重试、Workspace 信息 / 复制、公共组件、颜色对比度、路径安全 / 存储回归通过 |
| Git whitespace | `git diff --check` 通过 |
| Git 工作区 | 本阶段代码、测试、文档和截图作为本地提交保存，提交后工作区干净 |

前端测试继续使用既有 Playwright 基础设施，没有增加另一套测试框架。两种启动模式都真实运行后端、SQLite 和 React，覆盖创建 Project → Script → Scene → 多个 Shot，编辑、上移 / 下移、搜索 / 筛选、删除确认、刷新持久化、pending 与 API 冲突；另覆盖级联删除后的浏览器后退行为。

旧测试中“仅有基础设施表”的断言按 Phase 2 更新为准确的五张业务表集合；时间戳更新测试改用明确的较早初始时间，继续断言 updated_at 前进，避免依赖 Windows 两次连续调用的时钟精度。没有以跳过测试处理失败。

## 数据与环境隔离

- pytest 使用临时 Workspace / Database；Playwright 使用 `.workspace/e2e` 下独立 bootstrap 与数据库，最多 2 workers，测试服务完成后退出。
- 手动迁移验收只使用 `.workspace/phase2-migration`。**测试未写入用户真实 `D:\AI-Video-Workspace`**，没有修改用户 bootstrap 选择。
- 正常启动器在下次启动时通过 Alembic 自动将用户当前 Workspace 升到 head；没有在用户数据库上执行回退。
- 沿用现有 Node / Python / uv / npm 与 D 盘 Playwright 浏览器，没有安装新依赖、清理缓存、移动目录或更换架构。

## 截图

以下为真实 E2E 隔离数据库中的测试项目，明确不是用户生产数据；项目名称带 E2E 标识。已检查深浅色布局、信息密度和文字可读性。

- [Dark Script](docs/screenshots/phase-2-script-dark.png)
- [Light Script](docs/screenshots/phase-2-script-light.png)
- [Dark Shots](docs/screenshots/phase-2-shots-dark.png)
- [Light Shots](docs/screenshots/phase-2-shots-light.png)

## 当前边界

- 不包含 Asset / Character / Prompt / Storyboard / VideoResult、导出、回收站页面、Chapter / Sequence UI 或复杂 DnD。枚举中的制作状态仅为人工标记。
- 单进程本地服务；列表当前加载本项目全部数据，尚无分页或虚拟列表。后端提供搜索 / 筛选参数，前端对已加载列表组合过滤。
- 主 JS chunk 643.25 kB / gzip 201.47 kB，业务路由已拆包；Vite 仍提示主 chunk 超过 500 kB。未提高提示阈值。
- 沿用的 Zod PURE 注释和 Starlette/httpx、AnyIO 弃用提示仍存在，不阻止构建或测试；本阶段未升级依赖。
- 只验证 PostgreSQL DDL 可编译，没有连接真实 PostgreSQL；运行数据库保持 SQLite。现有 Storage 文件补偿与缩略图能力边界仍按 Phase 1 记录。

## 下一步

**停在 Phase 2，等待用户明确授权 Phase 3（Asset Library）。**
