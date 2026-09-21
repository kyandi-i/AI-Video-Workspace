# AI Video Workspace

本地优先的 AI 视频制作工作台。需求来源为 [MVP v0.1 开发规格](<AI Video Workspace · MVP v0.1 开发规格.md>)。

**当前完成 Phase 2.5：现有工作流 UX 修正。** 已可在深浅色工作台中创建项目、剧本、场景与镜头，编辑、软删除、排序、搜索与筛选，数据保存在本地 SQLite。Asset / Character / Prompt / Storyboard / VideoResult 尚未实现。范围见 [PROJECT_PLAN.md](PROJECT_PLAN.md)，每次开发只推进一个 Phase。

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
    api/routes/       # 健康检查、Workspace 与项目层级 API
    core/             # Bootstrap、数据库实例、统一异常与路径校验
    models/           # UUID/UTC/SoftDelete BaseModel、设置与五张业务表
    schemas/          # Pydantic 请求/响应契约
    repositories/     # BaseRepository + 各业务 Repository，默认忽略软删除记录
    services/         # Project/Script/Scene/Shot 与 Workspace Service；storage/ 抽象
    migrations/       # 0001_app_settings → 0002_core_workflow
  tests/
frontend/
  src/
    app/              # Router、Query Provider
    api/              # API 客户端
    components/       # 布局和 shadcn/ui 基础组件
    features/         # dashboard/settings/projects/scripts/scenes/shots
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

## Phase 2.5 UX 修正

- 修复公共 Select 未选中项被误绝对定位的问题；Trigger / Item 均为 36px，文字与勾选标记各有独立区域。菜单支持键盘导航、长文本省略与视口边界约束。
- Project / Shot 的状态选项、筛选器与 Badge 共用 `lib/status-display.ts`，通过 `lib/enum-display.ts` 生成 value → label 选项。显示 `Storyboard Prompt Ready` 等友好文案，API 仍提交原始枚举；未来枚举沿用该机制，页面不得自行格式化。
- 表单单行控件 36px、列表小按钮 / 图标按钮 32px；Textarea 使用多行规格。Dialog 标题 / Footer 固定，字段区滚动；取消在左、保存 / 删除在右，提交中禁用并拦截重复操作。
- 统一状态 Badge、长标题截断、删除影响说明、Empty / Error 状态；移动镜头原子应用后端返回的顺序。Shots 搜索与筛选保留在 URL，打开镜头并返回无需重新设置。
- 后端业务模型、API、数据库迁移与依赖保持不变。本次没有新增业务能力，未进入 Asset Library。

截图（隔离测试数据）：[Dark Select](docs/screenshots/phase-2.5-shot-select-dark.png)、[Light Select](docs/screenshots/phase-2.5-shot-select-light.png)、[Project Select](docs/screenshots/phase-2.5-project-select-light.png)、[Shots](docs/screenshots/phase-2.5-shots-dark.png)。完整验收见 [开发状态](DEVELOPMENT_STATUS.md)。

## UI Foundation

- 默认 Dark，Topbar 与 Settings 可切换 Light。浏览器 localStorage 只保存 `avw.ui.theme`；业务数据仍保存到 Workspace。
- Dashboard 展示真实连接、存储状态和最近更新项目；Projects 进入实际项目业务。Settings 提供主题切换与只读工作空间信息。
- 公共视觉规则、完整 Token 表和组件 API 见 [UI Foundation](docs/UI_FOUNDATION.md)。颜色统一维护于 `frontend/src/styles/tokens.css`，组件源码位于 `frontend/src/components/ui` 与 `components/common`。
- 开发模式可访问 <http://127.0.0.1:5173/__ui> 验收基础组件。该路由在生产构建中不可用。
- Phase 2 截图（独立 E2E 测试项目）：[Dark Script](docs/screenshots/phase-2-script-dark.png)、[Light Shots](docs/screenshots/phase-2-shots-light.png)。历史 UI Foundation：[Dark](docs/screenshots/phase-1.5-dark.png)、[Light](docs/screenshots/phase-1.5-light.png)。[资源审计报告](docs/RESOURCE_AUDIT_2026-09-20.md) 为 UI 开发前的基线，资源变化见开发状态。

## 本机资源路径

- 当前业务 Workspace Root：`D:\AI-Video-Workspace`。启动配置仍由用户级 Bootstrap Config 管理，但两个 Windows 配置位置都已指向该 D 盘目录；原 `C:\Users\Lenovo\AI-Video-Workspace` 保留为迁移前副本，不再作为当前业务 Workspace 使用。
- Playwright 浏览器：`D:\study\DO\DevCache\playwright`。`npm test` 和 `npm run test:install` 都通过项目级脚本固定该路径；`frontend/playwright.config.ts` 也为直接测试命令设置同一环境变量。
- 重新安装当前 Chromium 时运行 `npm --prefix frontend run test:install`。本次未删除 C 盘既有 `ms-playwright`，因为其中可能包含其他项目使用的版本。

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

Workspace 切换仍仅提供 API 入口；Settings 页面可查看工作空间与切换主题。可在本地 Swagger 文档中调用，或使用 PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/settings/workspace

# 选择一个新的工作空间；保留旧目录，不迁移文件。
$body = @{ workspace_root = 'D:\AI-Video-Workspace-Second' } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8765/api/settings/workspace -Method Put -ContentType 'application/json' -Body $body
```

成功响应包含 `workspace_root`、`database_path`、`initialized`。错误统一为 `{code, message, details}`，支持 400 / 404 / 409 / 422 / 500；内部错误不会向客户端暴露堆栈。

## 数据访问与存储约定

`Database` 实例提供 `engine` 和 `SessionLocal`，`get_db()` 从请求当前 Workspace 获取会话，不使用随切换变化的模块级全局连接。服务事务成功时提交，异常时回滚；Repository 只 flush，不自行 commit。

`BaseModel` 组合 UUID、Timestamp、SoftDelete mixin。UUID 在 Python 中为 `uuid.UUID`，使用 SQLAlchemy `Uuid` 在 SQLite / PostgreSQL 间适配。时间在数据库中存为无偏移 UTC，读出统一为带 UTC 时区的 datetime；拒绝无时区的时间输入。`get/list` 默认忽略已删除记录，需要显式 `include_deleted=True`；默认删除使用 `soft_delete`，可以 `restore`。设置键在软删除后仍保留唯一性，可恢复该记录。

普通设置存于 `app_settings`。Workspace Root 在外部 Bootstrap Config 中；该表不用于保存 API Key。

StorageProvider 返回原文件名、UUID 文件名、相对路径、字节数和 SHA-256。文件先复制到 `storage/temp`，完整写入并 fsync 后才发布到 `assets/<前两位>/<UUID>.<扩展名>`，避免半文件成为有效对象。重复名称不覆盖；原始文件删除不影响托管副本。Windows 使用拒绝覆盖的原子 rename；其他系统使用同文件系统硬链接发布再移除临时名称。

路径检查覆盖绝对路径、`..`、Windows 盘符/ADS、保留名称、符号链接、目录联接和被替换的根目录。删除仅处理普通文件，不递归删除目录。缩略图接口目前明确抛出 `NotImplementedError`，留到 Phase 3。

后续涉及数据库与文件的服务应租用同一个工作空间并将**数据库提交**放入补偿范围：

```python
with workspace.resources() as (database, storage):
    with storage.save_with_compensation(source_file) as stored:
        with database.session() as session:
            # repository.add(...)；持久化 stored.relative_path，不能保存绝对路径。
            ...
```

外层资源租约阻止切换，内层提交失败会删除新导入文件。不要在该租约内再次调用会申请租约的 `workspace.session()` 或 `set_workspace_root()`。目前只支持单进程本地服务；文件补偿不等于跨数据库/文件系统的崩溃原子事务，进程强制退出时可能留下无引用文件，后续资产模块再实现引用清理。

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

当前 head 是 `0002_core_workflow`，新增 projects / scripts / script_nodes / scenes / shots，保留原 app_settings。测试在独立临时数据库中验证 upgrade → downgrade base → upgrade，以及 autogenerate、metadata 一致性、UUID、UTC、软删除、事务回滚和路径安全。自动生成验收在迁移目录副本中运行，不污染正式 revision。

常用迁移命令（项目根目录；操作的是 bootstrap 当前选中的工作空间）：

```powershell
uv run --locked --project backend alembic -c backend/alembic.ini current
uv run --locked --project backend alembic -c backend/alembic.ini upgrade head
uv run --locked --project backend alembic -c backend/alembic.ini check
uv run --locked --project backend alembic -c backend/alembic.ini revision --autogenerate -m "describe schema change"
```

`downgrade 0001_app_settings` 会删除五张业务表；`downgrade base` 还会删除设置表。回退只在独立测试 Workspace 中执行。业务模型加入 `app/models/__init__.py` 后才能被 Alembic 发现。跨数据库可迁移性已做 PostgreSQL DDL 编译检查，本阶段未连接真实 PostgreSQL 服务。

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

测试自动启动并关闭服务，使用后端 8766 和开发前端 5174 端口，最多 2 个测试 worker。Playwright 使用仓库 `.workspace/e2e` 中的隔离配置与数据，不改变个人工作空间；pytest 使用临时目录。覆盖真实 API、断线重试、主题持久化 / 存储受限 / 跨标签同步、只读详情与复制、未知页面返回、响应式布局、两套颜色对比度和截图；开发模式额外覆盖公共组件交互。无需手动先启动测试服务。Phase 2 增加两种主题下的完整业务 CRUD、顺序调整、筛选、删除确认、刷新持久化、表单验证 / pending / API 冲突与 404 测试。

## 后续开发

项目使用本地 Git 版本控制，默认分支为 `main`。首次基线包含 Phase 0 与 Phase 1 的代码、测试、需求文档和依赖锁文件。本地 Workspace、数据库、环境配置、依赖目录及构建产物不纳入版本控制。尚未配置远程仓库。

```powershell
git status
git log --oneline
```

查看 [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md) 和 [Phase 2 实现约定](docs/PHASE_2_SPEC.md)。Phase 2.5 UX Fix 已完成并暂停；Phase 3（Asset Library）必须等待用户确认后才开始。

初始化参考官方文档：[Vite](https://vite.dev/guide/)、[Tailwind Vite 集成](https://tailwindcss.com/docs/installation/using-vite)、[shadcn/ui 手动安装](https://ui.shadcn.com/docs/installation/manual)、[FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)。

数据库实现参考：[SQLAlchemy Uuid](https://docs.sqlalchemy.org/en/20/core/type_basics.html)、[UTC 自定义类型](https://docs.sqlalchemy.org/en/20/core/custom_types.html)、[Alembic 共享连接](https://alembic.sqlalchemy.org/en/latest/cookbook.html)、[迁移自动生成](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)。
