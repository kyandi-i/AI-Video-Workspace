# 开发状态

更新日期：2026-09-22

**Phase 3.1 — Workspace Migration 已完成，等待用户验收。Phase 4 未开始。**

- 真实 Phase 3 Workspace 已从 `C:\Users\Lenovo\AI-Video-Workspace` 完整复制到 `D:\AI-Video-Workspace`，逐文件 SHA-256 校验后复用既有 BootstrapConfig 保存 D 选择。
- 修正文档与实机差异：此前 Bootstrap 已指向 D，但 D 只有 Phase 1 空数据库；该旧 D 目录已另行备份。
- 实际应用数据库与 Storage 均使用 D；原图、缩略图及 metadata 正常，全部原有数据库行保留。真实库1个Asset，无标签和绑定，未伪造数据。
- 人工小图上传证明原图、thumbnail 和 DB 仅写 D，C 全量文件未变；该人工测试记录与文件已清理。自动化回归继续使用隔离 Workspace。
- Settings 新增最小路径切换入口，复用现有 PUT API；Switch 不自动迁移数据。无新 revision、依赖、Storage 重写或 Phase 4 业务。
- lint / build / Ruff PASS；backend **111/111**；browser production **28/28**；browser development **30/30**；隔离 Alembic upgrade → downgrade base → upgrade / current / check PASS。
- 旧 C 副本仍保留，3个文件，总计 **16,052,219字节（约15.31 MiB）**，当前应用不再使用；未经用户确认不得删除。

完整路径、hash、数据清点、新写入证明、测试命令与限制见 [Phase 3.1 验收](docs/PHASE_3_1_STATUS.md)。

历史验收：[Phase 3](docs/PHASE_3_STATUS.md)、[Phase 2.5](docs/PHASE_2_5_STATUS.md)、[Phase 2](docs/PHASE_2_STATUS.md)、[Phase 1.5](docs/PHASE_1_5_STATUS.md)、[Phase 1](docs/PHASE_1_STATUS.md)、[Phase 0](docs/PHASE_0_STATUS.md)。范围见 [计划索引](PROJECT_PLAN.md) 和 [MVP 规格](<AI Video Workspace · MVP v0.1 开发规格.md>)。

**完成后停止，等待验收。**
