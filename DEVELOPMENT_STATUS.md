# 开发状态

更新日期：2026-09-30

**Phase 9 — Storyboard Workflow COMPLETE。Phase 10 NOT STARTED。**

- Recovery 3确认文案回归源于 Phase 9 同时改动 Asset Detail 删除确认与 AssetService 统一错误消息。最终统一恢复既有主提示`请先解除绑定`；Storyboard 引用数量仍在 details / impact list 中，active Storyboard 仍阻止 Asset 删除和改离`STORYBOARD_6GRID`。旧 Asset Library dark/light原失败用例 **2/2 PASS**，没有修改旧 expected。
- 最终 Phase9 Backend **28/28**、Backend full **314/314**、Phase9 Browser **6/6**、production Browser **62/62**、development Browser **64/64**，均正常 exit 0。Frontend lint/build、Ruff check/format PASS。
- 独立Alembic CLI完成upgrade → downgrade → upgrade → check → current，目标`0009_storyboards`；populated migration完成0008 → 0009 → 0008 → 0009并保持Phase0–8数据。
- Recovery 3自己的自动化前后生产保护文件 **11/11 SHA-256相同**。真实SPF/S13隔离副本通过V1/V2、Selected切换、刷新、独立后端重启、thumbnail/original、Shot reference解绑、Storyboard删除独立生命周期和Asset删除保护验收。
- 生产备份`D:\AI-Video-Workspace\backups\before-phase9-20260930-192304.db`与源库SHA-256均为`6bcbefa34fd56937a7b315a76a4613bb73b64a73197a23d05b9070d7fc1778c5`；之后只执行upgrade至`0009_storyboards`。18个Phase0–8旧表逐行不变，integrity=ok、FK=0，生产Storyboard=0，无Fake记录。
- 真实外部AI未调用，仍为 **PENDING USER EXPLICIT APPROVAL**。用户原有`HANDOFF.md`未编辑、恢复、暂存或提交；Phase10保持未开始。完整schema、关系语义、三次Failure-stop历史与证据见 [Phase9状态](docs/PHASE_9_STATUS.md)。

以下保留 Phase 9 的三次 Failure-stop / recovery 历史；最终状态以上述 Recovery 3 为准。

- Recovery确认首个失败纯属locator歧义；History缩略图已有`Storyboard V1 thumbnail`可访问名称，只精确修改browser test。四个主题/宽度均通过原失败点及V2/切换/刷新步骤。
- 完整专项随后在详情原图的另一处宽泛`detail.getByRole("img")`失败：同时匹配`Storyboard V1 original`和关闭按钮Lucide X。最终 **1/6 PASS、5 failed，exit 1**；按本轮“Browser still fails”停止，未继续修复或重跑。
- 本次Recovery未执行后续Backend重跑、full browser、独立Alembic CLI、S13或生产迁移。上一轮已通过的Backend 28/28、full 314/314、lint/build/Ruff事实保留，但不冒充Recovery最终重跑。
- Recovery自己的生产哈希基线前后 **11/11相同**；生产仍0008，无假记录、无备份或迁移。HANDOFF哈希仍为`C42D15FF…763A25`。

- Recovery 2只把详情原图locator精确为`Storyboard V1 original`；Phase9 Browser **6/6 PASS**。最终Backend专项 **28/28**、full **314/314**、lint/build/Ruff均PASS。
- Production Browser full发现62项，但两个既有Asset Library dark/light用例因Phase9删除确认文案由`请先解除绑定`变为`请先解除引用`而失败。这是旧功能回归，不是locator；立即中止时 **6 passed、2 failed、54未运行**。未修改旧expected，development full未运行。
- 因Failure-stop，独立Alembic CLI、S13/reference unlink隔离验收、production backup/upgrade和commit均未执行。Recovery 2自己的生产hash前后仍 **11/11相同**。

- 用户冻结 Storyboard / ProjectAssetLink / ShotAssetLink 独立生命周期。新增0009、Storyboard model/Repository/Service/API、复用Storage导入事务、版本和采用、来源Prompt、Asset in-use/改类型保护及Shot Workspace界面；未进入Phase10。
- Backend专项 **28/28 PASS**，全量 **314/314 PASS**；Frontend lint/build、Ruff check/format PASS。
- 首次Browser专项 **0/6 PASS：1 failed、1 interrupted、4 did not run，exit 1**。新测试 `v1.getByRole("img")` 同时匹配缩略图与3个Lucide SVG，strict mode失败；未执行尺寸断言。按Failure-stop停止，未改定位器重跑。
- Browser production/development全量、独立Alembic CLI、真实S13隔离副本验收未执行；pytest迁移与populated migration通过。
- 自动化前后生产9文件 + Bootstrap/HANDOFF **11/11哈希相同**；生产仍0008，无Phase9备份/生产升级，无假生产素材/记录，无真实AI调用。
- Phase9代码未暂存、未提交；用户原有HANDOFF修改哈希不变。完整当前模型、API、文件、证据及待办见 [Phase9状态](docs/PHASE_9_STATUS.md)。

以下为此前阶段历史。

**Phase 8 — Prompt Versioning COMPLETE。Phase 9 NOT STARTED。**

- Recovery 证明 Copy 的唯一区别是 Windows Clipboard API 将 LF 表示为 CRLF；数据库、effective content、DOM textContent、writeText 入参逐字一致。仅浏览器断言规范 `\r\n → \n`，不 trim、不折叠空白，保留中文/标点/首尾空格/空行/末尾换行。
- 最终 Backend Phase 8 **33/33 PASS**，Full **286/286 PASS**；Browser Phase 8 **6/6**、production **56/56**、development **58/58 PASS**，均 exit 0。Frontend lint/build、Ruff check/format、独立 Alembic CLI 全通过。
- 0007中实际插入6条旧生成事实，覆盖2类Prompt和软删除历史；0008升级/回退/回升、check/current、唯一约束真实冲突和全部旧事实保持通过。
- 自动化前后生产/Bootstrap/HANDOFF **10/10哈希不变**；备份 `before-phase8-20260929-231526.db` 与源SHA-256相等后只upgrade至 `0008_prompt_versioning`。18张旧表逐行不变，integrity=ok、FK=0；真实SPF/S13、四项需求、角色6状态和双层手套关联完整。
- 真实S13隔离副本完成V1/Edit/Save/Refresh/Copy/Regenerate V2/选择V1与V2/刷新/新服务进程重启；生产 **11/11哈希不变**，生产Prompt为0条，无Fake污染。真实外部AI未调用，仍PENDING USER EXPLICIT APPROVAL。
- 5张无关测试截图已恢复，HANDOFF.md用户原有修改哈希保持且排除提交。模型/API/完整文件及已知限制见 [Phase 8最终验收](docs/PHASE_8_STATUS.md)。

下节保留首次停工历史，最终状态以上述Recovery为准。

**Phase 8 — Prompt Versioning NOT COMPLETE / STOPPED。Phase 9 NOT STARTED。**

- 已实现但未完成验收：线性版本、稳定旧记录回填、历史 / 编辑 / Regenerate / Select API、版本 UI 与 Copy effective content。`generated_content` 和生成快照保持；编辑只写 `edited_content`；同 Shot / Type 的版本唯一、活跃 Selected 最多一个。
- Backend Phase 8 **30/30 PASS**；Full **283/283 PASS**（旧 253 + 新 30，exit 0）。Frontend lint / build、Ruff check / format PASS。
- Browser Phase 8 **0/6 PASS：1 failed、5 did not run，exit 1**。首个 Dark 1024 用例在多行 Copy 检查中读回 CRLF，期望 LF。按本轮 Failure-stop 停止；未修改该断言后继续，未运行 Browser production / development 全量、独立 Alembic CLI 或真实 S13 隔离副本验收。
- 自动化前后生产 8 个文件 + Bootstrap / HANDOFF 共 **10/10 SHA-256 相等**。生产 revision 仍 `0007_prompt_generation`；未创建 Phase 8 生产备份或执行迁移。无真实外部 AI 调用。
- 新 revision `0008_prompt_versioning` 仅在隔离测试库运行；0/1/5 条旧记录回退回升 / check 已通过。未提交，用户原有 `M HANDOFF.md` 哈希不变。详细事实与待办见 [Phase 8 状态](docs/PHASE_8_STATUS.md)。

以下为此前阶段记录。

**Phase 7 — AI Prompt Generation COMPLETE。Phase 8 NOT STARTED。**

- AIProvider Protocol / OpenAI-compatible Provider / AIService、独立 AI Settings、实际 Shot Context 与唯一 Phase 6 Renderer 集成、成功生成事实快照、Prompt UI / Retry / Copy 已完成。
- Recovery 移除非必需 `backend/tests/__init__.py`，共享 Fake 与 E2E 入口移至 `backend/test_support`；旧 pytest 组织和导入不变。原 collection 失败历史完整保留在状态文档。
- 最终 Backend **253/253**（原有 201 + Phase 7 52），新增 Browser **7/7**，production **50/50**，development **52/52**，全部正常 exit 0。lint / build / Ruff check / format（含 scripts）及隔离 Alembic upgrade / downgrade / upgrade / check / current 全部 PASS。
- 后补 3 项全部执行；另外补充 INSERT 后 / commit 前故障注入，确认回滚无半条事实，重试仅保存一条。
- 自动化前后生产文件 **7/7** SHA-256 相等；之后备份且源 / 备份哈希一致，仅 upgrade 真实库到 `0007_prompt_generation`。17 张旧业务表逐行不变，integrity=ok，FK=0。
- 使用真实 SPF S13 的隔离副本和现有 SPF 模板完成实际上下文 → Fake Generate → persistence → refresh → Copy；没有添加资产或写生产生成记录。验收前后生产 **8/8** 文件哈希相等。
- API Key 仅独立本机明文配置；GET / PUT 不回显，未写入生产 AI 配置。真实外部 AI 验收 **PENDING USER EXPLICIT APPROVAL**。
- 文件、schema、API、测试、备份路径、已知并发限制详见 [Phase 7 验收与恢复历史](docs/PHASE_7_STATUS.md)。用户原有 HANDOFF.md 修改保持且排除提交。下方为历史阶段记录。

**Phase 6 — Prompt Template COMPLETE。Phase 7 NOT STARTED。**

- 正式 GLOBAL / PROJECT 模板管理、Category、CRUD / search / filters / soft delete / restore / Duplicate / Copy；项目删除隐藏其模板，Global 不受影响。
- 唯一 15 项变量注册表；后端白名单验证，未知 / 表达式拒绝；原文保存，重复 / 静态 / 中文合法。固定 Sample Preview 仅文本替换，不调用 AI、不写库。
- 模板库 / 项目入口、Editor、光标插入、关闭草稿保护、Shot Workspace Picker；选择仅为页面内存状态，无 Shot 模板外键 / PromptRecord / Prompt Version。
- 恢复验证仅修正过期 schema 完整表清单。浏览器收尾定位为 Windows 沙箱拒绝进程树回收；获准在相同隔离配置的正常进程环境运行，无需修改 harness 或业务代码。
- Backend **201/201**、新增 Browser **7/7**、production **43/43**、development **45/45**，全部 exit 0；lint / build / Ruff check / format 与隔离 Alembic **PASS**。
- 自动化期间真实 DB / 资产 / thumbnail / 旧备份 **6/6 哈希一致**，共享配置不变。之后创建 `before-phase6-20260924-175114.db`，源与备份 SHA-256 一致，真实库仅 upgrade 到 `0006_prompt_templates`。
- 所有旧业务表逐行不变，SPF / S13 / 角色 / 6 States / 双层手套关系和结构化字段完整。真实界面只创建 `Seedance Video Generation` 与 `SPF 六宫格分镜模板` 两条短模板，创建 / 编辑 / 预览 / 刷新 / 重启验收通过。
- Dark / Light、1024 / 1280 验证通过；No new dependency；不修改 Bootstrap / Workspace / ACL，不处理 C Workspace 或 TEMP_WORKSPACE_VERIFY。

详细报告见 [Phase 6 验收](docs/PHASE_6_STATUS.md)。以下为历史阶段记录。

**Phase 5.1 — Workspace Root Recovery & Hardening COMPLETE。已完成，等待用户验收；不进入 Phase 6 Prompt Template。**

- 统一 Bootstrap Config：用户级环境变量 `AVW_BOOTSTRAP_CONFIG_PATH` 指向 `D:\AI-Video-Workspace-Config\config.json`（仅含 `workspace_root`，位于 Workspace 与仓库之外）。普通 Windows 会话与 `%APPDATA%` 被重定向的打包应用因此解析**同一份**配置 → `D:\AI-Video-Workspace`；两个环境实测 `bootstrap_config_path` 与 `workspace_root` 完全一致。
- 修复 fallback 自播种：`initialize_workspace()` 不再调用 `bootstrap.save()`。配置缺失只在内存中使用默认 root，首次启动仍可正常初始化，但**绝不**创建或改写 Bootstrap Config；只有显式 `PUT /api/settings/workspace` 写入。非法配置仍明确报 `BOOTSTRAP_INVALID`，不回退。
- 经正式 API 将真实 Workspace Root 由空的 C 恢复到 D：未 COPY / MOVE / RENAME / 覆盖任何数据库，未修改 `APPDATA` / `HOME` / `USERPROFILE`，未新建 symlink / junction。
- 修改配置前新增安全备份 `D:\AI-Video-Workspace\backups\before-workspace-config-fix-20260924-161401.db`；源与备份 SHA-256 一致（`425A2564…`），未覆盖 Phase 4 / Phase 5 备份。
- 真实数据核验（只读 + 正式 API）：SPF Project、S13（风淋 · 10 秒 · 四个 Phase 5 字段）、SPF培训女员工、6 个 CharacterState、`S13 → 黄色 PPE + 双层手套` 全部存在。
- 最小写入验证：经正式 API 创建并软删除 `TEMP_WORKSPACE_VERIFY` → D 变化、C 全程 SHA-256 不变。
- 回归：后端 **157/157**（Phase 5 基线 148 + 新增 9），browser production **36/36**，development **38/38**；Frontend lint / build、Ruff check / format PASS；Alembic 隔离 upgrade → downgrade → upgrade PASS，`current` = `0005_shot_workspace (head)`，`check` 无新操作。**无新 migration，无 schema 变更，无新依赖。**
- 隔离：pytest autouse fixture 与 Playwright `webServer.env` 均显式注入独立的 `AVW_WORKSPACE_ROOT` / `AVW_BOOTSTRAP_CONFIG_PATH`，自动化测试不继承本机生产环境变量，也不修改用户级设置。
- 真实 DB、原图、thumbnail、全部 backups 与 C 空 Workspace 在验收前后逐文件 SHA-256 一致。
- 未删除 C，也未删除任何旧配置 / 旧备份；C 结论为 **Safe to delete（待用户确认）**。详见 [Phase 5.1 验收](docs/PHASE_5_1_STATUS.md)。

**Phase 5 — Shot Workspace COMPLETE。**

- 正式 `/shots/:shotId/workspace`，列表直达，Header / Previous / Next / Scene Context / Characters / Reference Assets / Requirements / Production Status；旧详情与 CRUD / Search / Filter / Move 保留。
- Shot 新增 main_action / key_constraints / negative_constraints / free_notes 四个 nullable TEXT 字段，ShotCreate / ShotUpdate / ShotRead 向后兼容；creative_requirement 原样保留，非空时可查看 Legacy Creative Requirement，旧编辑器继续使用。
- 一次 PATCH 显式 Save，Saved / Unsaved / Saving / Save failed、失败草稿保留、防重复提交、内部路由离开确认与浏览器原生离开保护。
- GET Workspace 聚合真实上下文与项目服务端顺序；PUT character-states 在单事务内替换同角色状态，保留 Phase 4 唯一索引、冲突校验与生命周期。
- AssetPicker / ImportAssets / Asset Detail 复用；thumbnail 预览、前六项 / View All，Unbind / Remove 只解除关系。Scene 只读，角色资产不复制到 Shot。
- 迁移 `0005_shot_workspace`；Workspace 架构、Local-first、SQLite、Managed Storage、UUID、分层边界和全部锁文件保持。No new dependency.
- lint / build / Ruff check / format PASS；backend **148/148**（135 + 13），browser production **36/36**（31 + 5），browser development **38/38**（33 + 5），均正常退出。
- 隔离 Alembic CLI upgrade → downgrade base → upgrade / current / check PASS；有数据的0005 → 0004 → 0005保持 Phase 2/3/4 所有旧列及关联，外键校验通过。
- Dark / Light、1024 / 1280截图人工检查、无水平溢出、保存条可见、Textarea / Select / thumbnail布局通过。正式文档截图为隔离夹具。
- 所有自动化测试结束后真实 Workspace 初始文件 SHA-256保持不变。随后创建 `D:\AI-Video-Workspace\backups\before-phase5-20260923.db`，正常启动执行新迁移；没有覆盖 Phase 4 备份。
- 真实 SPF S13通过正式UI保存10秒与指定四字段，保留原角色 `SPF培训女员工 → 黄色 PPE + 双层手套`；按用户确认将场景“风淋”改名“风淋室”，使用实际存在的 S10导航验收，不新建 S12。
- 刷新、S10 → S13、服务重启后保持；其他业务数据、媒体和旧备份不变，DB integrity / FK通过。未绑定用途不明的真实素材。实机截图、脚本和数据快照仅存Git忽略的审计目录。

完整范围、数据模型、API、导航、保存行为、截图和限制见 [Phase 5 验收](docs/PHASE_5_STATUS.md)。

已知限制：导入与绑定为两次请求，绑定失败时资产仍在Library；Legacy字段通过旧详情编辑；Open Scene沿用场景列表；浏览器关闭提示由浏览器控制，无离线草稿恢复及多标签编辑冲突处理。

历史验收：[Phase 5.1](docs/PHASE_5_1_STATUS.md)、[Phase 4](docs/PHASE_4_STATUS.md)、[Phase 3.1](docs/PHASE_3_1_STATUS.md)、[Phase 3](docs/PHASE_3_STATUS.md)、[Phase 2.5](docs/PHASE_2_5_STATUS.md)、[Phase 2](docs/PHASE_2_STATUS.md)、[Phase 1.5](docs/PHASE_1_5_STATUS.md)、[Phase 1](docs/PHASE_1_STATUS.md)、[Phase 0](docs/PHASE_0_STATUS.md)。范围见 [计划索引](PROJECT_PLAN.md) 和 [MVP 规格](<AI Video Workspace · MVP v0.1 开发规格.md>)。

**Phase 6 完成后停止，等待验收。Phase 7 NOT STARTED。**
