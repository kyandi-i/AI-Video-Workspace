# 项目计划索引

当前开发阶段：**Phase 1.5 — UI Foundation，已完成，等待确认下一阶段。**

## 依据

1. [MVP v0.1 开发规格](<AI Video Workspace · MVP v0.1 开发规格.md>)：冻结技术栈、Local-first、分层架构与业务阶段边界。
2. [Phase 1 详细要求](docs/PHASE_1_SPEC.md)：Database / Alembic / Managed Storage，仅 app_settings 基础设施表。
3. [Phase 1.5 详细要求](docs/PHASE_1_5_SPEC.md)：用户提供的 UI Foundation 原文。
4. [开发状态](DEVELOPMENT_STATUS.md)：当前能力与验收记录；[Phase 0](docs/PHASE_0_STATUS.md) / [Phase 1](docs/PHASE_1_STATUS.md) 已归档。
5. [资源审计](docs/RESOURCE_AUDIT_2026-09-20.md)：Phase 1.5 前只读基线。用户明确确认“审计完成后立即执行 Phase 1.5”。

## Phase 1.5 范围

- 深浅色 Design Tokens，默认 Dark、localStorage 仅保存 UI Theme Preference。
- Sidebar + Topbar + 全宽 Workspace，工具化 Dashboard 与真实本地状态。
- shadcn/ui 风格源码组件、Radix 行为、Lucide 单一图标库、Sonner 反馈。
- WorkspacePanel / PageHeader / SectionHeader / EmptyState / EntityCard / MediaCard / DetailSheet。
- 只读 Workspace 信息及主题设置；组件交互、可读性、截图、前后端与迁移回归。

不实现 Project / Asset CRUD、Prompt、AI、分镜、视频版本或导出，不改写后端业务架构。没有执行缓存清理、目录迁移或依赖卸载。

完成本阶段后暂停。**Phase 2 必须再次获得用户确认，不自动进入。**
