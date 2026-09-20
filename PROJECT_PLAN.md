# 项目计划索引

当前开发阶段：**Phase 1 — Database + Alembic + Storage Infrastructure**。

本文件在 Phase 1 开始时补充：此前仓库没有 `PROJECT_PLAN.md`。需求依据如下，内容不替换原规格：

1. [AI Video Workspace · MVP v0.1 开发规格](<AI Video Workspace · MVP v0.1 开发规格.md>)：产品范围、冻结技术栈、阶段顺序与架构边界。
2. [Phase 1 详细要求](docs/PHASE_1_SPEC.md)：用户本次粘贴的要求原文，约束本阶段的具体范围。
3. [开发状态](DEVELOPMENT_STATUS.md)：已实现能力、验收记录和已知限制。

本次更具体的 Phase 1 要求优先于上一版开发记录的下一阶段建议：仅实现基础设施表 `app_settings`，不提前建立完整业务 Schema。

## Phase 1 范围

- SQLite / SQLAlchemy engine、SessionLocal、Base 和 get_db 依赖。
- UUID、UTC Timestamp、Soft Delete mixin；轻量 Repository 基础。
- Alembic metadata 发现、初始 revision、upgrade / downgrade / autogenerate。
- 独立 Bootstrap Config 与 WorkspaceService；初始化和切换工作空间。
- StorageProvider / LocalStorageProvider、安全相对路径、完整文件发布、异常补偿。
- 最小 Workspace API、统一错误结构、后端测试及 Phase 0 回归。

禁止提前实现 Project / Script / Scene / Shot CRUD，以及资产库、角色、Prompt、AI、分镜、视频结果和项目导出。

完成验收、更新 README 和 DEVELOPMENT_STATUS 后停止。**Phase 2 必须等待用户确认，不自动进入。**
