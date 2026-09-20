# 开发状态

更新日期：2026-09-20

## 当前阶段

**Phase 1 · Database + Alembic + Storage Infrastructure：已完成。**

本次只实现基础设施，未进入 Phase 2。后续必须等待用户确认。需求范围见 [PROJECT_PLAN.md](PROJECT_PLAN.md) 和 [Phase 1 要求原文](docs/PHASE_1_SPEC.md)。[Phase 0 验收记录](docs/PHASE_0_STATUS.md) 已保留。

## 实现内容与架构变化

- `core/database.py`：按 Workspace 建立 Database 实例，包含 engine / SessionLocal；get_db 请求依赖、事务提交回滚、连接释放与外键约束。
- `models/base.py`：UUID、UTC Timestamp、SoftDelete mixin 和 BaseModel。应用产生 UUID，SQLite 使用 SQLAlchemy Uuid 的便携存储，PostgreSQL 可使用原生 UUID。
- `models/app_setting.py`：唯一基础设施表 app_settings，不包含项目领域模型或敏感凭据。
- `repositories/base.py`：get / list / add / update / soft_delete / restore；默认隐藏软删除数据，Repository 只 flush。
- `core/bootstrap.py`：仅保存 workspace_root 的用户级配置，临时文件写入后原子替换。解析 Windows APPDATA 重定向后的物理路径，避免跨磁盘替换错误。
- `services/workspace.py`：路径验证、幂等目录初始化、迁移目标数据库、持久化切换与旧数据库释放。资源租约确保数据库与 Storage 在同一工作空间内完成操作；旧数据不搬迁、不删除。
- `services/storage/`：StorageProvider、StorageObject、LocalStorageProvider；相对路径、UUID 文件名、原文件名、大小与 SHA-256；安全复制、读取、删除、移动和补偿上下文。
- `core/paths.py`：路径穿越、Windows 盘符/ADS/保留名、符号链接、目录联接和根目录被替换的拦截。
- `api/routes/settings.py`：最小 GET / PUT Workspace API；统一 AppError 与 400/404/409/422/500 响应。
- 前端只更新阶段提示和真实存储初始化状态；没有添加业务页面或 CRUD。
- 本地启动器保留开发/构建模式，并显式转发隐藏子进程日志。

## Alembic 状态

- 当前唯一 head：`0001_app_settings`。
- 实际默认 Workspace 已迁移至该 head；数据库中仅有 app_settings 和 alembic_version。
- 应用启动通过 Alembic 升级，不使用 create_all。
- 独立测试数据库验证 upgrade → downgrade base → upgrade。
- 在迁移目录副本内验证 revision --autogenerate 及新增测试 revision 的升降级。
- alembic check 通过，Metadata 与当前 Schema 无差异。
- UTC 自定义类型在新 revision 中渲染为稳定的 sa.DateTime，避免依赖未来变动的应用类型实现。

## 验收结果

| 类别 | 结果 |
| --- | --- |
| Phase 0 后端回归 | 4/4 通过；健康检查和无业务表断言更新为 Phase 1 的初始化/基础设施语义，保留懒构造、SPA/API 分离和缺失构建提示 |
| Database / Repository | 6/6 通过：升降级、autogenerate、UUID、UTC、软删除、恢复、回滚、唯一性和 PostgreSQL DDL 编译 |
| Workspace | 12/12 通过：初始化、幂等、切换、重启、非法路径、损坏配置/数据库、配置写失败和进行中的事务 |
| Storage / 路径 / Bootstrap 重定向 | 32/32 通过：独立副本、同名文件、读删移、19 组危险路径、Windows 目录联接、祖先目录替换、原子配置路径、部分写入清理和 DB 回滚补偿 |
| Workspace API / Error Schema | 7/7 通过 |
| pytest 合计 | **61/61 通过，无跳过** |
| Playwright 构建模式 | **4/4 通过** |
| Playwright Vite 开发模式 | **4/4 通过** |
| TypeScript / Vite build / ESLint | 通过 |
| Ruff / Ruff format | 通过 |
| 实际默认配置启动 | 通过，已修复桌面环境 APPDATA 跨磁盘重定向问题 |

pytest 使用独立临时配置和数据。Playwright 使用 `.workspace/e2e` 中的隔离配置和数据库，不修改个人 Workspace。Windows 联接安全测试实际执行，没有跳过。

已在本机实际启动 `http://127.0.0.1:8765`，Workspace API 返回已初始化，健康检查返回 phase=1 和 storage_initialized=true。首次默认 Workspace 为 `C:\Users\Lenovo\AI-Video-Workspace`；后续以 Bootstrap Config 保存的选择为准。

## 已知限制

- 不实现 Project / Script / Scene / Shot 等业务 CRUD、资产库、AI、分镜、视频结果或导出；没有完整 Settings UI，可通过 Swagger 或 Workspace API 使用基础切换功能。
- 缩略图接口已定义，当前明确 NotImplemented，留到资产导入阶段。
- 仅支持单进程本地服务；资源租约不协调其他独立服务进程或手工修改磁盘的程序。
- 文件补偿处理普通异常，不提供跨数据库/文件系统的崩溃原子事务。强制退出可能留下未引用文件或临时文件，后续资产阶段再处理引用清理。
- POSIX 的拒绝覆盖发布依赖同文件系统硬链接；Windows 使用原子 rename。当前实际运行验收平台为 Windows。
- PostgreSQL 仅验证 DDL 可编译，未连接真实 PostgreSQL 服务；MVP 仍使用 SQLite。
- 上游 Starlette 的 httpx/AnyIO 弃用提示和 Zod 打包注释提示仍存在，不影响本次验收。

## 下一阶段建议

版本控制已建立：本地 Git 仓库使用 `main` 分支，以已完成的 Phase 0 + Phase 1 为首次基线。源码、测试、需求和锁文件纳入管理；Workspace、数据库、环境配置、依赖和构建产物通过忽略规则排除。未配置远程仓库。本次仅建立版本控制，不推进开发阶段。

**等待用户确认后，进入 Phase 2：Project / Script / Scene / Shot。**

以本阶段的 UUID BaseModel、Repository、数据库事务和 Workspace 资源边界为基础，增加项目制作层级、迁移和相应 CRUD；底层保留 ScriptNode 树结构。下一阶段的具体范围以用户确认后的计划为准。

## 阶段总览

| Phase | 内容 | 状态 |
| --- | --- | --- |
| 0 | 项目初始化 | 已完成 |
| 1 | DB + Alembic + Storage | 已完成 |
| 2 | Project / Script / Scene / Shot | 等待确认 |
| 3 | Asset Library | 待开始 |
| 4 | Character / CharacterState | 待开始 |
| 5 | Shot Workspace | 待开始 |
| 6 | Prompt Template | 待开始 |
| 7 | AI Prompt Generation | 待开始 |
| 8 | Prompt Versioning | 待开始 |
| 9 | Storyboard Workflow | 待开始 |
| 10 | Video Result | 待开始 |
| 11 | Export / Recycle Bin / UX | 待开始 |
