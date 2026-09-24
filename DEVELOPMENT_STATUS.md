# 开发状态

更新日期：2026-09-24

**Phase 5.1 — Workspace Root Recovery & Hardening COMPLETE。已完成，等待用户验收；不进入 Phase 6 Prompt Template。**

- 统一 Bootstrap Config：用户级环境变量 `AVW_BOOTSTRAP_CONFIG_PATH` 指向 `D:\AI-Video-Workspace-Config\config.json`（仅含 `workspace_root`，位于 Workspace 与仓库之外）。普通 Windows 会话与 `%APPDATA%` 被重定向的打包应用因此解析**同一份**配置 → `D:\AI-Video-Workspace`；两个环境实测 `bootstrap_config_path` 与 `workspace_root` 完全一致。
- 修复 fallback 自播种：`initialize_workspace()` 不再调用 `bootstrap.save()`。配置缺失只在内存中使用默认 root，首次启动仍可正常初始化，但**绝不**创建或改写 Bootstrap Config；只有显式 `PUT /api/settings/workspace` 写入。非法配置仍明确报 `BOOTSTRAP_INVALID`，不回退。
- 经正式 API 将真实 Workspace Root 由空的 C 恢复到 D：未 COPY / MOVE / RENAME / 覆盖任何数据库，未修改 `APPDATA` / `HOME` / `USERPROFILE`，未新建 symlink / junction。
- 修改配置前新增安全备份 `D:\AI-Video-Workspace\backups\before-workspace-config-fix-20260924-161401.db`；源与备份 SHA-256 一致（`425A2564…`），未覆盖 Phase 4 / Phase 5 备份。
- 真实数据核验（只读 + 正式 API）：SPF Project、S13（风淋 · 10 秒 · 四个 Phase 5 字段）、SPF培训女员工、6 个 CharacterState、`S13 → 黄色 PPE + 双层手套` 全部存在。
- 最小写入验证：经正式 API 创建并软删除 `TEMP_WORKSPACE_VERIFY` → D 变化、C 全程 SHA-256 不变。
- 回归：后端 **157/157**（Phase 5 基线 148 + 新增 9），browser production **36/36**，development **38/38**；Frontend lint / build、Ruff check / format PASS；Alembic 隔离 upgrade → downgrade → upgrade PASS，`current` = `0005_shot_workspace (head)`，`check` 无新操作。**无新 migration，无 schema 变更，无新依赖。**
- 隔离：pytest autouse fixture 与 Playwright `webServer.env` 均显式注入独立的 `AVW_WORKSPACE_ROOT` / `AVW_BOOTSTRAP_CONFIG_PATH`，自动化测试不继承本机生产环境变量，也不修改用户级设置。
- 真实 DB、原图、thumbnail、全部 backups 与 C 空 Workspace 在验收前后逐文件 SHA-256 一致。
- 未删除 C，也未删除任何旧配置 / 旧备份；C 结论为 **Safe to delete（待用户确认）**。详见 [Phase 5.1 验收](docs/PHASE_5_1_STATUS.md)。

**Phase 5 — Shot Workspace COMPLETE。**

- 正式 `/shots/:shotId/workspace`，列表直达，Header / Previous / Next / Scene Context / Characters / Reference Assets / Requirements / Production Status；旧详情与 CRUD / Search / Filter / Move 保留。
- Shot 新增 main_action / key_constraints / negative_constraints / free_notes 四个 nullable TEXT 字段，ShotCreate / ShotUpdate / ShotRead 向后兼容；creative_requirement 原样保留，非空时可查看 Legacy Creative Requirement，旧编辑器继续使用。
- 一次 PATCH 显式 Save，Saved / Unsaved / Saving / Save failed、失败草稿保留、防重复提交、内部路由离开确认与浏览器原生离开保护。
- GET Workspace 聚合真实上下文与项目服务端顺序；PUT character-states 在单事务内替换同角色状态，保留 Phase 4 唯一索引、冲突校验与生命周期。
- AssetPicker / ImportAssets / Asset Detail 复用；thumbnail 预览、前六项 / View All，Unbind / Remove 只解除关系。Scene 只读，角色资产不复制到 Shot。
- 迁移 `0005_shot_workspace`；Workspace 架构、Local-first、SQLite、Managed Storage、UUID、分层边界和全部锁文件保持。No new dependency.
- lint / build / Ruff check / format PASS；backend **148/148**（135 + 13），browser production **36/36**（31 + 5），browser development **38/38**（33 + 5），均正常退出。
- 隔离 Alembic CLI upgrade → downgrade base → upgrade / current / check PASS；有数据的0005 → 0004 → 0005保持 Phase 2/3/4 所有旧列及关联，外键校验通过。
- Dark / Light、1024 / 1280截图人工检查、无水平溢出、保存条可见、Textarea / Select / thumbnail布局通过。正式文档截图为隔离夹具。
- 所有自动化测试结束后真实 Workspace 初始文件 SHA-256保持不变。随后创建 `D:\AI-Video-Workspace\backups\before-phase5-20260923.db`，正常启动执行新迁移；没有覆盖 Phase 4 备份。
- 真实 SPF S13通过正式UI保存10秒与指定四字段，保留原角色 `SPF培训女员工 → 黄色 PPE + 双层手套`；按用户确认将场景“风淋”改名“风淋室”，使用实际存在的 S10导航验收，不新建 S12。
- 刷新、S10 → S13、服务重启后保持；其他业务数据、媒体和旧备份不变，DB integrity / FK通过。未绑定用途不明的真实素材。实机截图、脚本和数据快照仅存Git忽略的审计目录。

完整范围、数据模型、API、导航、保存行为、截图和限制见 [Phase 5 验收](docs/PHASE_5_STATUS.md)。

已知限制：导入与绑定为两次请求，绑定失败时资产仍在Library；Legacy字段通过旧详情编辑；Open Scene沿用场景列表；浏览器关闭提示由浏览器控制，无离线草稿恢复及多标签编辑冲突处理。

历史验收：[Phase 5.1](docs/PHASE_5_1_STATUS.md)、[Phase 4](docs/PHASE_4_STATUS.md)、[Phase 3.1](docs/PHASE_3_1_STATUS.md)、[Phase 3](docs/PHASE_3_STATUS.md)、[Phase 2.5](docs/PHASE_2_5_STATUS.md)、[Phase 2](docs/PHASE_2_STATUS.md)、[Phase 1.5](docs/PHASE_1_5_STATUS.md)、[Phase 1](docs/PHASE_1_STATUS.md)、[Phase 0](docs/PHASE_0_STATUS.md)。范围见 [计划索引](PROJECT_PLAN.md) 和 [MVP 规格](<AI Video Workspace · MVP v0.1 开发规格.md>)。

**Phase 5.1 完成后停止，等待验收。不进入 Phase 6。**
