# Phase 1.5：UI Foundation

前置条件：

* Phase 0 已完成
* Phase 1 数据库与 Storage 基础完成后执行
* 不改变当前业务架构
* 不提前实现后续业务功能

本阶段目标不是“把首页做漂亮”，而是建立后续所有业务页面统一使用的视觉系统和布局基础。

---

# 1. 总体视觉方向

AI Video Workspace 应从当前偏：

```text
浅色
大留白
营销式 Hero
低信息密度
```

调整为：

```text
专业生产工具
深色工作台
高信息密度
紧凑面板
弱边框
明显层级
青绿色 Accent
```

参考方向：

```text
Premium Dark Dashboard
Creative Production Tool
Professional Media Workspace
```

不要直接复制金融 Dashboard 内容或布局。

只提取视觉语言。

---

# 2. Theme

必须支持：

```text
Dark
Light
```

默认：

```text
Dark
```

用户选择应持久化。

可以使用：

```text
localStorage
```

仅存 UI Theme Preference。

这不属于业务数据。

---

# 3. Dark Theme 视觉原则

页面背景采用接近黑色的深灰，而不是纯黑。

层级建议：

```text
App Background
↓
Sidebar / Topbar
↓
Panel
↓
Card
↓
Interactive Element
```

各层之间主要通过：

```text
轻微明度变化
+
弱边框
+
少量阴影
```

区分。

禁止大量高亮边框和炫光。

---

# 4. Accent Color

主要 Accent 使用：

```text
青绿色 / Cyan-Green
```

用途仅限：

```text
Primary Button

Active Navigation

Selected State

Focus Ring

Progress

Success / Online State

重要交互反馈
```

不要：

```text
整片区域全铺青绿色

大量渐变

所有图标都高亮

大量 Neon Glow
```

视觉目标是：

> 黑色高级感为主，青绿色只是“操作高亮”。

---

# 5. Light Theme

Light Theme 不需要单独设计另一套产品。

应与 Dark Theme 共用 Design Token。

Light Mode：

```text
浅灰白背景

白色 Panel

中性边框

深色文字

相同青绿色 Accent
```

所有组件必须在两种模式下保持可读。

---

# 6. Design Tokens

统一维护 Theme Token。

至少包含：

```text
background

foreground

sidebar

sidebarForeground

panel

panelForeground

card

cardForeground

muted

mutedForeground

border

input

accent

accentForeground

success

warning

danger

ring
```

禁止每个页面自行硬编码：

```text
#0f0f0f

#22f2b2

...
```

颜色必须尽可能来自 Design Token。

---

# 7. Typography

不要使用营销型大字号。

工作台页面优先：

```text
Page Title

Section Title

Card Title

Body

Metadata

Caption
```

标题层级清晰即可。

不需要大量：

```text
48px
56px
```

Hero 字体。

产品是工具，不是 Landing Page。

---

# 8. Layout 基础

整体采用：

```text
Sidebar
+
Topbar
+
Main Workspace
```

Desktop 为主。

推荐：

```text
Sidebar:
约 220–260px

Topbar:
紧凑高度

Main:
自适应宽度
```

不要让主内容固定成很窄的居中网页。

AI Video Workspace 后续会出现大量：

```text
资产缩略图

Prompt 文本

视频预览

分镜

侧边详情

表格
```

必须充分利用横向空间。

---

# 9. Sidebar

重做 Sidebar。

视觉参考：

```text
深色独立区域

Logo 简洁

主导航清晰

Active Item 有 Accent 状态

Inactive Item 低对比

图标 + 文字

底部 Settings
```

第一版导航保持：

```text
Dashboard

Projects

Asset Library

Characters

Prompt Templates

Settings
```

不要在 Sidebar 中展示：

```text
“待开发”

Phase 编号

开发状态
```

这些属于开发信息，不属于正式产品界面。

---

# 10. Topbar

Topbar 保持克制。

可以包括：

```text
Breadcrumb

当前 Project / Page

Theme Toggle

Local Status
```

未来预留：

```text
Search

Quick Add

User / Workspace
```

但 MVP 不需要假用户头像和虚构 Username。

---

# 11. Dashboard 调整方向

移除当前大型营销式 Hero。

例如以下内容不应成为首页主体：

```text
每个好故事从一个清晰的工作空间开始
```

Dashboard 应更偏生产状态。

后续正式业务数据出现后，建议结构：

```text
Recent Projects

Production Progress

Recently Modified Shots

Recent Assets
```

Phase 1.5 暂时没有业务数据时，可以使用简洁 Empty State。

不要为了填页面而制造大量假数据。

---

# 12. Panel Component

建立统一：

```text
WorkspacePanel
```

用于未来：

```text
Storyboard

Prompt

Reference Assets

Video Results

Metadata

Notes
```

Panel 应具有：

```text
Title

Optional Description

Optional Actions

Content
```

视觉：

```text
深色 Surface

弱 Border

适中 Radius

低装饰
```

不要每个 Panel 都像独立营销卡片。

---

# 13. Section Header

建立统一 Section Header：

```text
Title

Metadata

Actions
```

例如未来：

```text
Reference Assets           + Add Asset
```

或者：

```text
Video Results              3 versions
```

---

# 14. Button 系统

统一至少：

```text
Primary

Secondary

Ghost

Destructive

Icon
```

Primary：

```text
Cyan-Green Accent
```

Secondary：

深色模式下保持中性。

禁止同一页面同时出现很多不同高饱和颜色的按钮。

---

# 15. Input 系统

统一：

```text
Input

Textarea

Select

Checkbox

Switch

Search Input
```

要求：

```text
Dark Mode 清晰

Focus 明确

Border 克制

高度统一
```

后续大量 Prompt 表单会依赖这些组件。

---

# 16. Badge

建立统一状态 Badge。

例如未来：

```text
DRAFT

REVIEW

DONE

VIDEO READY
```

Badge 不应全部使用 Accent。

建议：

```text
Neutral

Accent

Success

Warning

Danger
```

---

# 17. Tabs

后续 Shot Workspace 和 Asset Detail 会大量使用 Tabs。

统一视觉：

```text
简洁

紧凑

Active 明显

无大面积背景
```

---

# 18. Cards

区分：

```text
Panel
```

和：

```text
Card
```

Card 主要用于实体：

```text
Project

Asset

Character

Video Version
```

卡片应该方便未来放：

```text
Thumbnail

Name

Type

Status

Metadata
```

不要使用当前首页那种大量大空白功能介绍卡。

---

# 19. Asset Card 基础

虽然 Phase 1.5 不做 Asset Library 功能，但提前设计通用媒体 Card：

```text
Thumbnail Area

Type Badge

Asset Name

Metadata

Selected State
```

必须兼容：

```text
16:9

1:1

竖版人物图
```

图片应使用：

```text
object-fit: cover / contain
```

根据未来业务组件决定。

---

# 20. Scrollbar

Dark Mode 下统一 Scrollbar 风格。

保持弱存在感。

不要出现浏览器默认高对比白色滚动条破坏视觉。

---

# 21. Empty State

建立通用 Empty State。

例如：

```text
No projects yet

Create your first project
```

包括：

```text
Icon

Title

Description

Action
```

不要使用营销语言。

保持直接、工具化。

---

# 22. Loading / Skeleton

建立 Skeleton 基础。

未来 Asset Grid、Shot Workspace 加载时使用。

避免页面加载时：

```text
白屏

布局跳动
```

---

# 23. Toast

统一：

```text
Success

Error

Info
```

用于：

```text
保存成功

复制成功

上传完成

错误
```

建议直接使用 shadcn/ui 兼容方案。

---

# 24. Dialog / Sheet

未来编辑内容优先考虑：

```text
Dialog

Sheet
```

例如：

```text
创建 Project

编辑 Asset

选择 Reference Asset
```

Phase 1.5 统一基础样式即可。

---

# 25. Detail Panel / Sheet

资产库以后非常依赖侧边 Detail Panel。

提前建立：

```text
DetailSheet
```

视觉方向：

```text
右侧滑出

大图预览

Metadata

Actions
```

此 Phase 不需要业务数据。

---

# 26. Workspace 页面宽度

禁止所有页面固定：

```text
max-width: 1200px
```

然后居中。

生产工作台需要：

```text
width: 100%

合理 page padding
```

尤其是：

```text
Shot Workspace

Asset Library
```

未来需要尽可能使用屏幕空间。

---

# 27. Responsive

MVP 仍以 Desktop 为第一目标。

需要支持合理缩放到普通笔记本宽度。

暂时不要求完整 Mobile UX。

不要为了手机端牺牲桌面生产效率。

---

# 28. Dashboard 当前页面整改

本 Phase 可以直接重做当前 Dashboard 外观。

但只做视觉和布局。

删除：

```text
大 Hero Banner

营销式文案

Phase 卡片展示

“待开发”导航文字

开发阶段作为产品内容的展示
```

可以暂时显示：

```text
Workspace Overview

Local Workspace Status

Recent Projects Empty State

Recent Activity Empty State

Storage Status
```

不要虚构业务数据。

---

# 29. Local 状态

可以保留类似：

```text
Local
```

或绿色状态点。

用于表达：

```text
本地服务正常
```

视觉可结合 Cyan-Green Accent。

不要把：

```text
FastAPI v0.1.0
```

之类开发版本信息放在主 Dashboard 卡片中。

可以放 About / Settings。

---

# 30. Dark / Light Toggle

Topbar 提供：

```text
Theme Toggle
```

支持：

```text
Dark

Light
```

如果实现方便，也可增加：

```text
System
```

但用户需求至少必须支持 Dark / Light。

默认 Dark。

---

# 31. shadcn/ui

尽量复用：

```text
Button

Card

Dialog

Sheet

Tabs

Badge

Input

Textarea

Select

DropdownMenu

Tooltip

Separator

ScrollArea

Skeleton
```

不要重新自己造一整套基础组件。

但是可以在其上封装：

```text
WorkspacePanel

PageHeader

EntityCard

MediaCard

EmptyState
```

---

# 32. 禁止事项

本阶段禁止：

```text
重写业务架构

新增 Project CRUD

新增 Asset CRUD

新增 Prompt 功能

新增 AI

新增虚构业务数据

做复杂动画

做大面积 Neon

复制参考图 Logo / 品牌

复制参考图金融内容

引入重型 UI Framework
```

---

# 33. 动画

只允许轻微：

```text
hover

focus

panel transition

sheet transition
```

持续时间短。

工具软件不需要大量页面入场动画。

---

# 34. 目标关键词

整个 UI 应符合：

```text
Premium

Dark

Professional

Compact

Focused

Creative

Production

Modern
```

避免：

```text
Marketing

Cute

Overly Soft

Huge White Space

Colorful Dashboard

Gaming Neon
```

---

# 35. Phase 1.5 验收标准

完成后：

```text
1. 默认 Dark Mode

2. 可切换 Light Mode

3. Theme Preference 可保存

4. Sidebar 已转换为专业深色工作台样式

5. Topbar 风格统一

6. 全局背景 / Panel / Card 层级建立

7. Cyan-Green Accent 已统一

8. Button / Input / Badge / Tabs 风格统一

9. Dashboard 不再采用营销式 Hero

10. Phase / 待开发内容不再作为产品 UI 主体

11. 建立 WorkspacePanel

12. 建立 PageHeader

13. 建立 EmptyState

14. 建立基础 MediaCard / EntityCard

15. Dark / Light 均通过可读性检查

16. 不破坏 Phase 0 / Phase 1 功能

17. 前端 lint / build / tests 全通过
```

---

# 36. 完成后不要继续

Phase 1.5 完成后暂停。

提供：

```text
页面截图

主要 Design Token

新增公共组件

Dark Mode 截图

Light Mode 截图

测试结果
```

等待确认后再进入 Phase 2。
