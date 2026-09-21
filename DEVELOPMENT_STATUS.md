# 开发状态

更新日期：2026-09-21

## 当前阶段

**Phase 3 — Asset Library 已完成。停在本阶段，等待用户验收；Phase 4 未开始。**

依据：[本轮授权原文](docs/PHASE_3_SPEC.md)、[计划索引](PROJECT_PLAN.md)、[MVP 规格](<AI Video Workspace · MVP v0.1 开发规格.md>)。历史验收：[Phase 0](docs/PHASE_0_STATUS.md)、[Phase 1](docs/PHASE_1_STATUS.md)、[Phase 1.5](docs/PHASE_1_5_STATUS.md)、[Phase 2](docs/PHASE_2_STATUS.md)、[Phase 2.5](docs/PHASE_2_5_STATUS.md)。

## 开始时真实状态与文档差异

- 实际最新提交 `ff29ea6 fix: unify Phase 2.5 select and workflow UX`；修改前 `git status --short` 仅有未跟踪的 HANDOFF.md。
- HANDOFF 仍声称 Phase 2.5 未完成、最新提交 71d25ba，测试为 81 / 17 / 19，部分路径迁移描述过期。本轮保留其历史正文并添加显著历史标注，随文档纳入版本控制。
- MVP 第 16 节列举了用途型 AssetType；本轮明确冻结为 IMAGE / VIDEO / STORYBOARD_6GRID / OTHER，以最新用户要求为准。没有 Character / CharacterState / Storyboard 业务实体或工作流。
- 读取并复用现有代码、migration、tests、npm scripts、依赖锁及 Workspace / Storage 机制；没有推断历史 commit 或更换技术栈。

## 实际完成能力

- 统一 Asset Library：普通文件选择、多文件顺序导入、Drag & Drop、每项等待 / 导入中 / 成功 / 失败反馈、提交防重；一个坏文件不影响后续文件。
- PNG / JPG / JPEG / WebP 图片，以及 MP4 / MOV / WebM 视频；真实签名 / 解码校验、MIME、大小、尺寸、视频时长与 SHA-256。支持首帧缩略图、详情视频播放及 HTTP Range。
- Grid / List、名称和原文件名搜索、类型 / 标签筛选、每批 60 项加载更多。URL 保留视图、筛选和当前打开的详情。
- DetailSheet：按需原图 / 视频预览、基本 metadata、名称 / 描述 / 类型编辑、标签增删、Project / Shot 使用关系、绑定 / 解绑、资产软删除。
- Project 增加 Assets 入口；Shot Detail 增加关联资产入口。它们查询同一资产库，绑定不复制文件，没有提前实现完整 Shot Workspace。
- Dark / Light、1280 × 800 与 1024 × 720 检查通过；长文件名与标签截断、按钮位置稳定。修复新增 Assets 标签使 390px 导航溢出的问题；修复 Radix ScrollArea 的内部 table 布局被长标签撑宽的问题。既有公共组件与 Select 用例全部保留通过。

## 数据模型

所有新增表均沿用 UUIDMixin、TimestampMixin、SoftDeleteMixin，使用正式迁移 **0003_asset_library**。

| 实体 / 表 | 核心字段或关系 |
| --- | --- |
| Asset / assets | name、description、asset_type、original_filename、storage_path、thumbnail_path、mime_type、file_size、width、height、duration_seconds、checksum |
| Tag / tags | name、normalized_name UNIQUE；Unicode NFKC、空白折叠、casefold 去重，最多 80 字符 |
| AssetTag / asset_tags | Asset N:N Tag；asset_id + tag_id UNIQUE |
| ProjectAssetLink / project_asset_links | Project N:N Asset；project_id + asset_id UNIQUE |
| ShotAssetLink / shot_asset_links | Shot N:N Asset；shot_id + asset_id UNIQUE |

同一 Asset 可同时绑定多个项目 / 镜头，重复绑定幂等；解除绑定只软删除 Link，再绑定恢复同一 Link。Shot 绑定不隐式创建 Project 绑定。AssetType 与文件真实 MIME 分离：图片可归 Image / Storyboard 6-Grid / Other，视频可归 Video / Other，不能把视频改为图片分类。六宫格不要求生成 Storyboard 实体。

## Storage 与失败一致性

- 继续 `Route → Service → Repository`；文件处理由 `StorageService ↔ StorageProvider`，本地实现为 LocalStorageProvider。没有 Route SQL、BLOB、base64 API 或用户原始绝对路径引用。
- raw binary upload 写入当前 Workspace 的 `storage/temp/<uuid>.partial`；避免 multipart 框架落入系统临时目录。媒体验证后复制为 `storage/assets/<前两位>/<uuid>.<ext>`。
- 图片 / 视频首帧缩略图保存为长边至多 512px 的 JPEG，位于 `storage/thumbnails/<uuid>.jpg`。列表只加载缩略图，不批量解码视频。
- DB 保存相对 Workspace 的 `storage/assets/...`、`storage/thumbnails/...`；Provider 内部继续使用相对 storage 根的 key，不重建 Workspace Root。
- 文件复制 → 缩略图 → DB 写入与 commit；常规异常清理本次副本、缩略图和临时文件并回滚 DB。复制、缩略图、Repository 写入和 commit 注入失败均已验证。缩略图和上传临时文件名称冲突均不会覆盖或删除其他操作的已有文件。
- 上传断开及工作空间在上传途中切换会清理临时文件；切换后拒绝把旧文件写入新 DB。提交阶段沿用匹配数据库 / storage 的资源租约。
- 重复导入同样内容创建独立 UUID 副本；checksum 记录相同，但不做隐式去重。绑定同一 Asset 不产生新文件。源文件导入后删除不影响托管副本。

## 删除策略

- 资产被项目或镜头引用时返回 **409 ASSET_IN_USE**，要求先解绑再软删除；没有静默删除文件。
- Project / Scene / Shot 删除保持原有行为，Asset 本体和文件不受影响。已软删除 Project / Shot 的引用也计为占用，详情明确标注且允许解除，避免未来恢复后产生 broken reference。
- Asset 软删除后普通列表、详情与文件 API 均不可见，原文件、缩略图和标签关系保留。API 提供 include_deleted / restore；没有永久删除、回收站 UI 或导出能力。

## API

详细参数见 [README Asset API](README.md#asset-api) 或运行后的 `/api/docs`。全部路径有 `/api` 前缀。

| 方法 | 地址 |
| --- | --- |
| GET / POST | `/assets`（列表） / `/assets/upload`（二进制上传） |
| GET / PATCH / DELETE | `/assets/{id}` |
| POST | `/assets/{id}/restore` |
| GET | `/assets/{id}/file`、`/assets/{id}/thumbnail` |
| GET / POST | `/tags` |
| POST / DELETE | `/assets/{id}/tags/{tag_id}` |
| POST | `/projects/{project_id}/assets`、`/shots/{shot_id}/assets` |
| DELETE | `/projects/{project_id}/assets/{asset_id}`、`/shots/{shot_id}/assets/{asset_id}` |

资产列表支持 search、asset_type、tag_id、project_id、shot_id、include_deleted、offset、limit。统一错误 `{code, message, details}`；覆盖 INVALID_MEDIA、UNSUPPORTED_FILE、EMPTY_FILE、FILE_TOO_LARGE、INVALID_ASSET_TYPE、ASSET_IN_USE、ASSET_NOT_FOUND、WORKSPACE_CHANGED 等。

## 最终验收结果

| 检查 | 实际结果 |
| --- | --- |
| frontend lint | **PASS，无错误 / 警告** |
| TypeScript / Vite build | **PASS** |
| backend pytest | **109/109 PASS，无跳过**（原 81 项 + 28 项资产用例） |
| Ruff check / format | **PASS，52 个 Python 文件** |
| browser production/build | **26/26 PASS，无跳过**（原 22 项 + 4 项资产用例） |
| browser development | **28/28 PASS，无跳过**（含原公共组件开发验收） |
| Alembic CLI | 独立 `.workspace/phase3-migration`：upgrade head → downgrade 0002_core_workflow → upgrade head 全通过 |
| Alembic current / check | **0003_asset_library (head)**；No new upgrade operations detected |
| 数据迁移 | pytest 验证已有 Phase 2 项目 / 剧本 / 场景 / 镜头升级与带引用数据回退再升级后保留、完整 downgrade base → upgrade、metadata / FK 一致性 |
| git diff --check | **PASS** |

后端覆盖全部支持格式、真实内容识别、源文件删除后独立性、无效 / 超限 / 截断媒体、分页与字面搜索、标签去重、重复关系、引用保护、软删除 / 恢复、部分失败、断开 / 切换、文件与 DB 提交补偿。

浏览器覆盖正常导入、多文件中夹杂坏文件、视频拖入 / metadata / 播放、Grid / List、搜索 / 类型 / 标签筛选、编辑、标签、项目 / 镜头绑定与刷新持久化、拒绝删除被引用资产、解除关系、Loading / Empty / Error / Retry、导入防重。原 Project / Script / Scene / Shot CRUD、排序、Select 几何布局、深浅色、Workspace 信息与代理启动全部通过。

## 隔离与资源

- 用户明确表示无需验证真实素材，本轮没有访问或导入真实 SPF 素材，也未写入 `D:\AI-Video-Workspace`。
- pytest 使用临时 Workspace；npm test 为每轮创建 `.workspace/e2e/run-*`，bootstrap、DB、夹具、assets、thumbnails、temp 均在隔离目录。成功后服务退出再清理该次目录；失败目录保留排查。直接 Playwright 使用 `.workspace/e2e` 默认隔离目录。
- 自动审批曾拦截清理失败运行目录 `run-kHtmWX` 的命令，理由仅为 blocked by policy；未绕过，保留该 Git 忽略的测试目录。最终两轮成功运行目录均由正常测试脚本自动清理。
- 只提交代码、文档、截图；不提交 Workspace、DB、合成测试素材文件、.env、缓存或 API Key。测试素材由小型确定性脚本现场生成。

## 新增依赖

| 名称 | 锁定版本 | 用途 | 本机安装体积 |
| --- | --- | --- | --- |
| Pillow | 12.3.0 | 图片签名 / 解码、EXIF 方向、metadata、JPEG 缩略图 | 约 14.08 MiB |
| PyAV / av | 18.1.0 | 本地视频容器 / 时长 / 首帧解码；wheel 内含 FFmpeg 库 | 约 66.07 MiB |

修改 backend/pyproject.toml 与 uv.lock，无新增前端或系统依赖，不安装 FFmpeg CLI、NumPy、大型运行环境或后台队列。原有后端依赖没有升级。依据：[Pillow Image](https://pillow.readthedocs.io/en/stable/reference/Image.html)、[PyAV](https://github.com/PyAV-Org/PyAV)。

## UI 截图

全部来自真实浏览器与隔离测试数据库，合成图片明确标记 SPF TEST，并非真实 SPF 项目素材。已人工查看关键深浅色截图。

| 页面 | Dark | Light |
| --- | --- | --- |
| Grid / Import | [截图](docs/screenshots/phase3-grid-dark.png) | [截图](docs/screenshots/phase3-grid-light.png) |
| List / Search / Filter | [截图](docs/screenshots/phase3-list-dark.png) | [截图](docs/screenshots/phase3-list-light.png) |
| DetailSheet / Preview | [截图](docs/screenshots/phase3-detail-dark.png) | [截图](docs/screenshots/phase3-detail-light.png) |
| Tags / Project / Shot binding | [截图](docs/screenshots/phase3-bindings-dark.png) | [截图](docs/screenshots/phase3-bindings-light.png) |

## 真实限制

- 单文件 512 MiB，图像 / 视频解码尺寸不超过 4000 万像素。Other 仅为支持媒体的分类，不接收任意文档 / 可执行文件。
- 视频检查容器、有效时长和首个可解码帧，不逐帧扫描整段完整性。原文件不转码，浏览器播放能力取决于格式 / codec，部分 MOV 等只保证 metadata 与缩略图，提供原文件入口。
- 常规失败有补偿，但文件系统与 SQLite 不是跨资源原子事务；进程强制终止 / 断电或清理操作本身遇到磁盘故障仍可能留下文件。本阶段没有后台任务或崩溃恢复日志。
- 同一服务进程内的提交沿用 Workspace 租约串行化，大视频处理可能短暂等待。没有引入多进程生产部署、虚拟列表或复杂资源队列。
- 主 JS chunk 646.49 kB / gzip 约 202.60 kB；资产页面单独懒加载约 16.83 kB / gzip 6.23 kB。既有 Vite 大于 500 kB、Zod PURE 注释和 Python 依赖弃用提示仍存在，没有隐藏警告或升级无关依赖。

**Phase 3 完成后停止开发，等待用户验收。**
