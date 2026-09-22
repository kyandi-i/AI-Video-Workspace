# 项目计划索引

当前开发阶段：**Phase 3.1 — Workspace Migration，已完成，等待用户验收。Phase 4 未开始。**

## 依据

1. [MVP v0.1 开发规格](<AI Video Workspace · MVP v0.1 开发规格.md>)：冻结技术栈、Local-first、分层架构与业务阶段边界。
2. [Phase 1 详细要求](docs/PHASE_1_SPEC.md)：Database / Alembic / Managed Storage，仅 app_settings 基础设施表。
3. [Phase 1.5 详细要求](docs/PHASE_1_5_SPEC.md)：用户提供的 UI Foundation 原文。
4. [开发状态](DEVELOPMENT_STATUS.md)：当前能力与验收记录；[Phase 0](docs/PHASE_0_STATUS.md) / [Phase 1](docs/PHASE_1_STATUS.md) 已归档。
5. [资源审计](docs/RESOURCE_AUDIT_2026-09-20.md)：Phase 1.5 前只读基线。用户明确确认“审计完成后立即执行 Phase 1.5”。
6. [Phase 2 范围与实现约定](docs/PHASE_2_SPEC.md)：用户本轮授权的项目层级业务闭环与验收映射；[Phase 1.5 历史状态](docs/PHASE_1_5_STATUS.md)。

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

完成本阶段后暂停。**Phase 4 必须获得用户确认，不自动进入。**
