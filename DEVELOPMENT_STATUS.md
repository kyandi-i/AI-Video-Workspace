# 开发状态

更新日期：2026-09-21

## 当前阶段

**Phase 2.5 · UX Fix：已完成并暂停，等待用户确认。Phase 3 尚未开始。**

本次只修现有 Project / Script / Scene / Shot 交互和公共组件，没有新增业务能力，没有修改后端、业务模型、API 契约、迁移或依赖。依据：[计划索引](PROJECT_PLAN.md)、[UI 规范](docs/UI_FOUNDATION.md)、[MVP v0.1 规格](<AI Video Workspace · MVP v0.1 开发规格.md>)。

历史验收：[Phase 0](docs/PHASE_0_STATUS.md)、[Phase 1](docs/PHASE_1_STATUS.md)、[Phase 1.5](docs/PHASE_1_5_STATUS.md)、[Phase 2](docs/PHASE_2_STATUS.md)。Phase 2 的业务规则、软删除范围和存储边界保持不变。

## 修复说明

- **Select 根因修复**：原 `.select-item > span:last-child` 将最后一个 span 当作勾选标记；未选中时 Indicator 不渲染，实际被绝对定位的是 ItemText，造成文字错位、行高塌陷与重叠。现在 Value / ItemText 使用显式布局容器，Indicator 独立定位，不再依赖子元素顺序。Radix 会忽略 Value / ItemText 自身的 className / style，因此样式落在外层容器上。
- Select Trigger / Item 同为 36px，垂直居中；左右基准 padding 12px，选项右侧额外预留 28px。长文本截断且保留 title，不覆盖勾选图标；hover / focus / selected 各有清晰状态。Content 限制在可用视口内，Viewport 独立滚动。现有项目状态、镜头状态、剧本选择、场景选择和列表筛选全部复用此实现。
- `lib/status-display.ts` 是 Project / Shot 状态 label 与 tone 的唯一配置；`lib/enum-display.ts` 的 `enumOptions` 保留原始 value，生成友好 label。表单、筛选、Dashboard、项目卡片、列表和详情统一使用配置与 StatusBadge。后端仍接收原始枚举，未来枚举可复用同一机制，本轮没有实现未来业务类型。
- Input / Select / 默认 Button 统一为 36px，紧凑操作按钮为 32px；统一 12px 字号、20px 行高、6px 圆角、focus ring 与 disabled。Textarea 使用最小 88px 的多行规格，Dark / Light 共用尺寸 token。
- EntityForm 固定 Header / Footer，正文独立滚动；取消在左、保存在右。保存中禁用字段、关闭及操作按钮，并显示“保存中…”。ref 提交门闩防止 React pending 更新前的重复请求；删除使用相同保护。移除影响 Sheet 高度的后置 Dialog 样式覆盖。
- Project / Script / Scene / Shot 统一 DeleteEntity 确认模式，显示对象名称和影响范围。Scene 明确说明子 Shot 同时软删除并显示数量；删除按钮使用 Danger 样式。没有改变删除语义。
- 镜头表格保持 52px 行高；长标题、编号与场景名单行截断，操作区始终预留空间。状态统一使用 StatusBadge，颜色按 Neutral / Accent / Warning / Success 语义划分。
- 首次请求使用 Skeleton，空列表提供下一步操作，错误显示可读 message 和重试。后台刷新失败保留已成功加载的内容；404 隐藏失效实体。网络及非 JSON 错误使用可读兜底文案。
- Shots 搜索、场景与状态筛选保持统一控件高度；无匹配结果显示清除筛选入口。筛选写入 URL，打开 S13 后返回能保留上下文；从 Script / Scenes 打开镜头后返回原入口。
- 上移 / 下移继续由后端决定最终顺序；前端取消过期读取并一次性应用服务端返回列表，避免旧请求覆盖新顺序。边界按钮禁用，没有引入前端排序规则或复杂拖拽。

## 受影响的公共组件

`Select / SelectValue / SelectTrigger / SelectContent / SelectItem`、Input / Textarea / Button 的共享样式、Dialog / Sheet 的布局样式、`EntityForm / Choice / DeleteEntity`、`QueryState / ErrorState / QueryErrors`，以及新增 `StatusBadge` 与枚举显示工具。所有业务表单继续使用既有组件和 TanStack Query。

## 验收结果

| 检查 | 结果 |
| --- | --- |
| 前端 ESLint | 通过，无错误或警告 |
| TypeScript + Vite build | 通过 |
| 浏览器测试：构建模式 | **22/22 通过，无跳过** |
| 浏览器测试：Vite 开发模式 | **24/24 通过，无跳过** |
| 后端 pytest | **81/81 通过，无跳过** |
| Ruff check / format | 通过，42 个文件符合格式 |
| 迁移回归 | pytest 隔离数据库 upgrade → downgrade → upgrade、autogenerate 与外键检查通过；head 仍为 `0002_core_workflow` |
| Git whitespace | `git diff --check` 通过 |

新增 5 个浏览器用例，覆盖深浅色下选项的几何布局、hover / focus / selected、键盘选择、全部状态友好文案与原始 API value、控件尺寸、固定弹窗区域、长文本、删除影响说明、空结果、导航返回、排序与提交防重。额外模拟后台请求失败，验证旧内容保留和可读错误重试。

既有完整 CRUD、刷新持久化、级联删除后浏览器返回、主题持久化、Workspace 信息与 Sheet、连接重试和公共组件交互全部通过。检查全部现有业务页面，两主题下在 1280px 笔记本宽度、1366 / 1024 × 720 窗口检查弹窗与菜单；既有响应式测试继续覆盖 1920 / 1280 / 1024 / 390px。

测试继续使用既有 Playwright，不增加测试框架。pytest 使用临时 Workspace；浏览器使用 `.workspace/e2e` 隔离配置和数据库，测试服务自动退出。**没有写入用户真实 `D:\AI-Video-Workspace`，没有更改用户 bootstrap 选择。**

## 修复后截图

以下为真实浏览器、隔离 E2E 数据库中的测试记录；长标题用于检查截断，不是产品种子数据。截图已人工检查。

| 页面 | Dark | Light |
| --- | --- | --- |
| Shot 编辑状态 Select | [截图](docs/screenshots/phase-2.5-shot-select-dark.png) | [截图](docs/screenshots/phase-2.5-shot-select-light.png) |
| Project 编辑状态 Select | [截图](docs/screenshots/phase-2.5-project-select-dark.png) | [截图](docs/screenshots/phase-2.5-project-select-light.png) |
| Shots 列表与筛选 | [截图](docs/screenshots/phase-2.5-shots-dark.png) | [截图](docs/screenshots/phase-2.5-shots-light.png) |
| Scene 删除范围确认 | [截图](docs/screenshots/phase-2.5-delete-dark.png) | [截图](docs/screenshots/phase-2.5-delete-light.png) |

## 现有边界

- 不含 Asset Library / Character / Prompt / Storyboard / VideoResult 等后续业务；状态只作人工标记。
- 列表仍读取项目全部记录，没有增加分页、虚拟列表或移动端业务布局。
- 主 JS chunk 645.64 kB / gzip 202.39 kB，Vite 超过 500 kB 提示仍存在，没有提高阈值。既有 Zod PURE 注释、Python 依赖弃用提示未阻止构建与测试，本次没有升级依赖。
- **停在 Phase 2.5，等待用户确认，不自动进入 Phase 3。**
