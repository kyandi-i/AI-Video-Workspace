# AI Video Workspace

本地优先的 AI 视频制作工作台。需求来源为 [MVP v0.1 开发规格](<AI Video Workspace · MVP v0.1 开发规格.md>)。

**当前完成 Phase 4：Character / CharacterState。** 已支持 Project / Script / Scene / Shot 核心工作流、统一图片 / 视频资产库、托管导入、缩略图、标签及项目 / 镜头绑定。数据保存在本地 SQLite 与 Managed Storage。已支持项目角色、视觉状态、参考资产与镜头状态绑定。Prompt / Storyboard 工作流 / VideoResult 尚未实现。范围见 [PROJECT_PLAN.md](PROJECT_PLAN.md)。

## 环境

- Node.js 22.12+（本次验证使用 24.13.0），npm。
- Python 3.12+（本次验证使用 3.12.11），[uv](https://docs.astral.sh/uv/getting-started/installation/)。
- 无需 Docker、外部数据库、账号或 AI API Key。

## 首次安装

在项目根目录运行：

```powershell
uv sync --locked --project backend
npm --prefix frontend ci
npm --prefix frontend run build
```

后端依赖锁定在 `backend/uv.lock`，前端依赖锁定在 `frontend/package-lock.json`。

## 启动

在根目录执行：

```powershell
uv run --locked --project backend python scripts/start.py
```

自动打开 <http://127.0.0.1:8765>。FastAPI 同时托管构建后的 React 页面和 API。终端按 `Ctrl+C` 关闭本次启动的服务。代码更改后重新执行前端构建，或使用开发模式。

Windows 也可使用：

```powershell
.\start.ps1
```

如果 PowerShell 执行策略阻止脚本，直接使用上面的 `uv run` 命令，无需修改系统执行策略。

开发模式（Vite HMR + FastAPI reload）：

```powershell
uv run --locked --project backend python scripts/start.py --dev
```

浏览器地址为 <http://127.0.0.1:5173>，Vite 将 `/api` 代理到本地后端。启动器等待服务就绪后打开浏览器；任何服务异常退出时会清理它启动的其他进程。

可选参数：

```powershell
uv run --locked --project backend python scripts/start.py --port 8877 --no-browser
uv run --locked --project backend python scripts/start.py --dev --port 8877 --frontend-port 5273
```

`start.ps1` 对应参数为 `-Dev`、`-Port`、`-FrontendPort`、`-NoBrowser`。端口被占用时会报错，不会终止已有服务。服务仅绑定回环地址。

分别启动前后端时，在两个终端中运行：

```powershell
# 终端一，项目根目录
uv run --locked --project backend uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload

# 终端二，项目根目录
npm --prefix frontend run dev
```

## 目录与边界

```text
backend/
  app/
    api/routes/       # 健康检查、Workspace、项目层级与资产 API
    core/             # Bootstrap、数据库实例、统一异常与路径校验
    models/           # UUID/UTC/SoftDelete BaseModel、设置、项目层级与统一资产 / 关联表
    schemas/          # Pydantic 请求/响应契约
    repositories/     # BaseRepository + 各业务 Repository，默认忽略软删除记录
    services/         # Workflow / AssetService / Workspace；storage/ Service 与 Provider
    migrations/       # 0001_app_settings → 0002_core_workflow → 0003_asset_library → 0004_characters
  tests/
frontend/
  src/
    app/              # Router、Query Provider
    api/              # API 客户端
    components/       # 布局和 shadcn/ui 基础组件
    features/         # dashboard/settings/projects/scripts/scenes/shots/assets/characters
    lib/
  tests/              # Playwright 浏览器验收
scripts/start.py      # 本地启动和子进程清理
start.ps1            # Windows 启动入口
```

技术栈固定为 React / TypeScript / Vite / Tailwind CSS / shadcn/ui 与 FastAPI / SQLAlchemy / Alembic / Pydantic / SQLite。路由不直接执行 SQL、文件读写业务或 AI 请求。UI 图标统一为 lucide-react 命名导入的本地 SVG 组件，不依赖外部图片、字体、图标 API 或 CDN。

## 项目制作流程

1. 打开侧栏 **Projects**，创建项目并打开。
2. 在 **Script** 创建剧本，再添加场景；场景中可维护描述、固定约束与负面约束。
3. 在场景中创建镜头，填写项目内唯一的镜头编号、标题、时长、状态与创作要求。
4. 用上移 / 下移调整场景内镜头顺序；到 **Shots** 按编号或标题搜索，组合场景、状态筛选。
5. 点击镜头打开基础详情并编辑，返回时保留来源页面和镜头筛选。**Scenes** 可独立查看场景并展开镜头；**Overview** 显示真实数量。

全部创建、编辑和删除均写入本地数据库。业务数据不进入 localStorage。删除必须确认，Project / Script / Scene 会联动软删除后代；没有永久删除接口或 Recycle Bin 页面。Scene 删除同步软删除 ScriptNode 与 Shot。镜头编号区分大小写，软删除后仍保留唯一占用，可通过恢复接口恢复原记录。

Scene 的名称、描述和约束由 Scene 唯一维护；SCENE 节点的 title / description 留空。场景顺序仅在 ScriptNode 维护，API 中的 Scene.order_index 是投影。Shot 顺序由后端分配，删除和移动后连续，恢复的单个镜头追加到末尾。

## Core Workflow API

完整输入、输出契约见本地 `/api/docs`。Create / Update / Read schema 分离；PATCH 省略字段表示保留原值，显式 null 和未知字段返回 422。

| 资源 | 列表 / 创建 | 详情 / 更新 / 删除 |
| --- | --- | --- |
| Projects | `GET/POST /api/projects` | `GET/PATCH/DELETE /api/projects/{id}` |
| Scripts | `GET/POST /api/projects/{project_id}/scripts` | `GET/PATCH/DELETE /api/scripts/{id}` |
| Scenes | `GET/POST /api/projects/{project_id}/scenes` | `GET/PATCH/DELETE /api/scenes/{id}` |
| Shots | `GET/POST /api/scenes/{scene_id}/shots` | `GET/PATCH/DELETE /api/shots/{id}` |

- Scene 创建传入 `script_id`；Shot 创建传入 `project_id`。Service 校验它们与 URL 上的父级关系。
- `GET /api/projects/{id}/shots` 支持 `search`、`scene_id`、`status`；`GET /api/projects/{id}/stats` 返回 scripts / scenes / shots 实际数量。
- `POST /api/shots/{id}/move`：`{"direction":"up"}` 或 `{"direction":"down"}`，返回场景内最终顺序，边界移动不改变顺序。
- 四类资源列表、详情均支持 `include_deleted=true`，默认隐藏软删除记录；`POST /api/{projects|scripts|scenes|shots}/{id}/restore` 恢复记录。恢复后代前必须先恢复父级；恢复父级只恢复同一次级联删除的后代，不恢复此前单独删除的记录。
- 错误保持 `{code,message,details}`：不存在为 404，镜头编号冲突为 409，跨项目关系为 400，输入验证为 422。

## Characters / Character States

1. 从项目导航或 Overview 打开 **Characters**，创建角色身份，填写描述与长期约束 / 备注。
2. 打开角色详情，在 **Character Reference Assets** 绑定已有 Asset，或用 Import Asset 托管导入并自动绑定。
3. 创建角色的视觉状态，维护名称、描述、参考素材；使用上移 / 下移调整顺序。
4. 在现有 Shot Detail 的 **Characters** 区域选择角色和状态，点击 **Add Character State**。同镜头可有多个角色，每个角色只允许一个状态，且必须属于同一项目。
5. 被镜头使用的状态不能单独删除。删除角色会级联删除状态并解除关系，不删除 Asset；恢复只恢复同次删除的状态，参考和镜头关系需重新绑定。角色及状态列表提供“显示已删除 / 恢复”。

Character 是身份，CharacterState 是视觉阶段，实际图片 / 视频仍统一为 Asset。名称在项目 / 角色内唯一，区分大小写，软删除后保留占用。Asset 删除保护已包含 Character / State 引用。无新依赖。

新增 API 与模型字段、删除规则、135项后端 / 31项生产浏览器 / 33项开发浏览器验收及两种主题截图见 [Phase 4 状态](docs/PHASE_4_STATUS.md)。本阶段只给 Shot Detail 增加基础绑定入口，未实现 Phase 5 Workspace。

## Phase 2.5 UX 修正

- 修复公共 Select 未选中项被误绝对定位的问题；Trigger / Item 均为 36px，文字与勾选标记各有独立区域。菜单支持键盘导航、长文本省略与视口边界约束。
- Project / Shot 的状态选项、筛选器与 Badge 共用 `lib/status-display.ts`，通过 `lib/enum-display.ts` 生成 value → label 选项。显示 `Storyboard Prompt Ready` 等友好文案，API 仍提交原始枚举；未来枚举沿用该机制，页面不得自行格式化。
- 表单单行控件 36px、列表小按钮 / 图标按钮 32px；Textarea 使用多行规格。Dialog 标题 / Footer 固定，字段区滚动；取消在左、保存 / 删除在右，提交中禁用并拦截重复操作。
- 统一状态 Badge、长标题截断、删除影响说明、Empty / Error 状态；移动镜头原子应用后端返回的顺序。Shots 搜索与筛选保留在 URL，打开镜头并返回无需重新设置。
- 后端业务模型、API、数据库迁移与依赖保持不变。本次没有新增业务能力，未进入 Asset Library。

截图（隔离测试数据）：[Dark Select](docs/screenshots/phase-2.5-shot-select-dark.png)、[Light Select](docs/screenshots/phase-2.5-shot-select-light.png)、[Project Select](docs/screenshots/phase-2.5-project-select-light.png)、[Shots](docs/screenshots/phase-2.5-shots-dark.png)。完整验收见 [开发状态](DEVELOPMENT_STATUS.md)。

## UI Foundation

- 默认 Dark，Topbar 与 Settings 可切换 Light。浏览器 localStorage 只保存 `avw.ui.theme`；业务数据仍保存到 Workspace。
- Dashboard 展示真实连接、存储状态和最近更新项目；Projects 进入实际项目业务。Settings 提供主题切换、工作空间信息与绝对路径输入切换。切换复用原有 API，不自动迁移文件。
- 公共视觉规则、完整 Token 表和组件 API 见 [UI Foundation](docs/UI_FOUNDATION.md)。颜色统一维护于 `frontend/src/styles/tokens.css`，组件源码位于 `frontend/src/components/ui` 与 `components/common`。
- 开发模式可访问 <http://127.0.0.1:5173/__ui> 验收基础组件。该路由在生产构建中不可用。
- Phase 2 截图（独立 E2E 测试项目）：[Dark Script](docs/screenshots/phase-2-script-dark.png)、[Light Shots](docs/screenshots/phase-2-shots-light.png)。历史 UI Foundation：[Dark](docs/screenshots/phase-1.5-dark.png)、[Light](docs/screenshots/phase-1.5-light.png)。[资源审计报告](docs/RESOURCE_AUDIT_2026-09-20.md) 为 UI 开发前的基线，资源变化见开发状态。

## 本机资源路径

- 当前业务 Workspace Root：`D:\AI-Video-Workspace`。2026-09-22 的 Phase 3.1 已完整复制并验证 C 盘真实 Phase 3 数据，随后通过既有 BootstrapConfig 保存选择。此前 Bootstrap 虽指向 D，但 D 只有 Phase 1 空库，旧文档“迁移完成”的说法不准确。Phase 3.1 当时保留了原 `C:\Users\Lenovo\AI-Video-Workspace` 安全副本，但 Phase 4 实机复查未找到该路径；本轮没有删除或移动它。Phase 4 迁移前另备份了 D 盘数据库至其 backups 目录。详见 [迁移验收](docs/PHASE_3_1_STATUS.md)。
- Playwright 浏览器：`D:\study\DO\DevCache\playwright`。`npm test` 和 `npm run test:install` 都通过项目级脚本固定该路径；`frontend/playwright.config.ts` 也为直接测试命令设置同一环境变量。
- 重新安装当前 Chromium 时运行 `npm --prefix frontend run test:install`。本次未删除 C 盘既有 `ms-playwright`，因为其中可能包含其他项目使用的版本。

## 安全迁移 Workspace

Settings 中输入目标绝对路径并“保存并切换工作空间”，调用现有 `PUT /api/settings/workspace`。成功后重新载入页面，清空旧 Workspace 查询缓存；失败保留当前选择与输入。空目录会初始化为空 Workspace，这属于 **Switch Workspace**，不会自动复制数据。

迁移已有 Workspace 时按顺序操作：

1. 停止所有使用该 Workspace 的应用进程，确认数据库没有写入。
2. 清点整个目录；若目标已有内容，先备份并确认，不能盲目合并或覆盖其他 Workspace。
3. 完整 COPY 所有文件、子目录（包括 data、storage、temp、exports、backups 及未知扩展名），保留源目录。
4. 比较文件清单、大小和 SHA-256，至少校验 workspace.db；数据库 Asset 路径必须为 Workspace 相对路径，发现绝对路径应停止并报告。
5. 校验通过后，通过现有 BootstrapConfig 或 Settings 切换到副本，不在数据库中存放定位自己的 root。
6. 重启，核对实际数据库 / 文件解析、原有数据和一次新上传，新文件应仅写入目标目录；清理该人工测试资产。
7. 保留旧 Workspace，等待用户确认后才可删除。

本阶段未新增自动迁移 API 或 Workspace Manager，也未硬编码产品根目录。pytest、Playwright、Alembic 回退回升必须同时隔离 Bootstrap 与 Workspace，不能使用真实业务目录。

## 配置与数据

可复制 `backend/.env.example` 为 `backend/.env`。环境变量前缀为 `AVW_`；相对工作空间路径始终相对于仓库根目录解析，不依赖启动目录。

默认 Workspace 为 `~/AI-Video-Workspace`。首次服务启动自动创建下列目录，并通过 **Alembic upgrade head** 初始化数据库；应用不使用 `create_all()` 管理 Schema。

```text
<workspace_root>/
  data/workspace.db
  storage/assets/
  storage/thumbnails/
  storage/temp/
  exports/
  backups/
```

Bootstrap Config 默认位于 Windows `%APPDATA%/AI-Video-Workspace/config.json`（其他系统为 `~/.config/AI-Video-Workspace/config.json`），仅保存 `workspace_root`。可通过 `AVW_BOOTSTRAP_CONFIG_PATH` 指定独立配置。它必须位于工作空间之外。

查找顺序：**已保存的 Bootstrap Config → AVW_WORKSPACE_ROOT → 默认目录**。`AVW_WORKSPACE_ROOT` 仅用于首次配置，后续通过 API 选择的目录在重启后继续生效；损坏的配置会明确报错，不会静默重置。若要隔离测试或另一套实例，必须同时指定独立的 bootstrap 配置路径与初始 root。

工作空间切换会验证绝对路径、创建必要目录、迁移目标数据库，再原子写入配置并替换数据库连接。旧目录不会移动或删除，正在执行的事务会先完成。配置保存或数据库初始化失败时，当前选择保持不变；目标中已经初始化的目录/数据库可能保留，应用不会冒险清理用户选中的目录。新旧工作空间不允许互相嵌套。

`backend/.env`、虚拟环境、构建产物、测试输出和 `.workspace` 已加入忽略规则。API 文档位于 <http://127.0.0.1:8765/api/docs>，健康检查位于 <http://127.0.0.1:8765/api/health>。

## Workspace API

Workspace 切换可从 Settings 使用现有 API；页面还可查看工作空间与切换主题。可在本地 Swagger 文档中调用，或使用 PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/settings/workspace

# 选择一个新的工作空间；保留旧目录，不迁移文件。
$body = @{ workspace_root = 'D:\AI-Video-Workspace-Second' } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8765/api/settings/workspace -Method Put -ContentType 'application/json' -Body $body
```

成功响应包含 `workspace_root`、`database_path`、`initialized`。错误统一为 `{code, message, details}`，支持 400 / 404 / 409 / 422 / 500；内部错误不会向客户端暴露堆栈。

## Asset Library 使用

1. 打开侧栏 **Asset Library**，点击 **Import Asset** 选择多个文件，或拖入导入区域。每个文件独立显示等待、导入中、成功或可读失败原因。
2. 默认根据实际内容识别 Image / Video。导入时或详情编辑时可选择 Storyboard 6-Grid / Other；六宫格只是图片分类，没有 Storyboard 版本工作流。
3. 使用 Grid / List、名称或原始文件名搜索、类型和标签筛选；每次加载 60 项，支持加载更多。视图、筛选与当前详情保存在 URL，刷新后保留。
4. 点击资产打开 DetailSheet，预览、重命名、描述编辑、添加 / 移除标签。在上方选择项目，再绑定项目或选择该项目镜头绑定；Shot 绑定不自动创建 Project 绑定。
5. Project 的 Assets 标签和 Shot Detail 的“查看关联资产”可查看对应素材。绑定只创建关系，不复制文件。
6. 被引用资产返回 `ASSET_IN_USE`，包括已软删除 Project / Shot 的保留引用；在详情中可解除这些绑定。资产软删除保留原文件、缩略图与标签关联，正常查询及文件 URL 隐藏；API 提供 restore，本阶段没有回收站或永久删除 UI。

支持 PNG / JPG / JPEG / WebP、MP4 / MOV / WebM，单文件上限 512 MiB，解码尺寸上限 4000 万像素。后端按文件签名与实际解码校验 MIME，前端扩展名与 MIME 不作为可信结论。Other 是已支持媒体的分类，不接受任意可执行文件或文档。

导入请求使用单文件原始二进制流，多文件由 UI 顺序提交；不转 base64，不写数据库 BLOB，不需要 multipart 依赖。所有上传临时数据流入当前 Workspace 的 `storage/temp`，正式文件使用 UUID 文件名保存至 `storage/assets/<前两位>/<uuid>.<ext>`。数据库存 `storage/assets/...`、`storage/thumbnails/...` 的 Workspace 相对路径，沿用 Provider 相对 storage 根的内部 key。原文件移动 / 删除不影响资产。

复制、缩略图和数据库提交组成一项可补偿导入：任一步异常回滚数据库并清理本次正式副本 / 缩略图 / 临时文件，单个失败不影响其他导入。工作空间在上传中切换时拒绝提交并清理旧工作空间临时文件。重复导入会创建新的 UUID 资产与副本，不按 checksum 自动去重；关联同一 Asset 不复制文件。

新增 Python 依赖只有 **Pillow 12.3.0**（图片解码 / metadata / 缩略图，安装约 14.08 MiB）与 **PyAV 18.1.0**（视频 metadata / 首帧，含本地 FFmpeg 库，安装约 66.07 MiB）。无新增前端或系统依赖；无需安装 FFmpeg 命令行、NumPy 或后台队列。依赖版本锁在 uv.lock。安装方式仍为 `uv sync --locked --project backend`。

列表只加载缩略图；详情图片按需加载原图，视频有 controls、preload=metadata，不自动播放，原文件 API 支持 HTTP Range。浏览器是否播放取决于容器 / 编码支持，不能播放时仍提供缩略图、metadata 与原文件入口；不转码整段视频。

### Asset API

所有地址均有 `/api` 前缀，统一错误结构仍为 `{code, message, details}`。

| 方法 | 路径 / 能力 |
| --- | --- |
| GET | `/assets`：search、asset_type、tag_id、project_id、shot_id、include_deleted、offset、limit |
| POST | `/assets/upload?filename=...&asset_type=...`：Content-Type application/octet-stream，body 为单个文件；asset_type 可省略 |
| GET / PATCH / DELETE | `/assets/{id}`：详情、基本信息编辑、软删除 |
| POST | `/assets/{id}/restore` |
| GET | `/assets/{id}/file`、`/assets/{id}/thumbnail` |
| GET / POST | `/tags`：列出、创建或复用规范化名称 |
| POST / DELETE | `/assets/{id}/tags/{tag_id}`：关联 / 解除标签 |
| POST | `/projects/{project_id}/assets`、`/shots/{shot_id}/assets`，body `{asset_id}` |
| DELETE | `/projects/{project_id}/assets/{asset_id}`、`/shots/{shot_id}/assets/{asset_id}`：解除关联 |

标签采用 Unicode NFKC、空白折叠和 casefold 去重；名称不超过 80 字符。关联表均有 UUID、时间戳、deleted_at 与关系唯一约束，重复绑定幂等，重新绑定恢复同一 Link。

[Dark Grid](docs/screenshots/phase3-grid-dark.png) · [Light List](docs/screenshots/phase3-list-light.png) · [Dark DetailSheet](docs/screenshots/phase3-detail-dark.png) · [Light Binding](docs/screenshots/phase3-bindings-light.png)。全部截图使用隔离 E2E 合成素材，未导入用户真实 SPF 素材。

## 数据访问与存储约定

`Database` 实例提供 `engine` 和 `SessionLocal`，`get_db()` 从请求当前 Workspace 获取会话，不使用随切换变化的模块级全局连接。服务事务成功时提交，异常时回滚；Repository 只 flush，不自行 commit。

`BaseModel` 组合 UUID、Timestamp、SoftDelete mixin。UUID 在 Python 中为 `uuid.UUID`，使用 SQLAlchemy `Uuid` 在 SQLite / PostgreSQL 间适配。时间在数据库中存为无偏移 UTC，读出统一为带 UTC 时区的 datetime；拒绝无时区的时间输入。`get/list` 默认忽略已删除记录，需要显式 `include_deleted=True`；默认删除使用 `soft_delete`，可以 `restore`。设置键在软删除后仍保留唯一性，可恢复该记录。

普通设置存于 `app_settings`。Workspace Root 在外部 Bootstrap Config 中；该表不用于保存 API Key。

StorageProvider 返回原文件名、UUID 文件名、相对路径、字节数和 SHA-256。文件先复制到 `storage/temp`，完整写入并 fsync 后才发布到 `assets/<前两位>/<UUID>.<扩展名>`，避免半文件成为有效对象。重复名称不覆盖；原始文件删除不影响托管副本。Windows 使用拒绝覆盖的原子 rename；其他系统使用同文件系统硬链接发布再移除临时名称。

路径检查覆盖绝对路径、`..`、Windows 盘符/ADS、保留名称、符号链接、目录联接和被替换的根目录。删除仅处理普通文件，不递归删除目录。图片与视频首帧缩略图由 Pillow / PyAV 在本地生成，长边不超过 512px，JPEG 文件保存到 storage/thumbnails。

后续涉及数据库与文件的服务应租用同一个工作空间并将**数据库提交**放入补偿范围：

```python
with workspace.resources() as (database, storage):
    with storage.save_with_compensation(source_file) as stored:
        with database.session() as session:
            # repository.add(...)；持久化 stored.relative_path，不能保存绝对路径。
            ...
```

外层资源租约阻止切换，内层提交失败会删除新导入文件。不要在该租约内再次调用会申请租约的 `workspace.session()` 或 `set_workspace_root()`。目前只支持单进程本地服务；文件补偿不等于跨数据库/文件系统的崩溃原子事务，进程强制退出时可能留下无引用文件，本阶段已有引用保护，但尚无崩溃恢复日志或永久文件清理。

## 验证

在根目录运行：

```powershell
uv run --locked --project backend pytest backend/tests
uv run --locked --project backend ruff check backend/app backend/tests scripts
uv run --locked --project backend ruff format --check backend/app backend/tests scripts
npm --prefix frontend run lint
npm --prefix frontend run build
uv run --locked --project backend alembic -c backend/alembic.ini heads
uv run --locked --project backend alembic -c backend/alembic.ini upgrade head --sql
```

当前 head 是 `0004_characters`，新增 characters / character_states / character_asset_links / character_state_asset_links / shot_character_state_links，保留全部 Phase 1–3 数据表。测试在独立临时数据库中验证 upgrade → downgrade base → upgrade，以及 autogenerate、metadata 一致性、UUID、UTC、软删除、事务回滚和路径安全。自动生成验收在迁移目录副本中运行，不污染正式 revision。

常用迁移命令（项目根目录；操作的是 bootstrap 当前选中的工作空间）：

```powershell
uv run --locked --project backend alembic -c backend/alembic.ini current
uv run --locked --project backend alembic -c backend/alembic.ini upgrade head
uv run --locked --project backend alembic -c backend/alembic.ini check
uv run --locked --project backend alembic -c backend/alembic.ini revision --autogenerate -m "describe schema change"
```

`downgrade 0003_asset_library` 会删除 Phase 4 五张角色 / 关联表；`downgrade 0002_core_workflow` 还会删除资产 / 关联表但保留项目层级；`downgrade 0001_app_settings` 会删除全部业务表；`downgrade base` 还会删除设置表。回退只在独立测试 Workspace 中执行。业务模型加入 `app/models/__init__.py` 后才能被 Alembic 发现。跨数据库可迁移性已做 PostgreSQL DDL 编译检查，本阶段未连接真实 PostgreSQL 服务。

浏览器测试需先构建前端，并首次安装 Chromium：

```powershell
Set-Location frontend
npm run test:install
npm test
# 验证 Vite 开发代理与开发启动入口
$env:AVW_E2E_MODE = 'dev'
npm test
Remove-Item Env:AVW_E2E_MODE
```

测试自动启动并关闭服务，使用后端 8766 和开发前端 5174 端口，最多 2 个测试 worker。npm test 为每次运行建立 `.workspace/e2e/run-*` 独立配置、数据库与小型图片 / 视频夹具；成功后待服务退出再清理该运行目录，失败保留供排查。直接调用 Playwright 则使用 `.workspace/e2e` 默认隔离目录。pytest 使用临时目录，不改变个人工作空间。覆盖真实 API、断线重试、主题持久化 / 存储受限 / 跨标签同步、只读详情与复制、未知页面返回、响应式布局、两套颜色对比度和截图；开发模式额外覆盖公共组件交互。无需手动先启动测试服务。Phase 2 增加两种主题下的完整业务 CRUD、顺序调整、筛选、删除确认、刷新持久化、表单验证 / pending / API 冲突与 404 测试。

## 后续开发

项目使用本地 Git 版本控制，默认分支为 `main`。首次基线包含 Phase 0 与 Phase 1 的代码、测试、需求文档和依赖锁文件。本地 Workspace、数据库、环境配置、依赖目录及构建产物不纳入版本控制。尚未配置远程仓库。

```powershell
git status
git log --oneline
```

查看 [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) 和 [Phase 2 实现约定](docs/PHASE_2_SPEC.md)。Phase 4 已完成并暂停，详见 [Phase 4 验收](docs/PHASE_4_STATUS.md)；不自动进入 Phase 5。

初始化参考官方文档：[Vite](https://vite.dev/guide/)、[Tailwind Vite 集成](https://tailwindcss.com/docs/installation/using-vite)、[shadcn/ui 手动安装](https://ui.shadcn.com/docs/installation/manual)、[FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)。

数据库实现参考：[SQLAlchemy Uuid](https://docs.sqlalchemy.org/en/20/core/type_basics.html)、[UTC 自定义类型](https://docs.sqlalchemy.org/en/20/core/custom_types.html)、[Alembic 共享连接](https://alembic.sqlalchemy.org/en/latest/cookbook.html)、[迁移自动生成](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)。
