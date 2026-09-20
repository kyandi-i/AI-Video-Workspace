# 开发状态

更新日期：2026-09-20

## 当前阶段

**Phase 1.5 · UI Foundation：已完成。** 用户明确确认“审计完成后立即执行 Phase 1.5”；现已完成资源审计、UI 基础与验收，停在本阶段，等待确认 Phase 2。

需求和范围见 [PROJECT_PLAN.md](PROJECT_PLAN.md) 与 [Phase 1.5 原文](docs/PHASE_1_5_SPEC.md)。历史验收：[Phase 0](docs/PHASE_0_STATUS.md)、[Phase 1](docs/PHASE_1_STATUS.md)。

## 本阶段实现

- 默认 Dark；Topbar / Settings 切换 Light，`avw.ui.theme` 是唯一 localStorage UI 偏好。预渲染应用主题、存储受限降级、非法值回退、跨标签同步。
- 统一 background / sidebar / panel / card 层级、弱边框、青绿色 Accent、紧凑排版与滚动条。完整 Token 值和 API 见 [UI Foundation](docs/UI_FOUNDATION.md)。
- 重做 Sidebar / Topbar / 全宽 Main；保留六个导航名称，Settings 位于底部。尚无业务的导航禁用，不展示开发阶段标签。
- Dashboard 删除营销 Hero、开发路线、Phase 卡片和虚构用户；展示真实服务/存储状态、项目/镜头/素材/活动的明确空状态。
- Settings 只提供 UI 主题和只读 Workspace 元数据。DetailSheet 展示真实目录、数据库文件、初始化状态，并支持复制路径及 Toast。没有从 UI 写入或切换 Workspace。
- 新增 WorkspacePanel、PageHeader、SectionHeader、EmptyState、EntityCard、MediaCard、DetailSheet；统一 Button、Card、Input、SearchInput、Textarea、Select、Checkbox、Switch、Badge、Tabs、Dialog、Sheet、DropdownMenu、Tooltip、Separator、ScrollArea、Skeleton、Toast。
- 沿用 shadcn/ui 源码管理方式与 Radix primitives；只用 lucide-react 命名导入。没有远程图标、字体、图片或网络图标 API。
- 开发专用 `/__ui` 验收入口覆盖基础组件；样例明确标注，不是业务数据，不出现在生产路由中。
- 后端源码、API 契约、StorageProvider、Repository、Schema、迁移均未更改，没有新增业务功能。

## 验收结果

| 检查 | 结果 |
| --- | --- |
| ESLint | 通过 |
| TypeScript + Vite build | 通过 |
| Playwright 构建模式 | **12/12 通过，无跳过** |
| Playwright Vite 开发模式 | **14/14 通过，无跳过** |
| pytest 全部后端回归 | **61/61 通过，无跳过** |
| Ruff check / format | 通过，35 个文件格式符合要求 |
| Alembic current | `0001_app_settings (head)` |
| Alembic check | `No new upgrade operations detected` |
| 实际默认 Workspace 服务 | `http://127.0.0.1:8765` 正常，storage_initialized=true |
| 主题与状态 | 默认/保存/非法/受限存储/跨标签同步、服务断线/重试、独立 Workspace 读取错误通过 |
| 交互 | 只读详情、复制反馈、焦点约束/返回、Esc、表单、Select、Tabs、Switch、Checkbox、三类 Toast、媒体选择与三种比例通过 |
| 可读性 | 两种主题各 10 组关键文字 Token 对比度 ≥4.5:1，并人工检查截图 |
| 布局 | 1920 / 1440 / 1280 / 1024 / 390px 无水平溢出；1920px Main 超过 1600px |
| Local-first | 页面资源请求只访问本地；详情查看和复制没有 API 写操作；未增加业务 localStorage |
| Git whitespace | `git diff --check` 通过 |

原 Phase 0 的真实连接、失败恢复、404 返回和视口检查已迁入 workspace 测试并更新为正式工具 UI 的语义；bootstrap 测试现在覆盖主题初始化和跨标签同步。不是继续断言被需求要求删除的营销内容。

测试服务使用独立 `.workspace/e2e` 配置和数据库；pytest 的数据库/存储/迁移测试使用临时目录，保留升降级、autogenerate、UTC / UUID、事务和危险路径回归。浏览器测试最多 2 workers。两种测试启动方式均实际运行并自动退出。

健康 API 的 `phase=1` 仍表示原后端基础设施阶段；UI Foundation 不改写已有 API 阶段字段。

## 截图

正式截图使用实际默认 Workspace，非虚构业务数据：

- [Dark Dashboard](docs/screenshots/phase-1.5-dark.png)
- [Light Dashboard](docs/screenshots/phase-1.5-light.png)
- [DetailSheet](docs/screenshots/phase-1.5-detail.png)
- [Dark 组件验收](docs/screenshots/phase-1.5-components-dark.png)
- [Light 组件验收](docs/screenshots/phase-1.5-components-light.png)

## 资源与依赖

[只读资源审计](docs/RESOURCE_AUDIT_2026-09-20.md) 记录 UI 开发前的基线、C/D 盘归因、RAM、依赖和图标。审计后没有执行缓存清理、目录迁移、原有依赖卸载或浏览器重新下载。

| 项目 | UI 前 | UI 后测量 |
| --- | ---: | ---: |
| frontend/node_modules | 184.90 MiB | 189.30 MiB，增加约 4.40 MiB |
| frontend/dist | 0.482 MiB | 0.632 MiB |
| 生产 JS | 484.07 kB / gzip 151.49 kB | 634.70 kB / gzip 198.46 kB |
| 生产 CSS | 20.86 kB / gzip 5.67 kB | 26.90 kB / gzip 6.31 kB |
| backend/.venv | 69.64 MiB | 69.64 MiB |

上表 bundle 单位 kB 为十进制，与 Vite 输出一致；磁盘 MiB 为二进制。UI 后工程文件内容快照约 260.89 MiB，测量在最终文档和部分验收截图落盘前，最终 Git 对象/截图会带来少量额外变化；未把逻辑大小冒充 NTFS 分配空间。审计中的 C 盘与 RAM 数字是开发前基线，不冒充新界面的重新测量。

新增 9 个 Radix 直接依赖与 Sonner，共安装 49 个依赖包；安装时 npm audit 为 0 vulnerabilities。没有新增图标库、图表库、动画库或重型 UI Framework。未接入业务的组件由开发验收页消费，生产构建移除开发模块及只供它使用的 JS。

## 已知限制

- 本阶段不包含 Project / Asset / Character / Prompt 业务及创建操作。空状态不代表这些模块已实现。
- 完整移动端体验不在当前范围；普通笔记本与桌面优先。
- Vite 单 JS chunk 约 634.70 kB，仍有大于 500 kB 的性能提示。当前 gzip 约 198.46 kB；可在后续业务路由出现时按页面拆包，当前未提高提示阈值或引入额外框架。
- 沿用的 Zod PURE 注释提示，以及 Starlette/httpx 和 AnyIO 弃用提示不阻止构建/测试，本阶段未为这些提示升级后端依赖。
- 对比度测试覆盖核心 token，不是完整无障碍认证。
- Phase 1 的单进程服务、文件补偿与缩略图能力边界继续适用，见历史验收记录。

## 下一步

**等待用户确认后才进入 Phase 2（Project / Script / Scene / Shot）。**
