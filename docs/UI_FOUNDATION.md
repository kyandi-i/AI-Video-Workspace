# Phase 1.5 · UI Foundation

本阶段只建立视觉系统、布局和公共组件；没有实现 Project / Asset CRUD、Prompt、AI 或其他业务模块。Dashboard 的项目、镜头、素材和活动区域是明确的空状态，不能视为已经实现对应功能。服务与 Workspace 元数据来自已有真实 GET API。

## 使用与预览

- 默认 Dark。Topbar 可切换 Light；Settings 使用相同 ThemeProvider。
- 仅将 `avw.ui.theme = dark | light` 保存到 localStorage。阻止存储时退化为当前页面内存偏好；非法值回退 Dark；同源标签页同步主题。
- HTML 首屏脚本在 React 挂载前读取偏好，避免浅色闪屏。没有远程字体、CDN 图标、图片服务或虚构用户。
- 开发模式下访问 `/__ui`，可验证所有公共组件。该路由及其样例模块从生产路由和 JS 中移除，不出现在产品导航中。
- Dashboard / Settings 均可在默认构建地址 `http://127.0.0.1:8765` 查看。

## Design Tokens

唯一颜色源为 `frontend/src/styles/tokens.css`；`frontend/src/index.css` 将其映射为 Tailwind 语义颜色。使用 CSS kebab-case 对应规格中的 camelCase 名称。HTML 中唯一初始 theme-color 值用于 CSS 加载前的浏览器主题色，挂载后从当前 background token 同步。

| Token | Dark | Light |
| --- | --- | --- |
| background | `#111517` | `#F2F5F6` |
| foreground | `#E9EFF2` | `#1B2830` |
| sidebar | `#14191C` | `#F8FAFB` |
| sidebarForeground | `#AEBBC3` | `#576872` |
| panel | `#191F23` | `#FFFFFF` |
| panelForeground | `#E9EFF2` | `#1B2830` |
| card | `#20272C` | `#F7F9FA` |
| cardForeground | `#E9EFF2` | `#1B2830` |
| muted | `#273138` | `#E6ECEF` |
| mutedForeground | `#9EACB5` | `#576872` |
| border | `#303A40` | `#D9E1E5` |
| input | `#53636D` | `#8999A2` |
| control | `#252E34` | `#EDF1F3` |
| accent | `#53D9B0` | `#087B61` |
| accentForeground | `#10271F` | `#FFFFFF` |
| success | `#6CDBB5` | `#126E53` |
| warning | `#E5BA72` | `#8B5B10` |
| danger | `#F58D91` | `#AB3443` |
| ring | `#53D9B0` | `#087B61` |

还有 overlay / shadow 辅助 token。浅色模式使用更深的同色相 Accent，以维持白色按钮文字的对比度。Badge / Selected 状态用 token 的 color-mix 生成轻背景，不新增页面颜色常量。

字级：页面标题 23px、Section / Card 标题 13px、正文 13px、表单 12px、元信息 11–12px、辅助标注 9–10px。系统字体 Segoe UI / Microsoft YaHei，不下载字体。桌面 Sidebar 232px，笔记本最小常规宽度下 220px；Topbar 59px；Main 不设固定最大宽度。窄于 1150px 时右栏换行，窄于 850px 时导航收为图标。完整移动端交互留在后续阶段。

## 公共组件

组件源码直接保存在仓库，采用 shadcn/ui 的源码管理与组合方式，复用 Radix 行为；没有安装整套 UI Framework 或 shadcn 运行时。Sheet 复用 Dialog，不重复引入弹层依赖。

| 位置 | 组件 | 用法与边界 |
| --- | --- | --- |
| `components/common/page-header.tsx` | PageHeader | title / description / metadata / actions |
| `components/common/section-header.tsx` | SectionHeader | Panel 内标题、元信息、说明与操作 |
| `components/common/workspace-panel.tsx` | WorkspacePanel | 标题、可选说明 / 操作 / 元信息、内容；有可访问名称 |
| `components/common/empty-state.tsx` | EmptyState | Lucide 图标、标题、说明、可选 action、compact |
| `components/common/entity-card.tsx` | EntityCard | name / metadata / status / preview；选择按钮与 aria-pressed |
| `components/common/media-card.tsx` | MediaCard | 16:9、1:1、3:4；cover / contain；懒加载、缺图及加载失败占位、类型 Badge |
| `components/common/detail-sheet.tsx` | DetailSheet | 右侧预览、滚动内容、操作；焦点约束、关闭后回到触发控件 |
| `components/ui/button.tsx` | Button | primary / secondary / ghost / destructive，sm / icon，asChild |
| `components/ui/input.tsx` 等 | Input / SearchInput / Textarea / Select / Checkbox / Switch | 统一 34px 单行高度、焦点、禁用与键盘行为 |
| `components/ui/badge.tsx` | Badge | neutral / accent / success / warning / danger |
| `components/ui/tabs.tsx` | Tabs | 紧凑下划线选中态、方向键导航 |
| `components/ui/dialog.tsx` / `sheet.tsx` | Dialog / Sheet | 标题、描述、关闭按钮、Esc 与 modal 焦点管理 |
| `components/ui/sonner.tsx` / `lib/notifications.ts` | Toaster / notify | success / error / info，统一 token 与 Lucide 图标 |
| `components/ui/` | Card / DropdownMenu / Tooltip / Separator / ScrollArea / Skeleton | 中性表面、弱边框、低装饰、稳定加载占位 |

示例：

```tsx
<WorkspacePanel title="Reference Assets" metadata="References" actions={actions}>
  {content}
</WorkspacePanel>
<MediaCard name={asset.name} src={asset.previewUrl} mediaType="IMAGE"
  aspectRatio="3/4" fit="contain" selected={selected} onSelect={select} />
```

后续业务数据必须经对应 features 模块接入。MediaCard 是纯显示组件，不提供上传、持久化或下载 API；传入的媒体地址由未来 Storage 接入方负责。不要将开发验收样例当成产品种子数据。

## 依赖与资源

- 只使用 lucide-react 命名导入，保持 SVG Components / tree shaking；无远程图标 API、CDN、PNG/JPG 图标集。
- 新增直接依赖：Radix dialog、tabs、select、checkbox、switch、dropdown-menu、tooltip、separator、scroll-area，以及 sonner。Slot 沿用原依赖；共享 Radix 包由 npm 去重。
- 所有新增 primitive 都有实际产品或开发验收调用。Select / Checkbox / Switch 和实体媒体 Card 尚未接入业务页面，这是本阶段基础组件的范围；生产 tree shaking 会去除仅在开发验收页引用的 JS。
- 锁文件随版本更新；安装时 npm audit 为 0 vulnerabilities。没有清理、迁移或卸载任何原有依赖 / 缓存。
- Playwright worker 固定为 2，避免本机默认按 CPU 核心启动过多浏览器测试进程。
- 最终生产包大小和资源增量见开发状态；Vite 大于 500 kB 的单 chunk 提示作为后续按业务页面拆包的优化项，不通过提高阈值隐藏。

## 验收边界

Dark / Light 检查前景/背景、Panel、Card、次要文字、Sidebar、Accent 按钮以及 success / warning / danger 的 10 组文字 token 对比度，均至少 4.5:1。此为关键 token 的 WCAG AA 检查，不是完整产品无障碍认证；同时实际检查两种主题页面与组件截图。

键盘与交互覆盖主题、跨标签同步、表单、Select、Tabs、Checkbox、Switch、Dialog、DetailSheet、Toast、媒体选中状态；布局检查 1920 / 1440 / 1280 / 1024 / 390px。Playwright 的独立测试 Workspace 与实际用户 Workspace 分离。迁移与 Storage 回归沿用全部后端测试。

截图见 `docs/screenshots/phase-1.5-*`；正式页面使用本机真实 Workspace，组件页明确标注为开发验收样例。

本阶段结束后停止，等待用户确认 Phase 2。
