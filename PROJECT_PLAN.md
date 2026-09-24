# 项目计划索引

当前开发阶段：**Phase 5.1 — Workspace Root Recovery & Hardening，已完成，等待用户验收；不进入 Phase 6 Prompt Template。**

## Phase 5.1 范围

- 诊断并修复 C / D 环境分叉：普通 Windows 与打包应用读取两份不同 Bootstrap Config，且缺失配置时 `initialize_workspace()` 会把 fallback 静默写成正式选择。
- 最小代码修复：`initialize_workspace()` 不再写 Bootstrap Config；配置缺失只提供内存默认 root，首次启动仍可用；非法配置明确报错不回退。
- 经正式 `PUT /api/settings/workspace` 把真实 Workspace Root 恢复为 `D:\AI-Video-Workspace`，不 COPY / MOVE / 覆盖任何数据。
- 统一配置：用户级 `AVW_BOOTSTRAP_CONFIG_PATH` → `D:\AI-Video-Workspace-Config\config.json`，两个环境解析同一份配置；不修改 APPDATA / HOME / USERPROFILE。
- 新增 9 项后端用例与完整回归；无新 migration、无 schema 变更、无新依赖。
- 详细范围、证据与限制见 [Phase 5.1 状态](docs/PHASE_5_1_STATUS.md)。Phase 5.1 COMPLETE，完成后停止，不进入 Phase 6。

## 依据

1. [MVP v0.1 开发规格](<AI Video Workspace · MVP v0.1 开发规格.md>)：冻结技术栈、Local-first、分层架构与业务阶段边界。
2. [Phase 1 详细要求](docs/PHASE_1_SPEC.md)：Database / Alembic / Managed Storage，仅 app_settings 基础设施表。
3. [Phase 1.5 详细要求](docs/PHASE_1_5_SPEC.md)：用户提供的 UI Foundation 原文。
4. [开发状态](DEVELOPMENT_STATUS.md)：当前能力与验收记录；[Phase 0](docs/PHASE_0_STATUS.md) / [Phase 1](docs/PHASE_1_STATUS.md) 已归档。
5. [资源审计](docs/RESOURCE_AUDIT_2026-09-20.md)：Phase 1.5 前只读基线。用户明确确认“审计完成后立即执行 Phase 1.5”。
6. [Phase 2 范围与实现约定](docs/PHASE_2_SPEC.md)：用户本轮授权的项目层级业务闭环与验收映射；[Phase 1.5 历史状态](docs/PHASE_1_5_STATUS.md)。

## Phase 5 范围

- Dedicated Shot Workspace：Header、项目真实顺序 Previous / Next、Scene 只读上下文、Character / State 上下文、Shot 参考素材、Production Status。
- 四个 nullable TEXT 要求字段、显式 Save、保存状态与未保存离开保护；creative_requirement 原样兼容。
- 原子替换角色状态；复用 AssetPicker / ImportAssets / Asset Detail / thumbnail，不新增素材角色分类或业务流程表。
- 迁移 `0005_shot_workspace`，隔离完整回归148后端 / 36生产浏览器 / 38开发浏览器，Dark / Light / 1024 / 1280。
- 真实 SPF S13 备份、迁移、10秒及需求保存、S10前后导航、刷新重启持久化验收通过；用户确认场景改名风淋室。
- 详细范围、兼容、API、截图、测试与限制见 [Phase 5 状态](docs/PHASE_5_STATUS.md)。Phase 5 COMPLETE，完成后停止，不进入 Phase 6。

## Phase 4 范围

- Project → Character → CharacterState；独立角色身份 / 视觉状态，参考媒体仍为统一 Asset。
- Character / State CRUD、顺序、软删除恢复、两类资产绑定、Shot N:N 状态绑定与同角色冲突保护。
- 项目 Characters 页面、角色详情、State 管理、AssetPicker、Shot Detail 基础绑定；复用现有 UI / Storage / API 分层。
- 迁移 0004_characters、Asset 引用保护扩展、Project / Scene / Shot 删除关系一致性、隔离完整回归与真实 SPF 验收。
- 本轮用户明确采用 Project scope、简单 description / notes，不增加原规格中的结构化 appearance_constraints；本轮要求优先。
- 详细字段、API、验收和限制见 [Phase 4 状态](docs/PHASE_4_STATUS.md)。完成后停止，不实现 Phase 5。

## Phase 3.1 范围

- 完整 COPY / SHA-256 VERIFY / 既有 BootstrapConfig / 启动验证；真实 Workspace 从 C 盘迁至 D 盘，保留旧 C 副本。
- 复用现有 WorkspaceService 与切换 API；Settings 增加最小路径切换入口，Switch 不等于自动 Migrate。
- 相对 Asset / thumbnail 路径不重写，数据库结构不变；隔离测试覆盖复制、切换、重启、新上传与原目录不变。
- 完成报告见 [Phase 3.1 验收](docs/PHASE_3_1_STATUS.md)；[Phase 3 历史状态](docs/PHASE_3_STATUS.md)。本阶段完成后停止。

## Phase 3 范围

- [本轮用户要求](docs/PHASE_3_SPEC.md)：统一 Asset、Managed Storage 图片 / 视频导入、多文件 / Drag & Drop、metadata、thumbnail、Grid / List、搜索 / 分类 / 标签、DetailSheet、Project / Shot 绑定。
- 只采用 IMAGE / VIDEO / STORYBOARD_6GRID / OTHER；本轮明确要求优先于 MVP 旧枚举列表。无 Character、Prompt 或 Storyboard 业务实体。
- 删除被引用资产返回 ASSET_IN_USE；先解绑再软删除，原文件与缩略图保留。被删除的 Project / Shot 仍保留可解绑引用，便于未来恢复。
- 迁移 0003_asset_library；Route → Service → Repository 与 StorageService ↔ StorageProvider 保持。
- 完成后停在 Phase 3，不自动进入 Phase 4。详见 [开发状态](DEVELOPMENT_STATUS.md)。

## Phase 2.5 已完成范围

- 只修现有 Project / Script / Scene / Shot 与公共组件的 UI / UX，不改业务模型、API 或迁移，不新增业务能力。
- 公共 Select 几何布局、状态 value → label / Badge 映射、控件尺寸、Dialog / Sheet 布局、删除确认、列表行高与长文本。
- Loading / Empty / Error、返回导航与筛选保留、服务端镜头顺序的稳定显示。
- Dark / Light、笔记本窗口、全部既有 CRUD 与公共组件回归、截图与文档。
- 详细结果见 [开发状态](DEVELOPMENT_STATUS.md)；[Phase 2 历史验收](docs/PHASE_2_STATUS.md)。

## Phase 2 已完成范围

- Project → Script → ScriptNode(SCENE) → Scene → Shot，五张 UUID / 时间戳 / 软删除表与正式迁移。
- Route → Service → Repository；场景 / 节点事务一致性、项目关系校验、镜头编号唯一性与连续排序。
- 项目列表、Overview、剧本树、场景列表、镜头搜索与筛选、基础镜头详情。
- 沿用 Dark / Light、紧凑工作台、Dialog、Skeleton、Toast、TanStack Query；只刷新受影响的数据。
- 数据库 / Service / API / 浏览器验证、迁移回退回升、文档与本地 Git 提交。

Phase 2 当时不实现 Asset / Character / Prompt / Storyboard / VideoResult、导出、回收站页面、Chapter / Sequence UI、复杂拖拽。没有更换技术栈或增加依赖。

完成本阶段后暂停。**不进入 Phase 6 Prompt Template，等待用户验收。**
