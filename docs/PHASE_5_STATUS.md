# Phase 5 — Shot Workspace 验收

日期：2026-09-23。基线 `627ab09`，包含 `6456839`，开始时 working tree clean。范围仅 Dedicated Shot Workspace；不进入 Phase 6。

## 完成范围与页面

正式路由 `/shots/:shotId/workspace` 沿用现有独立 Shot 路由风格。从 Shot 列表每行 Workspace 或旧详情 Open Workspace 进入，保留旧详情、Edit / Delete、搜索、场景 / 状态筛选、Move Up / Down。

- Header：shot_code、title、duration_seconds、友好 StatusBadge、当前项目镜头位置。
- Scene Context：name / description / fixed_constraints / negative_constraints，只读，不复制进 Shot；Open Scene 跳转现有项目场景页面。
- Characters：角色身份、描述 / notes、当前视觉状态、角色和状态参考缩略图。封面优先 State 第一张 IMAGE，其次 Character 第一张 IMAGE，缺失时用本地 Users 图标。两类参考分别最多三张，更多通过角色详情查看。
- Shot Requirements：title、description、duration_seconds、status 与四个自然语言多行要求。主表单一次 PATCH，不逐字段 autosave。
- Reference Assets：公共 AssetPicker、ImportAssets、AssetDetailSheet。默认最多六张 thumbnail，View All 展开；绑定、导入后自动绑定、解绑。解除关系不删除实体或托管文件。
- Production Status：直接消费既有 Shot.status 与 Phase 2.5 友好标签 / Badge / 36px Select。Scene / Characters / References / Main Action 摘要从已保存数据计算，没有 Workflow 或 Readiness 表。

宽屏三栏，1024 / 1280 为上下文 + 要求两栏、参考区下置；更窄窗口单栏。桌面保存导航条 sticky，所有列 min-width 受限，多行文本自动换行。公共 Loading / ErrorState / 重试 / Empty 状态保持。

没有 Prompt / Storyboard / VideoResult / GenerationJob / Timeline / AI 调用；没有新增素材 role 分类、账号、云服务或 Workspace 架构。

## 数据模型与兼容

迁移 `0005_shot_workspace`，父 revision `0004_characters`。只给 `shots` 增加：

| 字段 | 类型 | 用途 |
| --- | --- | --- |
| main_action | TEXT nullable | 镜头具体动作 |
| key_constraints | TEXT nullable | 镜头级硬要求 |
| negative_constraints | TEXT nullable | 镜头级禁止内容 |
| free_notes | TEXT nullable | 其他生产补充 |

ShotCreate / ShotUpdate / ShotRead 同步支持。PATCH 省略保留原值；新 nullable 字段允许 null，UI 清空保存空字符串。旧必填字段仍不接受 null；duration 沿用有限、非负数校验。

`creative_requirement` 不删除、不改写、不自动复制。Workspace 非空时显示可展开 Legacy Creative Requirement；旧详情 / 编辑器继续维护它。真实迁移前四条 Shot 的该字段均为空；隔离测试明确验证非空旧文本保留。description 仍是人类可读简述，与 main_action 分开。

Scene、Character、State 和 Asset 的内容只在读取时聚合。没有增加重复上下文列。UUID / UTC / soft delete / SQLite / Managed Storage / Route → Service → Repository 边界保持。

## 保存与导航

- Previous / Next 使用 ShotRepository.by_project 现有服务端顺序：Script 创建顺序 → ScriptNode.order_index → Shot.order_index，沿用原 tie-breaker。跨场景连续导航，不按 shot_code 排序；首尾分别 disabled。
- 主表单显示 Saved / Unsaved changes / Saving… / Save failed。保存期间禁用字段与提交，ref 防重复提交；失败保留草稿。
- React Router useBlocker 覆盖前后镜头、侧栏、链接和浏览器应用内 Back。确认框提供 Stay / Discard and Leave。beforeunload 为浏览器关闭 / 刷新注册原生保护，最终提示由浏览器控制。
- 角色与素材关联即时保存，与主表单 Save 分开，关系刷新不清空草稿。Workspace 离开后释放聚合缓存，再次进入从持久化上下文初始化；旧详情编辑不会被旧表单缓存覆盖。

## Character / Asset 集成

`PUT /shots/{id}/character-states` 在同一 atomic savepoint 内校验目标项目，软删除此角色原 Link，再绑定 / 恢复新 Link；异常回滚原绑定。原 DB active 部分唯一索引继续保证每个 Shot 每个 Character 仅一个 active State。重复替换幂等，其他角色不受影响。旧 POST 的冲突行为保持兼容。

Workspace 使用同一角色选择 / 状态选择体系；Change State 预选当前角色，Replace State 安全替换，Remove 仅解绑。点击角色名打开现有 Character Detail，不重新实现角色 CRUD。

素材复用 Phase 3/4 的 AssetPicker、托管上传和详情。thumbnail URL 用于列表，只有用户打开 Asset Detail 才查看详情媒体。未增加封面字段或 reference_role。

## API

以下均带 `/api`：

| 方法 / 路径 | 变化 |
| --- | --- |
| GET /shots/{id}/workspace | 新增：Shot、Scene、character_states（含 Character / State assets）、Shot assets、previous_shot / next_shot、position / total |
| PUT /shots/{id}/character-states | 新增：body {character_state_id}，绑定或替换目标角色状态 |
| POST /scenes/{id}/shots | 支持四个新字段 |
| PATCH /shots/{id} | 支持一次提交结构化要求、标题、描述、时长、状态；保留旧字段 |
| GET /shots/{id} 与列表 | ShotRead 包含四个新字段 |
| GET /shots/{id}/character-states | 新增 character_description / character_notes / character_assets 上下文 |
| POST /shots/{id}/assets、DELETE /shots/{id}/assets/{asset_id} | 原接口复用 |
| POST /assets/upload、GET /assets/{id}、GET /assets/{id}/thumbnail | 原接口复用 |
| POST /shots/{id}/character-states、DELETE /shots/{id}/character-states/{state_id} | 原接口兼容 |

聚合服务复用 Repository，不在 Route 执行 SQL。校验 active Shot → Scene → Project；状态上下文额外检查同项目，异常关系返回现有友好错误，不显示 traceback。

## 验证

| 检查 | 结果 |
| --- | --- |
| Frontend lint / build | PASS / PASS |
| Ruff check / format --check | PASS / PASS，64 个 Python 文件 |
| Backend | 148/148（原135 + 新13） |
| Browser production | 36/36（原31 + 新5） |
| Browser development | 38/38（原33 + 新5） |
| Alembic CLI | upgrade head → downgrade base → upgrade head PASS |
| Alembic current / check | 0005_shot_workspace (head) / No new upgrade operations detected |
| Populated migration | 0005 → 0004 → 0005；原 Phase 2/3/4 所有旧列、角色关系、素材关系逐行一致，FK 检查空 |

后端新增13项覆盖四字段 create/update/clear/null、legacy、完整 PATCH、Scene / Character / State / Asset 上下文、真实顺序与首尾、跨项目关系、替换幂等和失败回滚、Scene / Shot 删除、迁移与应用重启。既有135项完整保留；历史 Phase 2 schema 的夹具改为反射旧表写入，避免使用带新列的当前 ORM，原迁移断言不减少。

浏览器新增5项：Dark / Light 完整生产流程两项；未保存保护、失败草稿、重复提交、重试、返回刷新一项；加载失败重试一项；六项预览上限 / View All / Asset Detail 一项。包含导入并绑定、解绑、角色绑定 / 替换 / 移除、时长 / 状态、刷新、Previous / Next、角色与状态缩略图、1024 / 1280、保存条可见、无水平溢出。旧 CRUD / 排序 / 搜索 / 筛选与 Phase 2.5 Select 回归通过。

实际命令：

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q --basetemp=.workspace/pytest-phase5-r2 -o cache_dir=.workspace/pytest-cache
backend/.venv/Scripts/ruff.exe check backend/app backend/tests scripts
backend/.venv/Scripts/ruff.exe format --check backend/app backend/tests scripts
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend test
$env:AVW_E2E_MODE = 'dev'
npm --prefix frontend test
```

Alembic CLI 使用 `.workspace/phase5-alembic/config.json` 与 `.workspace/phase5-alembic/workspace`。pytest / E2E 全部隔离。真实 DB、原图、thumbnail、已有备份在自动化回归期间逐文件 SHA-256 保持不变。

初轮后端3项失败为测试使用旧 schema 的当前 ORM及 head 断言；已修复夹具并全量通过。初轮离开保护测试从直接访问页面回 about:blank，修正为真实应用内历史后通过。Windows 沙箱测试退出清理挂起，授权在沙箱外用同一隔离配置重跑后正常退出。保留已有 Starlette 弃用、Vite chunk / Zod 注释警告；一次浏览器主动断连产生 Windows 10054 日志，所有断言和退出码通过。无依赖更新。

## UI 截图与人工看图

以下为隔离合成夹具，不含真实素材。已人工查看两种主题下 Header / Context / Characters / Requirements / References / Production / 导航的布局；1024、1280 无横向溢出，Textarea、Save 和 Select 没有裁切或重叠。

- [Dark 1280](screenshots/phase5-shot-workspace-dark.png)
- [Light 1280](screenshots/phase5-shot-workspace-light.png)
- [Dark 1024](screenshots/phase5-shot-workspace-1024.png)
- [Light 1024](screenshots/phase5-shot-workspace-light-1024.png)

## 真实 SPF 验收

全部自动化回归结束后重新校验真实 Workspace 文件哈希，原 DB、媒体、thumbnail 与已有备份均未变。随后创建 `D:\AI-Video-Workspace\backups\before-phase5-20260923.db`，没有覆盖 Phase 4 备份；通过正常启动由 Alembic 升至 0005，没有直接编辑真实 schema，没有真实 downgrade。

- 真实项目 `SPF屏障设施培训视频`，原有 S13 标题为“风淋”，时长为0，场景名为“风淋”。用户明确确认使用实际前一镜头 S10 验证导航，并将场景改名“风淋室”；没有新增 S12 或其他替代记录。
- 通过正式 Scene PATCH 改名，Workspace UI 将 S13 时长保存为10秒，并填写用户指定 Main Action、Key Constraints、Negative Constraints。Free Notes 为“以场景固定约束和已绑定角色状态为准。”旧 status 仍为 Draft，其他镜头未修改。
- 自动聚合原有 `SPF培训女员工 → 黄色 PPE + 双层手套`；没有新建角色 / 状态。真实唯一素材仍是未确认用于本镜头的无关图片，不绑定；真实 References 空态符合数据。
- 正式页面保存 → 刷新 → Previous 到 S10 → Next 回 S13，字段保持。结束本轮服务进程并重新运行启动器，第二轮浏览器再验证场景、角色状态、10秒、四字段、刷新和前后导航，均保持。
- 逐表检查数量没有变化，所有旧列均保留，只有授权的 S13 时长 / 更新时间以及场景名称 / 更新时间改变；四个新增字段写入要求。原图、thumbnail、Phase 4 与更早备份哈希不变。`integrity_check=ok`，`foreign_key_check` 空，head 为0005。
- 真实快照、UUID、脚本、日志及截图仅存放于 Git 忽略的 `.workspace/phase5-audit/`；正式文档截图全部使用隔离夹具。验收服务已关闭，可按 README 正常启动。

## 依赖与限制

No new dependency. 前后端 dependency config / lockfile 均不变，继续只用 lucide-react named import。

- 导入与绑定仍是两次请求；绑定失败时素材保留在 Library，可重新 Bind Asset。
- Legacy Creative Requirement 在 Workspace 只读，修改仍通过旧 Shot Detail。
- Open Scene 使用既有场景列表入口；当前没有独立 Scene Detail 路由。
- 浏览器关闭提示由浏览器决定；没有离线草稿恢复或多标签并发编辑冲突解决。

Phase 5 COMPLETE。完成迁移、UI/API、回归与真实验收后停止，不进入 Phase 6 Prompt Template。
