# 开发状态

更新日期：2026-09-23

**Phase 4 — Character / CharacterState 已完成，等待用户验收。不进入 Phase 5 Shot Workspace。**

- 新增项目角色与角色视觉状态：UUID、UTC、软删除、名称唯一、notes nullable、服务端连续排序及同次级联恢复。
- 新增 CharacterAssetLink / CharacterStateAssetLink / ShotCharacterStateLink，复用统一 Asset；角色本身不存图片，不复制文件。Shot 同项目、同角色单 active 状态由 Service 与 DB 索引保护。
- 状态使用中删除返回明确镜头数量；Asset 引用保护加入角色 / 状态；Project / Script / Scene / Shot 删除同步处理新增关系，不留 active orphan。
- 项目 Characters 导航、Grid / Search、角色详情、状态 CRUD / 顺序 / 预览、AssetPicker、导入自动绑定、软删除恢复与基础 Shot 绑定 UI。继续复用 Phase 2.5 / 3 公共组件与 Dark / Light 视觉。
- 迁移 `0004_characters`；Route → Service → Repository / Provider、Local-first、SQLite、Managed Storage 与外置 Bootstrap 保持。No new dependency.
- lint / build / Ruff PASS；backend **135/135**（111 + 24）；browser production **31/31**（28 + 3）；browser development **33/33**（30 + 3）；隔离 Alembic upgrade → downgrade base → upgrade / current / check PASS，已有 Phase 2/3 数据逐行迁移保留。
- Dark / Light、1024 / 1280、表单 / Picker / Shot / 详情截图验证；修正 Picker 搜索框被 Select 挤压并加入几何断言。截图使用合成夹具。
- 全部自动化回归后，真实 D Workspace 原有 DB / 原图 / thumbnail 哈希与测试前一致。此后才执行用户明确授权的真实数据验收。
- 真实 SPF 项目已建立 `SPF培训女员工`、六个状态、风淋场景与 S13，绑定 `黄色 PPE + 双层手套`。刷新和应用重启后保持。用户确认暂不绑定唯一的无关动漫头像；真实素材绑定不冒充已验收。
- 真实迁移前 DB 备份：`D:\AI-Video-Workspace\backups\before-phase4-20260923.db`。原有业务行和媒体哈希保持，DB integrity / FK 检查通过。
- 历史 C 盘安全副本本轮只读检查未找到；未对该路径执行删除或移动。当前应用仍使用 `D:\AI-Video-Workspace`。

完整模型、API、生命周期、真实验收、截图和限制见 [Phase 4 验收](docs/PHASE_4_STATUS.md)。

已知限制：恢复不自动重建 Phase 4 关联，需要重新绑定；名称区分大小写且已删除记录仍保留名称；Picker 每次确认一个 Asset；导入与绑定为两次请求，绑定失败时素材仍在 Library。

历史验收：[Phase 3.1](docs/PHASE_3_1_STATUS.md)、[Phase 3](docs/PHASE_3_STATUS.md)、[Phase 2.5](docs/PHASE_2_5_STATUS.md)、[Phase 2](docs/PHASE_2_STATUS.md)、[Phase 1.5](docs/PHASE_1_5_STATUS.md)、[Phase 1](docs/PHASE_1_STATUS.md)、[Phase 0](docs/PHASE_0_STATUS.md)。范围见 [计划索引](PROJECT_PLAN.md) 和 [MVP 规格](<AI Video Workspace · MVP v0.1 开发规格.md>)。

**本阶段完成后停止，等待验收。**
