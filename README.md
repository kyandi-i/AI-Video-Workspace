# AI Video Workspace

本地优先的 AI 视频制作工作台。需求来源为 [MVP v0.1 开发规格](<AI Video Workspace · MVP v0.1 开发规格.md>)。

**当前完成 Phase 1：Database + Alembic + Storage Infrastructure。** 已具备数据库、Workspace 初始化与切换、安全文件存储和基础 Repository。项目、资产、Prompt 等业务功能尚未实现。范围见 [PROJECT_PLAN.md](PROJECT_PLAN.md)，每次开发只推进一个 Phase。

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
    api/routes/       # 健康检查与最小 Workspace API
    core/             # Bootstrap、数据库实例、统一异常与路径校验
    models/           # UUID/UTC/SoftDelete BaseModel、app_settings
    schemas/          # Pydantic 请求/响应契约
    repositories/     # BaseRepository，默认忽略软删除记录
    services/         # WorkspaceService；storage/ 中为存储抽象与本地实现
    migrations/       # 0001_app_settings，支持升降级和自动生成
  tests/
frontend/
  src/
    app/              # Router、Query Provider
    api/              # API 客户端
    components/       # 布局和 shadcn/ui 基础组件
    features/         # 按业务模块组织，目前只有 dashboard
    lib/
  tests/              # Playwright 浏览器验收
scripts/start.py      # 本地启动和子进程清理
start.ps1            # Windows 启动入口
```

技术栈固定为 React / TypeScript / Vite / Tailwind CSS / shadcn/ui 与 FastAPI / SQLAlchemy / Alembic / Pydantic / SQLite。路由不直接执行 SQL、文件读写业务或 AI 请求。当前首页插画由 CSS 构成，不依赖外部图片、字体或网络请求。

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

本阶段提供 API 验收入口，设置产品页面尚未实现。可在本地 Swagger 文档中调用，或使用 PowerShell：

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

当前 head 是 `0001_app_settings`，只创建基础设施表。测试在独立临时数据库中验证 upgrade → downgrade base → upgrade，以及 autogenerate、metadata 一致性、UUID、UTC、软删除、事务回滚和路径安全。自动生成验收在迁移目录副本中运行，不污染正式 revision。

常用迁移命令（项目根目录；操作的是 bootstrap 当前选中的工作空间）：

```powershell
uv run --locked --project backend alembic -c backend/alembic.ini current
uv run --locked --project backend alembic -c backend/alembic.ini upgrade head
uv run --locked --project backend alembic -c backend/alembic.ini check
uv run --locked --project backend alembic -c backend/alembic.ini revision --autogenerate -m "describe schema change"
```

`downgrade base` 会删除设置表，只在独立测试 Workspace 中执行。业务模型加入 `app/models/__init__.py` 后才能被 Alembic 发现。跨数据库可迁移性已做 PostgreSQL DDL 编译检查，本阶段未连接真实 PostgreSQL 服务。

浏览器测试需先构建前端，并首次安装 Chromium：

```powershell
Set-Location frontend
npx playwright install chromium
npm test
# 验证 Vite 开发代理与开发启动入口
$env:AVW_E2E_MODE = 'dev'
npm test
Remove-Item Env:AVW_E2E_MODE
```

测试自动启动并关闭服务，使用后端 8766 和开发前端 5174 端口。Playwright 使用仓库 `.workspace/e2e` 中的隔离配置与数据，不改变个人工作空间；pytest 使用临时目录。覆盖真实 API 连接、断线重试、未知页面返回、桌面截图和窄屏溢出。无需手动先启动测试服务。

## 后续开发

项目使用本地 Git 版本控制，默认分支为 `main`。首次基线包含 Phase 0 与 Phase 1 的代码、测试、需求文档和依赖锁文件。本地 Workspace、数据库、环境配置、依赖目录及构建产物不纳入版本控制。尚未配置远程仓库。

```powershell
git status
git log --oneline
```

查看 [DEVELOPMENT_STATUS.md](DEVELOPMENT_STATUS.md)。下一阶段建议为 Phase 2（Project / Script / Scene / Shot），必须等待用户确认后才开始。

初始化参考官方文档：[Vite](https://vite.dev/guide/)、[Tailwind Vite 集成](https://tailwindcss.com/docs/installation/using-vite)、[shadcn/ui 手动安装](https://ui.shadcn.com/docs/installation/manual)、[FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)。

数据库实现参考：[SQLAlchemy Uuid](https://docs.sqlalchemy.org/en/20/core/type_basics.html)、[UTC 自定义类型](https://docs.sqlalchemy.org/en/20/core/custom_types.html)、[Alembic 共享连接](https://alembic.sqlalchemy.org/en/latest/cookbook.html)、[迁移自动生成](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)。
