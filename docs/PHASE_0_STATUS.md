# 开发状态

更新日期：2026-09-20

## 当前阶段

**Phase 0 · 项目初始化：已完成。**

依照规格第 63 节，本次只执行 Phase 0。下次开发从 Phase 1 开始。当前交付为可启动的工程基础，不代表完整 MVP 制作闭环已完成。

## 本次交付

- React + TypeScript + Vite，Tailwind CSS 与 shadcn/ui 基础组件和配置。
- React Router 页面路由、TanStack Query 服务状态缓存、Zod 响应校验。
- 中文概览、制作流程说明、阶段提示；未实现功能标记为待开发并禁用入口。
- FastAPI 健康检查、Pydantic 响应模型、统一 HTTP/参数错误格式。
- 后端模块边界：API / Schema / Service / Repository / Model / Core。
- SQLAlchemy Base 与 Alembic 脚手架；没有提前创建业务模型或迁移版本。
- 依赖锁文件、代码检查配置、后端测试、真实后端参与的 Playwright 验收。
- Python 本地启动器与 PowerShell 入口；支持开发/构建模式、服务就绪检测、自动打开浏览器、端口校验与子进程清理。
- README、环境变量示例、忽略规则与后续 Agent 开发约定。

## 验收记录

| 检查 | 结果 |
| --- | --- |
| Python / FastAPI 实际启动 | 通过，回环地址提供健康检查与前端页面 |
| 前端 TypeScript / Vite 构建 | 通过 |
| ESLint / Ruff / Ruff format | 通过 |
| pytest | 4 项通过：健康检查不创建 Workspace、SPA 与 API 分离、缺失构建提示、迁移初始状态 |
| Playwright 构建模式 | 4 项通过 |
| Playwright Vite 开发模式 | 4 项通过，包含开发代理与 reload 启动 |
| 页面检查 | 桌面截图已检查，390px 窄屏无横向溢出 |
| Alembic heads | 通过，预期无 revision |
| Alembic upgrade head --sql | 通过，无业务迁移 SQL；未创建数据库 |
| npm audit（安装时） | 0 vulnerabilities |

浏览器验收覆盖首页与真实后端连接、断线提示和恢复、未知地址返回、桌面渲染及基础窄屏布局。Phase 0 之前仓库仅包含规格文档，没有可回归的既有业务功能；规格文件保持原样。

## 已知边界

- 尚无数据库业务表、Managed Storage、设置保存、项目/镜头 CRUD、上传、AI 调用或导出。
- Alembic 当前仅验收脚手架与空迁移链；真实数据库 upgrade/downgrade 在 Phase 1 验证。
- Workspace Root 仅在后端配置层预留。此阶段不会创建或切换工作空间。
- 上游依赖存在非阻断告警：Starlette 的 httpx/AnyIO 弃用提示，ESLint 9 维护提示，以及 Zod 注释的打包提示。构建、检查及功能测试通过；后续升级依赖应连同锁文件和回归检查一起处理。
- 当前目录原本没有 Git 元数据。本次没有自动创建提交或连接远程仓库。

## 下一阶段：Phase 1

范围：DB + Alembic + Storage 抽象。

1. 引入 UUID 领域模型与关联表，保持未来迁移 PostgreSQL 的能力。
2. 添加第一版 Alembic migration，验证新库升级、降级及再次升级。
3. 实现 Workspace 内部目录初始化与路径校验，明确切换而非隐式迁移。
4. 实现 StorageProvider / LocalStorageProvider 边界及安全文件存取。
5. 针对数据完整性、路径越界、文件独立副本和异常清理验证。
6. 完成本阶段验收并更新开发记录后，再进入 Phase 2。

## 阶段总览

| Phase | 内容 | 状态 |
| --- | --- | --- |
| 0 | 项目初始化 | 已完成 |
| 1 | DB + Alembic + Storage | 待开始 |
| 2 | Project / Script / Scene / Shot | 待开始 |
| 3 | Asset Library | 待开始 |
| 4 | Character / CharacterState | 待开始 |
| 5 | Shot Workspace | 待开始 |
| 6 | Prompt Template | 待开始 |
| 7 | AI Prompt Generation | 待开始 |
| 8 | Prompt Versioning | 待开始 |
| 9 | Storyboard Workflow | 待开始 |
| 10 | Video Result | 待开始 |
| 11 | Export / Recycle Bin / UX | 待开始 |
