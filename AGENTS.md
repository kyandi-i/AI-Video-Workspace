# 开发约定

- 先阅读 `PROJECT_PLAN.md`、`AI Video Workspace · MVP v0.1 开发规格.md` 和 `DEVELOPMENT_STATUS.md`；阶段细则见计划索引。
- 按规格第 63 节，每次只完成当前 Phase，不提前一次性实现整个系统。
- 每阶段结束必须运行项目与测试，检查迁移和已有功能，并更新 README 与 DEVELOPMENT_STATUS。
- 保持冻结技术栈、Local-first、SQLite、Managed Storage、UUID，以及 Route → Service → Repository / Provider 边界。
- 不将示例数据、静态占位或尚未实现的功能描述为已完成。
- 业务模块放入 frontend/src/features，后端数据库访问通过 Repository，文件访问通过 StorageProvider，AI 访问通过 AIProvider。
- 不引入注册、云服务、图片/视频生成 API、桌面外壳或强制 Docker；范围变更遵从规格第 64 节。
