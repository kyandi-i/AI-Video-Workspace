# 资源占用与依赖审计（Phase 1.5 开发前）

审计日期：2026-09-20。此报告是开始 UI Foundation 前的基线，不代表新增 UI 组件之后的依赖大小。

审计阶段没有删除、迁移、卸载或修改源码。复用了已有 FastAPI，启动 Vite 并用独立 Chromium 窗口打开首页测量；浏览器正常关闭，未运行测试套件或构建。用户随后明确确认“审计完成后立即执行 Phase 1.5”。

## 测量口径

- 下文 MiB = 1,048,576 字节，GiB = 1,073,741,824 字节。目录大小默认文件内容合计，不能把父子目录相加。
- 项目包含隐藏文件、.git、依赖和缓存，共 13,610 个文件。通过 Windows FileStandardInfo 读取文件分配空间，按文件标识去重；不包含 NTFS 目录、MFT 等文件系统公共元数据。
- 不跟随目录联接/符号链接递归，防止重复统计。pytest 目录跳过的 114 个联接主要来自路径安全测试；真实文件已统计。未发现读取错误。
- 共享缓存缺少“由哪个项目写入”的完整历史，不能将全部容量归因于本项目。
- RAM 使用 Working Set 近似常驻内存；不同进程的共享页可能重复统计，不等同于独占物理内存或系统内存增量。

## 磁盘：项目目录

| 位置 | 大小 | C/D 盘 | 用途 | 是否必要 | 是否建议处理 |
| --- | ---: | --- | --- | --- | --- |
| `D:\GitHub_kyandi-i\AI_Web` | **256.06 MiB 内容；276.72 MiB 文件分配空间** | D | 完整工程 | 是 | 正常，无需清理 |
| `D:\GitHub_kyandi-i\AI_Web\frontend\node_modules` | 184.90 MiB | D | 前端运行与开发依赖 | 开发必要 | 保留 |
| `D:\GitHub_kyandi-i\AI_Web\backend\.venv` | 69.64 MiB | D | 后端环境 | 必要 | 保留 |
| `D:\GitHub_kyandi-i\AI_Web\frontend\dist` | 0.482 MiB | D | 生产构建 | 构建运行模式必要 | 可重建，无清理收益 |
| `D:\GitHub_kyandi-i\AI_Web\frontend\node_modules\.vite` | 10.38 MiB，已含于 node_modules | D | Vite 预打包缓存 | 可再生 | 仅故障排查时考虑重建 |
| `D:\GitHub_kyandi-i\AI_Web\backend\__pycache__` | 不存在 | D | Python 字节码 | — | 无需处理 |
| `D:\GitHub_kyandi-i\AI_Web\backend\app` 中的 `__pycache__` | 合计 64.2 KiB | D | 应用字节码 | 可再生 | 无需处理 |
| `D:\GitHub_kyandi-i\AI_Web\backend\tests` 中的 `__pycache__` | 合计 140.2 KiB | D | 测试字节码 | 可再生 | 无需处理 |
| 全项目 `__pycache__`，包含虚拟环境 | 15.21 MiB，已含于总量 | D | Python 字节码 | 可再生 | 不优先处理 |
| `D:\GitHub_kyandi-i\AI_Web\.workspace\e2e\workspace\data\workspace.db` | 24 KiB | D | E2E 独立数据库 | 测试数据 | 可再生 |
| `D:\GitHub_kyandi-i\AI_Web\.workspace\e2e\workspace\storage` | 0 字节文件内容 | D | 测试托管目录 | 目录必要 | 无需处理 |
| `D:\GitHub_kyandi-i\AI_Web\.workspace\e2e\workspace\storage\temp` | 0 字节文件内容 | D | 测试导入暂存 | 目录必要 | 无需处理 |
| `D:\GitHub_kyandi-i\AI_Web\frontend\test-results` | 0.248 MiB | D | 验收截图和结果 | 非运行必需 | 可再生 |
| `D:\GitHub_kyandi-i\AI_Web\backend\.pytest_cache` | 5.62 KiB | D | pytest 索引 | 可再生 | 无需处理 |
| `D:\GitHub_kyandi-i\AI_Web\.ruff_cache` | 234 B | D | Ruff 缓存 | 可再生 | 无需处理 |
| `D:\GitHub_kyandi-i\AI_Web\.git` | 0.171 MiB | D | 版本历史 | 必要 | 保留 |
| 项目根 `logs` / `storage` / `temp` | 不存在；项目 .log 合计 0 | D | 无独立日志或素材目录 | — | 无需处理 |

超过 50 MiB 的目录只有 frontend（185.80 MiB）、其 node_modules（184.90 MiB），以及 backend（70.00 MiB）、其 .venv（69.64 MiB）。这是两组嵌套关系，不是四份占用。

## 磁盘：C 盘与用户目录

| 完整位置 | 大小 | 实际盘符 | 用途 / 是否本项目产生 | 是否必要 | 是否建议处理 |
| --- | ---: | --- | --- | --- | --- |
| `C:\Users\Lenovo\AppData\Local\ms-playwright` | **1,403.05 MiB** | C | 共享测试浏览器；有本项目和 creating-workflow 两个注册记录 | 浏览器测试需要 | 优先规划迁到 D；不能全部归因于本项目 |
| `C:\Users\Lenovo\AppData\Local\ms-playwright\chromium-1243` | 431.92 MiB | C | 本项目 Phase 0 明确下载的完整 Chromium | 有界面测试/本次测量使用 | 可迁移；删除后需显式重新 install，不会仅因打开应用自动下载 |
| `C:\Users\Lenovo\AppData\Local\ms-playwright\chromium_headless_shell-1243` | 270.10 MiB | C | 本项目 Phase 0 下载；默认 headless 测试使用 | 当前测试需要 | 可迁移；删除后测试会提示缺浏览器，需重新 install |
| `C:\Users\Lenovo\AppData\Local\ms-playwright\chromium-1234` | 426.69 MiB | C | 较旧版本，另有项目注册 | 其他项目可能需要 | 先核对另一个项目，不能直接判定可删 |
| `C:\Users\Lenovo\AppData\Local\ms-playwright\chromium_headless_shell-1234` | 270.75 MiB | C | 较旧 headless 版本 | 其他项目可能需要 | 同上 |
| `C:\Users\Lenovo\AppData\Roaming\uv\python` | 61.54 MiB | C | 共享 Python 3.12.11，当前 .venv 指向它；不能证明最初由本项目安装 | 后端运行必要 | 可规划迁 D 并重建虚拟环境引用；不可直接删/移动 |
| `C:\Users\Lenovo\AppData\Local\npm-cache` | 15.17 MiB | C | 旧 npx/prebuild 残留，含其他工具；不是当前 npm cache | 非本项目运行必需 | 可在确认其他工具不用后清理；再次调用相关工具可能下载 |
| `C:\Users\Lenovo\AppData\Local\pnpm` | 8.09 KiB，另有联接未重复统计 | C | pnpm 配置/小索引；本项目使用 npm | 共享工具配置 | 不建议整体清理；不能当作纯缓存 |
| `C:\Users\Lenovo\AppData\Local\Temp\pytest-of-Lenovo` | 4.34 MiB | C | 留存目录内测试名对应本项目 | 测试运行后非必要 | 可迁测试临时目录；无测试运行时可清理，之后重新生成，无网络下载 |
| `C:\Users\Lenovo\AppData\Local\Temp\playwright-transform-cache` | 21.4 KiB | C | 本项目 Playwright 配置和用例转换缓存 | 可再生 | 可迁/清，运行测试重新编译，不下载浏览器 |
| `C:\Users\Lenovo\AppData\Local\Temp\node-compile-cache` | 15.40 MiB | C | Node 共享编译缓存，无法全部归因本项目 | 可再生 | 可迁/清；后续本地重新编译 |
| `C:\Users\Lenovo\AppData\Local\Temp\npm-cache-opencode` | 0 | C | 其他工具命名的空目录 | 非本项目 | 无空间收益 |
| `C:\Users\Lenovo\AppData\Local\Temp\uvmpkduc.bxo` | 0 | C | uv 空临时目录，来源不确定 | 非必需 | 无空间收益 |
| `C:\Users\Lenovo\AI-Video-Workspace` | **24 KiB** | C | 本项目真实 Workspace，当前只有 SQLite；storage/temp 均为空 | **业务数据，不是缓存** | 未来素材增长前规划迁 D；不能清理，不会自动恢复已有数据 |
| `C:\Users\Lenovo\AppData\Roaming\AI-Video-Workspace` | 67 B | **实际 D** | 本项目 Bootstrap Config | 必要 | 保留，容量可忽略 |

Bootstrap Config 的物理完整目录为：

`D:\WpSystem\S-1-5-21-2336341969-3287654707-1809469733-1001\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Roaming\AI-Video-Workspace`

没有发现 `C:\Users\Lenovo\.virtualenvs`、`C:\Users\Lenovo\.pnpm-store`、`C:\Users\Lenovo\AppData\Local\uv\cache` 或 `C:\Users\Lenovo\AppData\Local\pip\Cache`。本项目虚拟环境和 Vite cache 已位于 D 盘。

### 当前已在 D 盘的共享缓存

| 位置 | 大小 | 用途 | 是否必要 | 是否建议处理 |
| --- | ---: | --- | --- | --- |
| `D:\study\DO\DevCache\npm` | 907.89 MiB | 当前 npm cache，多项目共享 | 可再下载 | 已在 D，不建议为了本项目整库清理 |
| `D:\study\DO\DevCache\uv` | 75.32 MiB | 当前 uv cache，包含本项目依赖和索引 | 可再下载 | 保留加速安装 |
| `D:\study\DO\DevCache\pip` | 19.29 MiB | 共享 pip cache，本项目主要用 uv | 可再下载 | 不属于当前项目增量 |
| `D:\study\DO\DevCache\pnpm-store` | 11.56 MiB 内容；去重约 10.12 MiB | pnpm store，本项目未使用 pnpm 安装 | 其他工具可能需要 | 不处理 |

## 运行内存

测量环境：复用已有 FastAPI :8765，启动 Vite HMR :5173（后端没有额外打开 reload 监控器）。独立 headed Chromium 1243 打开当前首页，无业务数据。未运行 pytest/Playwright 测试套件。测试浏览器比个人 Chrome 更易隔离归因，但不等同于普通浏览器已有标签页的增量。

| 进程 | RAM（Working Set） | 是否正常 |
| --- | ---: | --- |
| Vite / Node，PID 44004 | 空闲约 104 MiB；首页约 146 MiB | 正常，首次加载会预处理依赖 |
| esbuild，PID 31700 | 约 19 MiB | 正常，Vite 子进程 |
| FastAPI 实际 Python，PID 44768 | 约 81 MiB | 正常 |
| 后端启动 Python，PID 45100 | 约 24.5 MiB | 正常 |
| 两个 .venv Python 转发进程 | 合计约 9.4 MiB | 是转发进程，不是两个后端服务器 |
| uv 启动器，PID 20148 | 约 22.6 MiB | 正常 |
| 本次独立 Chromium 浏览器进程树 | 首页约 572 MiB | 包含浏览器、GPU、renderer、utility 等；不是单个页面独占 |
| pytest / Playwright 测试工作进程 | 0 | 未运行测试套件；本次测量驱动自身不计入应用 RAM |
| 既有用户 Chrome / Adobe Node / Edge WebView | 存在其他应用进程 | 排除出本项目，不据此判定项目异常 |

- 开发服务空闲合计约 **260 MiB**；首页加载后服务约 **302 MiB**。
- 加上独立 Chromium 后约 **874 MiB（0.85 GiB）**。这是进程工作集相加的近似值，不是排除共享页后的唯一物理内存。
- 全机可用物理内存约 15.69 GiB。开发服务空闲测得整机已用 12.71 GiB / 可用 2.98 GiB；打开首页时约已用 12.97 GiB / 可用 2.71 GiB。后台软件也在变化，不能将整机差值全部归因于本项目。
- 审计开始只有 :8765，一个 FastAPI；审计启动一个 :5173 Vite。未发现残留 :5174/:8766 测试服务器或重复 dev server。未见明显异常项目进程；未做长时间内存泄漏测试。

## 前端依赖

以下为开发前安装目录大小，包含类型、源码、开发版、source map 等，**不是浏览器下载量**。

| 依赖 | 用途 | 大小/影响 | 是否实际使用 | 是否重复 |
| --- | --- | ---: | --- | --- |
| React + React DOM | UI 基础 | 0.17 + 7.69 MiB | 是 | 否 |
| `@radix-ui/react-slot` | shadcn Button asChild | 43.8 KiB | 是 | 否 |
| `@radix-ui/react-compose-refs` | Slot 间接依赖 | 12.6 KiB | 间接 | 否 |
| `class-variance-authority` | Button variants | 21.6 KiB | 是 | 否 |
| `clsx` | 条件 className | 8.4 KiB | 是 | 与 tailwind-merge 互补 |
| `tailwind-merge` | 合并 Tailwind 冲突类 | 1.00 MiB | 是 | 否 |
| `lucide-react` | **唯一图标库** | **27.25 MiB** | 是，具名导入 | 否，安装包大不等于生产包大 |
| Tailwind CSS | 唯一 CSS 框架 | 0.737 MiB | 是 | 否 |
| `@tailwindcss/vite` + Tailwind 原生工具链 | CSS 构建 | @tailwindcss 合计约 3.21 MiB；另有 lightningcss 约 9.07 MiB | 是，构建用 | 不是额外 UI 框架 |
| `@tanstack/react-query` + query-core | API 缓存/状态 | 合计约 4.63 MiB | 是 | 否 |
| `react-router-dom` + react-router | 路由 | 合计约 4.58 MiB | 是 | dom 是包装层，不是重复路由方案 |
| Zod | API 响应校验 | 5.86 MiB | 是 | 否 |
| TypeScript | 类型检查 | 22.53 MiB | 是，开发用 | 否 |
| Vite | 开发与打包 | 2.13 MiB，不含工具链 | 是 | 否 |
| `@vitejs/plugin-react` / Babel / esbuild | React 转换与预打包 | Babel 约 7.90 MiB；esbuild 约 11.15 MiB | 是，构建用 | 职责不同，不宜直接删一个 |
| `@playwright/test` + playwright + playwright-core | 浏览器验收 | npm 部分约 17.72 MiB；浏览器另算 | 测试中使用 | 非产品运行依赖 |
| ESLint / typescript-eslint / hooks / refresh / globals | 代码检查 | ESLint 约 2.87 MiB；hooks 3.91 MiB；@typescript-eslint 4.09 MiB | 是，配置实际引用 | 无重复 Linter |
| Prettier | 格式化 | 9.50 MiB | 开发中手动调用；暂无 npm format 脚本 | 不是未使用的大型运行库 |
| `@types/node/react/react-dom` | 类型定义 | 合计约 2.85 MiB | 编译使用 | 无运行时成本 |
| 动画库 / 图表库 / 第二套 UI Framework | 未安装 | 0 | — | 无 |

lockfile 中有少量 ESLint 链路的多版本工具依赖（如 globals、minimatch、semver、eslint-visitor-keys），属于间接依赖版本约束，没有多套图标库或重型组件框架。未发现可明确判定为“安装了但源码/构建/测试均未使用”的大型直接依赖。

已有生产构建：JS **472.72 KiB，gzip 147.94 KiB**；CSS **20.37 KiB，gzip 5.54 KiB**。未重新构建，仅读取现有产物。

## 图标

| 来源 | 实现方式 | 是否本地 | 是否需要联网 | 建议 |
| --- | --- | --- | --- | --- |
| lucide-react 0.468.0 | 具名导入 React SVG Component | 是，node_modules/生产 JS | 运行时不需要 | 保持现状 |
| 远程 API / CDN 图标 | 未发现 | — | — | 不引入 |
| PNG/JPG 图标资源 | 当前 src 未发现 | — | — | 不需要新增图片图标包 |
| CSS 首页插画 | 本地 CSS 图形，不是第二个图标库 | 是 | 不需要 | 与图标依赖无关 |

源码未发现 `import * as Icons` 或整体图标对象导入。lucide 包声明 ESM 入口和 `sideEffects: false`；现有生产 JS 中识别到 **19 个图标定义**，页面有 34 个 SVG 实例（重复使用图标）。实际浏览器资源请求均为 localhost，没有远程图标 API/CDN。`components.json` 的远程 `$schema` 是编辑器配置，不是网页的图标网络请求。

Vite 的开发预打包缓存可以比生产图标集合大，这不代表生产版本包含整套 Lucide。当前符合“单一 lucide-react + tree shaking + 无远程 API”原则。

## shadcn/ui

- 组件源码直接位于 `frontend/src/components/ui/button.tsx`，目前只加入了 Button，并有 `components.json` 配置。
- 未安装 shadcn 整套运行时或第二个大型 UI 框架；源码复制本身不意味着大量依赖。
- Radix 当前只有 react-slot（直接）和 react-compose-refs（间接），合计约 56.4 KiB，Button 确实使用。
- 没有“只为一个组件安装整个重型 UI 套件”的情况。
- Phase 1.5 增加 Dialog/Select/Tabs 等后，应只引入对应轻量 Primitive，继续保持一个图标库；新增公共组件即使尚无业务页面消费，也应有独立验收入口，不能伪装为已实现业务。

## 总结与未来建议（均未执行）

1. 项目目录 **256.06 MiB 文件内容 / 276.72 MiB 分配空间**。
2. 可以明确关联本次开发的 C 盘浏览器 1243 两包、测试暂存和 Workspace，合计约 **706.40 MiB**；若加上项目正在使用但来源不可专属归因的共享 Python，约 **767.95 MiB**。所有本次检查到的 C 盘相关工具目录共 **1,499.56 MiB（1.46 GiB）**，包括其他项目浏览器和共享缓存，不能全算本项目新增。
3. 整个审计范围前三个不重叠目录：ms-playwright **1,403.05 MiB**、D 盘 npm cache **907.89 MiB**、本项目 node_modules **184.90 MiB**。只看项目内部：node_modules、.venv、dist。
4. 当前开发服务空闲约 **260 MiB**；打开首页且计入独立浏览器约 **874 MiB**。没有重复 dev server 的证据。
5. 未发现明显不必要的大型直接依赖；最大的可规划优化对象是测试浏览器安装位置，不是 UI 图标实现。
6. 图标系统符合单一 Lucide、按需打包、本地离线使用原则。
7. 未来优先将 Playwright 浏览器放到 D 盘（安装和运行统一设置 `PLAYWRIGHT_BROWSERS_PATH`）；其次为实际 Workspace（当前切换不会自动搬迁旧数据）、Python 安装目录（`UV_PYTHON_INSTALL_DIR`，需重建 venv 引用），最后才考虑测试/Node 临时缓存。npm/uv/pip/pnpm 的缓存配置已在 D 盘。

迁移机制参考官方说明：[Playwright 浏览器路径与安装](https://playwright.dev/docs/browsers)、[uv 存储位置](https://docs.astral.sh/uv/reference/storage/)。本次没有执行任何清理、迁移或卸载。
