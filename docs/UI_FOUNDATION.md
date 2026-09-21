# UI Foundation · Phase 2.5 修订

视觉基础建立于 Phase 1.5；Phase 2 接入项目层级工作流，Phase 2.5 统一公共组件交互。Project / Script / Scene / Shot 已接入真实数据库；Asset / Prompt / AI 等仍未实现。历史记录见 PHASE_1_5_STATUS.md 和 PHASE_2_STATUS.md。

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
| `components/ui/input.tsx` 等 | Input / SearchInput / Textarea / Select / Checkbox / Switch | Input / Select 36px；Textarea 多行；明确焦点、禁用与键盘行为 |
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
- 公共 primitive 均有产品或开发验收调用；Select 已用于状态、剧本、场景与筛选。生产 tree shaking 去除只在开发验收页引用的 JS。
- 锁文件随版本更新；安装时 npm audit 为 0 vulnerabilities。没有清理、迁移或卸载任何原有依赖 / 缓存。
- Playwright worker 固定为 2，避免本机默认按 CPU 核心启动过多浏览器测试进程。
- 最终生产包大小和资源增量见开发状态；Vite 大于 500 kB 的单 chunk 提示作为后续按业务页面拆包的优化项，不通过提高阈值隐藏。

## 验收边界

Dark / Light 检查前景/背景、Panel、Card、次要文字、Sidebar、Accent 按钮以及 success / warning / danger 的 10 组文字 token 对比度，均至少 4.5:1。此为关键 token 的 WCAG AA 检查，不是完整产品无障碍认证；同时实际检查两种主题页面与组件截图。

键盘与交互覆盖主题、跨标签同步、表单、Select、Tabs、Checkbox、Switch、Dialog、DetailSheet、Toast、媒体选中状态；布局检查 1920 / 1440 / 1280 / 1024 / 390px。Playwright 的独立测试 Workspace 与实际用户 Workspace 分离。迁移与 Storage 回归沿用全部后端测试。

截图见 `docs/screenshots/phase-1.5-*`；正式页面使用本机真实 Workspace，组件页明确标注为开发验收样例。

Phase 2.5 已完成并暂停，等待用户确认；不自动进入 Phase 3。

## Phase 2.5 控件与枚举规范

| Token / 部位 | 规则 |
| --- | --- |
| control-height | 36px：Input、Select Trigger / Item、默认 Button |
| control-height-compact | 32px：表格小按钮与图标按钮 |
| control-radius / font-size / line-height | 6px / 12px / 20px，两主题相同 |
| control-padding-x | 12px；Select Item 为右侧勾选标记额外保留 28px |
| Textarea | 最小 88px，多行 line-height 20px，padding 8px 12px |
| Select | Value / ItemText 外有独立布局容器；Indicator 独立 class，不使用子元素位置猜测。Viewport 独立滚动，菜单受可用视口限制 |
| Dialog 表单 | 固定 Header / Footer，form-body 内滚动；提交时 ref 门闩阻止重复请求，同时禁用控件与关闭操作 |
| Sheet | 沿用 Dialog 标题与操作样式，独立滚动正文；移除后置 ui-dialog 样式对 Sheet 高度的覆盖 |
| 状态 | lib/status-display.ts 唯一配置 label / tone，lib/enum-display.ts 的 enumOptions 生成原始 value + 显示 label；StatusBadge 统一呈现 |

颜色语义：Draft / Archived 为 Neutral，进行中 / 就绪为 Accent，Paused / Review 为 Warning，Completed / Done 为 Success。Destructive 删除使用 Danger；不按每个状态分配任意颜色。未来新增枚举必须提供完整的显示映射并复用 enumOptions，不在页面中拆下划线生成标签。

现有业务表单使用 EntityForm / DeleteEntity，取消始终在左、保存或确认删除在右。表格保持 52px 行高，小按钮与图标按钮同高；长标题 / 场景名单行截断并保留完整 title。操作区常驻，不在 hover 时改变布局。

浏览器几何验收同时检查选项高度、文字垂直中心、文字与勾选图标间距、菜单边界、控件字体 / 圆角 / 高度、Dialog 固定区域、长标题行高。截图见 `docs/screenshots/phase-2.5-*`，使用隔离 E2E Workspace 的测试记录。
