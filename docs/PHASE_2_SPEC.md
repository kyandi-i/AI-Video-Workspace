# Phase 2 · Core Workflow

依据：用户在 2026-09-21 提交的 Phase 2 详细要求（42 节），以及冻结的 MVP v0.1 规格。本文件记录本轮范围、具体取舍与验收入口；不替代总规格。

## 范围

实现 Project → Script → ScriptNode(type=SCENE) → Scene → Shot 的实际数据库与 UI 闭环。每张表使用已有 BaseModel 的 UUID、UTC Timestamp、SoftDelete mixin。保留 NodeType CHAPTER / SEQUENCE / SCENE / OTHER 与 nullable parent_id；本阶段仅创建根级 SCENE 节点。

Project status：DRAFT / ACTIVE / PAUSED / COMPLETED / ARCHIVED。

Shot status：DRAFT / ASSET_PREPARING / STORYBOARD_PROMPT_READY / STORYBOARD_READY / VIDEO_PROMPT_READY / VIDEO_GENERATING / REVIEW / DONE。状态仅用于人工标记；不会触发未实现的制作功能。

## 数据一致性取舍

- Scene 必须有唯一、非空的 script_node_id。Service 验证节点类型与所属 Script / Project；业务 API 不允许重新绑定父级。
- Scene.name / description / fixed_constraints / negative_constraints 是业务内容来源。SCENE 节点 title / description 留空，避免维护影子字段；其他节点类型预留这些字段。
- Scene 表不重复存 order_index；SceneRead 从 ScriptNode 投影 script_id / order_index，并计算有效 Shot 数量。排序为剧本创建顺序、节点 order_index、created_at，最后 UUID 打破相同时间的平局。
- 创建 Scene 在一个 Service savepoint 中验证父级、分配顺序、创建节点和场景。外层沿用 WorkspaceService.session 的提交 / 回滚边界；失败即使被调用方捕获，也不会留下节点。Repository 只 flush。
- 沿用 Workspace 资源锁：单进程内请求事务持锁到提交，避免并发分配重复顺序；数据库外键、CHECK、UNIQUE 提供第二层约束。没有加入多进程服务支持。
- Shot 编号 trim 后在 Project 内区分大小写唯一，软删除后仍占用编号。不同 Project 可各有 S01；冲突返回 SHOT_CODE_CONFLICT / 409。
- Shot 时长必须有限且 >= 0；order_index >= 0，输入不能直接控制顺序。创建追加，删除重排，上移 / 下移相邻交换后重排，边界移动幂等。

## 删除与恢复

- Project → Script → Scene / ScriptNode → Shot 逐层软删除，全部保留原行与外键。Scene 删除明确同步软删除其 SCENE 节点和当前有效 Shot。
- 一次级联使用相同 UTC deleted_at，恢复父级时仅恢复相同删除批次的后代；此前独立删除的数据保持已删除状态。删除标记晚于数据库已有删除时间，避免低精度时钟或时钟回拨导致批次碰撞。
- 恢复子级要求父级有效。单独恢复场景 / 镜头追加到有效兄弟末尾并连续编号；恢复整棵子树保持确定性排序。重复 restore 不改变当前顺序。
- GET 默认不可见软删除数据；列表与详情有 include_deleted，四类实体有 restore API。没有物理删除业务 API，也没有回收站页面。

## 界面和请求边界

路由：`/projects`、`/projects/:projectId`、`/projects/:projectId/script`、`/projects/:projectId/scenes`、`/projects/:projectId/shots`、`/shots/:shotId`。

Project 卡片展示名称、摘要、状态、更新时间；Overview 是真实 Scripts / Scenes / Shots count。Script 页面组织剧本 → 可折叠场景 → 镜头表格。Scene 编辑固定 / 负面约束。Shots 提供组合搜索、场景和状态筛选，排序由服务端执行。基础 Shot Detail 可编辑，不包含 Prompt / Storyboard。

四个 Feature 各自有 api.ts / hooks.ts / types.ts；统一 Query Key Factory；Dialog 即时字段验证、保存锁定、可读错误、成功 Toast、删除确认。级联删除同时清理受影响的已缓存详情，避免回退导航复用已删除镜头。

默认 Dark，支持 Light，延续现有 Token 与组件；没有加入新的包、外部图片 / 字体或业务 localStorage。业务路由按页面懒加载。前端列表筛选当前使用已加载的本项目数据；后端也支持同等搜索 / 筛选参数，当前未做分页和虚拟列表。

## 验收映射

| 要求 | 实现 / 验证 |
| --- | --- |
| 五类模型、五个 Repository、四个 Service | backend/app 对应目录中的 workflow.py |
| CRUD / restore / include_deleted / move / stats / 统一错误 | backend/app/api/routes/workflow.py 与 schemas/workflow.py |
| 创建事务、1:1、跨项目、软删除、恢复、唯一、并发排序 | backend/tests/test_workflow.py |
| 正式升降级、已有设置保存、带数据回退、autogenerate、UUID / UTC、PostgreSQL DDL | backend/tests/test_database.py |
| 全流程 CRUD、两主题、搜索 / 筛选、刷新、错误、pending、删除确认 | frontend/tests/workflow.spec.ts |
| 原 UI Foundation、设置、断线、主题、布局、对比度回归 | frontend/tests/workspace.spec.ts、bootstrap.spec.ts |

测试只使用临时目录及仓库 `.workspace/e2e`，不会写入 `D:\AI-Video-Workspace`。最终结果见 [开发状态](../DEVELOPMENT_STATUS.md)。

## 明确不包含

Asset Upload / Library 功能、Character / CharacterState、Prompt Template / Generation、AI Provider UI、Storyboard、VideoResult、Project Export、Recycle Bin UI、Chapter / Sequence UI、复杂 DnD。没有更换技术栈、存储策略或分层边界。
