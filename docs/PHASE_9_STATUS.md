# Phase 9 — Storyboard Workflow / COMPLETE

日期：2026-09-30。最终 **Phase 9 COMPLETE；Phase 10 NOT STARTED**。

基线：`ef9b8a9732678a427d33a1db5ee61a6f9ae5bcea feat: add prompt versioning`。
用户原有 `M HANDOFF.md` 未编辑、恢复、暂存或提交，前后 SHA-256 相等。

## 首次 Failure-stop 历史

用户明确冻结 Storyboard / ProjectAssetLink / ShotAssetLink 独立生命周期后继续实现。
后端专项及全量通过，首次浏览器专项失败后按本轮 Failure-stop 停止；没有修改失败定位器、删除断言或继续重跑。

首个用例 `Phase 9 import history selection source preview dark 1024` 在
`frontend/tests/storyboards.spec.ts:88` 的缩略图检查失败：

```text
expect(v1.getByRole("img")).toHaveJSProperty("naturalWidth", 512)
strict mode violation: resolved to 4 elements
1 thumbnail <img> + 3 Lucide SVGs (Check / Eye / Image)
```

这是新浏览器测试定位器不唯一；尚未执行 naturalWidth 数值断言。不能据此声称全链 UI 通过，也不能把它描述为已证实的图片损坏。
该用例此前已检查空态、Selected 六宫格来源、首次导入、V1 Selected 和来源 Prompt 文案；第二次导入、版本切换等后续步骤未完成。
另一并行用例被中断，其余四个未运行。保留原始断言和失败产物。

失败现场位于 Git 忽略目录：

```text
frontend/test-results/storyboards-Phase-9-import-58f7e-on-source-preview-dark-1024-chromium/error-context.md
frontend/test-results/storyboards-Phase-9-import-58f7e-on-source-preview-dark-1024-chromium/trace.zip
```

| 验证项 | 本轮实际结果 |
| --- | --- |
| Phase 9 Backend | **28/28 PASS**，exit 0 |
| Backend full | **314/314 PASS**，原有 286 + 新增 28，exit 0 |
| Phase 9 Browser | **0/6 PASS**：1 failed、1 interrupted、4 did not run，exit 1 |
| Browser production full | 未运行；不沿用 Phase 8 的 56/56 作为本轮结果 |
| Browser development full | 未运行；不沿用 Phase 8 的 58/58 作为本轮结果 |
| Frontend lint | PASS，exit 0 |
| Frontend build | PASS，exit 0；保留既有 Rollup annotation / bundle warning |
| Ruff check / format --check | PASS / PASS，97 files formatted |
| 隔离迁移 pytest | PASS，包含 upgrade / downgrade / metadata check |
| populated migration pytest | PASS，0008 → 0009 → 0008 → 0009，旧表逐行保持 |
| 独立 Alembic CLI | 未执行 |
| 真实 SPF S13 隔离副本验收 | 未执行 |
| 自动化前后生产保护 | **11/11 SHA-256 相同** |

后端 JUnit 在 `.workspace/phase9/backend-storyboards.xml`、`backend-full.xml`；生产安全清单为同目录 `before.json` / `after.json`。均为忽略产物，不提交。

## 已实现但尚未完成全阶段验收

范围仅外部六宫格结果导回、整数版本、来源 Prompt、历史、采用、软删除与恢复 API。
没有图片生成、GenerationJob、队列、分格、OCR、视频业务实体或 Phase 10 功能；无新依赖。

### 当前 schema

新增 migration `0009_storyboards`，down_revision=`0008_prompt_versioning`，未更改既有 migration。

```text
storyboards
id UUID PK
shot_id UUID FK shots.id
asset_id UUID FK assets.id
source_prompt_record_id UUID FK prompt_records.id nullable
storyboard_type String(20), 固定 GRID_6，CHECK
version INTEGER > 0
is_selected BOOLEAN
notes nullable TEXT
created_at / updated_at UTC timestamp
deleted_at nullable UTC timestamp
UNIQUE(shot_id, version)
UNIQUE INDEX shot_id WHERE is_selected=1 AND deleted_at IS NULL
indexes: shot_id / asset_id / source_prompt_record_id
```

沿用规格第22节的 nullable 来源及 storyboard_type；本阶段只允许 GRID_6。无冗余 project_id，通过 Shot 获取项目。
Storyboard 没有文件路径、缩略图路径、binary 或 base64 字段。Asset 为唯一媒体事实，不建立 UNIQUE(asset_id)，已有 Asset 可跨版本复用。

### 版本、来源和 Selected

- 同一 Shot 从1开始递增；软删除版本继续占用版本号。history 按整数 version 降序。
- 首次和后续创建都自动采用新版本；清除旧采用、版本分配、关系建立及新记录写入在事务内完成。复用 Phase 8 的先写入获取 SQLite writer lock、再 MAX+1 模式，DB 唯一约束兜底；跨进程 busy/冲突可以失败回滚。
- Select 只改变 is_selected / updated_at，不覆盖 asset_id、shot_id、source_prompt_record_id、version、created_at。新结果必须新建版本，无覆盖历史的 PATCH API。
- 来源可为空；非空必须是同一 Shot 的具体 PromptRecord，Service 拒绝跨 Shot / Project。未额外限制来源类别。默认 UI 解析当前 Selected STORYBOARD_6GRID Prompt，也可显式选择其他具体版本或不关联。
- 不复制 Prompt 文本。Prompt selected / edited_content 变化不改变 Storyboard 的 source ID。Read 返回来源版本、类别及 Edited metadata；不新建 Prompt 删除 API。

### 独立关系（本轮用户冻结规则）

导入复用 StorageService 的 stream / staging / metadata / thumbnail / 文件限制与媒体安全校验。
在其既有 database.session 内创建 Asset，随后 StoryboardService 确保 ProjectAssetLink、ShotAssetLink 并创建 Storyboard。DB提交失败继续复用已有文件、thumbnail、temp 清理策略。

Use Existing Asset 同样在事务中确保两类 Link 并创建新版本；复用现有 active Link，已软删除 Link 通过原有 link helper 恢复同一行，不复制媒体。

三者没有共享 owner / source 生命周期：

- 删除 Storyboard 只软删除该版本并清除它的 Selected；不自动 fallback，不删除 Asset / 两类 Link。
- 解绑 Project / Shot Reference 只作用于既有 Link，Storyboard 不变；Storyboard 的读取和媒体预览直接经 asset_id 解析，完全不要求 Link 仍存在。
- 多版本共用同一 Asset 合法。删除一个版本不会改变其他版本或绑定。
- 没有添加 Link owner/source/purpose 字段、所有权实体或自动回收逻辑。
- Restore API 恢复原版本且不自动 Selected，也不重建参考绑定；Asset 必须先恢复且仍是六宫格分类。
- Shot / Project 删除通过父级可见性隐藏 Storyboard，原关系保留；对已删除父级仍允许删除 Storyboard 以释放引用。

### Asset 引用保护

AssetService 的统一 in-use 检查加入 active Storyboard，包括父级已软删除但 Storyboard 仍有效的引用。
返回409 ASSET_IN_USE及引用数。即使两类 Link 已解绑，只要 Storyboard 有效仍不能删除 Asset。
被有效 Storyboard 使用的 Asset 也不能改成 IMAGE / VIDEO / OTHER，防止创建后破坏类型约束。
Storyboard 软删除后不再单独占用 Asset；独立 Link / Character 等其他引用仍按原规则保护。
Asset Detail 返回 Storyboard 引用并提供相应 Shot Workspace 链接。

### 当前 API

```text
GET  /api/shots/{shot_id}/storyboards[?include_deleted=true]
POST /api/shots/{shot_id}/storyboards
     {asset_id, source_prompt_record_id?, notes?}
POST /api/shots/{shot_id}/storyboards/import
     ?filename=...&source_prompt_record_id=...&notes=...
     raw file request body，沿用现有上传 convention
GET  /api/storyboards/{id}[?include_deleted=true]
POST /api/storyboards/{id}/select
DELETE /api/storyboards/{id}
POST /api/storyboards/{id}/restore
```

history 的 is_selected 标记用于当前采用查找。读取包含 Asset metadata 与来源 Prompt metadata。
路由仅委托 Service；版本分配、跨 Shot 校验和关联事务在 Service，SQL 在 Repository。

### 当前 UI

Shot Workspace 新增 Storyboard panel：来源版本选择、可选备注、单图选择/拖入、Use Existing Asset、Current Selected、History、Select、View、Open Asset、确认软删除。
已有 AssetPicker 添加可选固定分类，Storyboard 使用时锁定 STORYBOARD_6GRID，保留其他业务默认行为。
列表/当前采用均加载现有 thumbnail endpoint，查看详情才加载 file endpoint。继续使用原公共组件、深浅主题 tokens 和 Lucide。
导入期间纳入页面离开保护。恢复仅后端 API，本轮未添加回收站 UX。
上述 UI 已构建，浏览器验收未完成，不宣称全部可用或视觉通过。

## 后端测试覆盖

28项覆盖导入及三类关系、既有Link不重复、同Asset多版本无复制、单独删除/解绑、删除采用不fallback、恢复不重建Link、来源稳定与跨Shot/Project拒绝、错误/缺失/已删除Asset、缺失父级/Prompt、版本正数/唯一/Selected唯一/FK/type真实约束冲突、并发创建/选择、不同连接争抢同版本、五个写入/提交故障点回滚与文件清理、父级删除恢复、重启持久化、有数据迁移回退回升。
现有测试只更新两处正式 schema head / 完整表清单以纳入0009和storyboards，保留原断言；原286项全部通过。

## Production safety / SPF

自动化前成功读取生产9文件及Bootstrap/HANDOFF，自动化后 **11/11相等**。数据库前后 SHA-256：

```text
6bcbefa34fd56937a7b315a76a4613bb73b64a73197a23d05b9070d7fc1778c5
```

生产仍为 `0008_prompt_versioning`。本轮没有创建 Phase9 backup、升级生产或写测试 Storyboard/Asset。没有 source/backup SHA可报告。
接手只读查询 integrity_check=ok、foreign_key_check=0；之后数据库字节未变。本轮未再次执行迁移后的 SPF 定向业务核验，因为未进行生产迁移。
真实S13隔离副本尚未验收；pytest 的合成S13与浏览器测试 fixtures 全部在隔离Workspace，不能冒充真实SPF验收。
自动化不会连接真实Provider；真实外部AI仍 **PENDING USER EXPLICIT APPROVAL**。

## 修改文件 / Git

本轮新增：

```text
backend/app/api/routes/storyboards.py
backend/app/migrations/versions/0009_storyboards.py
backend/app/models/storyboards.py
backend/app/repositories/storyboards.py
backend/app/schemas/storyboards.py
backend/app/services/storyboards.py
backend/tests/test_storyboards.py
frontend/src/features/storyboards/api.ts
frontend/src/features/storyboards/storyboard-panel.tsx
frontend/src/features/storyboards/storyboards.css
frontend/tests/storyboards.spec.ts
docs/PHASE_9_STATUS.md
```

本轮修改：

```text
backend/app/main.py
backend/app/models/__init__.py
backend/app/schemas/assets.py
backend/app/services/assets.py
backend/app/services/storage/service.py
backend/tests/test_bootstrap.py
backend/tests/test_database.py
frontend/src/features/assets/asset-detail.tsx
frontend/src/features/assets/asset-picker.tsx
frontend/src/features/assets/types.ts
frontend/src/features/shots/shot-workspace.tsx
README.md
DEVELOPMENT_STATUS.md
PROJECT_PLAN.md
```

Phase9-owned working tree **非clean，未暂存、未提交**。HANDOFF仅用户原有修改，其哈希不变。
DB、备份、测试素材、trace、截图、dist、忽略审计脚本与配置均不进入提交。没有修改旧migration、ACL、C盘旧Workspace或TEMP_WORKSPACE_VERIFY。

## 已知限制与后续门槛

既有 API Key 本机明文、AI等待持Workspace锁/读事务、timeout重试可能重复计费等限制保留；不在Phase9处理。
Storyboard历史暂未分页；来源关联固定PromptRecord而非编辑时文本快照，符合不复制Prompt内容的规则。服务仍受既有SQLite单写者/Workspace锁限制，没有后台任务系统。

按 Failure-stop 已停止。恢复后仍需修复唯一缩略图定位器并完成专项/全量浏览器、独立Alembic CLI、真实S13隔离副本刷新/新后端进程重启、生产哈希复核。全部通过才可生产备份/只upgrade、旧数据验证及提交。

**Phase 9 NOT COMPLETE。Phase 10 NOT STARTED。**

## Recovery / Completion Pass — 第二次停止

Recovery 先读取实际失败页面与 JSX。History card 的真实缩略图已经提供稳定可访问名称
`Storyboard V1 thumbnail`；同一 article 内另外三个 role=img 匹配来自 Select / View /
Open Asset 按钮中的 Lucide SVG。根因确认是 browser test 使用无 name 的宽泛 role locator，
不是 thumbnail endpoint、Asset 关系或图片加载失败。

只修改 `frontend/tests/storyboards.spec.ts`：

```text
v1.getByRole("img")
→ v1.getByRole("img", { name: "Storyboard V1 thumbnail", exact: true })
```

未修改 UI、Lucide、schema、API、Service 或业务语义。重新从专项第一项运行全部6项。
四个主题/宽度用例均通过原失败点，并继续通过V2创建、V1保留、V2采用、切换V1、
唯一Selected和刷新持久化；随后在详情预览的另一处既有宽泛 locator 停止：

```text
detail.getByRole("img")
```

它同时匹配 `img`（accessible name=`Storyboard V1 original`）和关闭按钮中的 Lucide X。
已有稳定语义定位方式，但本轮附件明确把“Phase 9 Browser still fails”列为立即停止条件，
因此没有继续修复第二处 locator、没有再次重跑，也没有执行后续 Backend / full Browser /
Alembic CLI / S13 / production migration。

Recovery专项最终实际结果：**1/6 PASS、5 failed、exit 1**。通过项为无效图片失败后显式重试；
四个主题/宽度用例及 Use Existing Asset 用例均在同一详情原图定位器 strict-mode error 处失败。
这仍是测试定位歧义；trace显示目标原图已出现在DOM，尚未执行 naturalWidth 断言，不能将专项记为通过。

本次 Recovery 建立了独立生产安全基线，不复用前次结果。浏览器自动化前后生产9文件、
Bootstrap与HANDOFF共 **11/11 SHA-256相同**；生产DB仍为0008且SHA-256仍为
`6bcbefa34fd56937a7b315a76a4613bb73b64a73197a23d05b9070d7fc1778c5`。
Git-managed screenshots与开始时相同，test-results / trace / fixtures / dist均在忽略范围。
HANDOFF SHA-256仍为`c42d15ff745ea67b90d10a1be80e652151deed57e805259698f424963b763a25`。

**Recovery 后最终状态仍为 Phase 9 NOT COMPLETE / STOPPED；Phase 10 NOT STARTED。**

## Recovery / Completion Pass 2 — locator通过，完整回归停止

第二次Recovery复核详情DOM，确认原图已具有稳定可访问名称`Storyboard V1 original`；
关闭按钮内Lucide X属于独立控件。仅把两处详情断言从宽泛`detail.getByRole("img")`
改为：

```text
detail.getByRole("img", {
  name: "Storyboard V1 original",
  exact: true,
})
```

未改UI、Lucide、业务代码、schema、API或migration。保留第一次thumbnail精确定位修复。
Phase9 Browser随后完整执行，最终 **6/6 PASS，exit 0**。实际覆盖空态、来源Prompt、V1/V2、
thumbnail、原图详情、历史顺序、新版本自动采用、切换采用、刷新持久化、已有Asset复用、
无效类型拒绝、解绑ShotAssetLink后Storyboard及原图仍可用、删除关系独立性和失败重试。

之后重新验证：Phase9 Backend **28/28 PASS**；Backend full **314/314 PASS**；Frontend
lint/build、Ruff check/format均PASS。Build只有既有Rollup annotation与bundle size warning。

Production Browser full共发现62项，但最先执行的两个旧Asset Library dark/light用例失败。
失败不是locator：Phase9把既有Asset删除确认文案从测试及原产品契约中的`请先解除绑定`
改成了`请先解除引用`。收到的实际文案为：

```text
仍有 1 个项目、1 个镜头、0 个角色、0 个状态和 0 个分镜引用，请先解除引用。
```

旧用例明确要求`请先解除绑定`，因此这是Phase9引入的旧功能回归。确认删除后的旧API错误文案
也可能受到新增措辞影响，但运行尚未到该断言。按本轮Failure-stop立即中止runner，没有修改旧测试
expected、没有继续development full、Alembic CLI、S13或production migration。
中止时production full实际为 **6 passed、2 failed、54未运行，非PASS**。

第二次Recovery使用新的独立生产hash基线；全部自动化前后生产9文件、Bootstrap、HANDOFF
共 **11/11 SHA-256相同**。生产DB仍为0008，SHA-256仍为
`6bcbefa34fd56937a7b315a76a4613bb73b64a73197a23d05b9070d7fc1778c5`。
HANDOFF仍为用户原有修改，SHA-256仍为
`c42d15ff745ea67b90d10a1be80e652151deed57e805259698f424963b763a25`。
Git-managed screenshots与基线一致；test-results、trace、dist和隔离fixtures保持忽略。

**Recovery 2最终状态：Phase 9 NOT COMPLETE / STOPPED；Phase 10 NOT STARTED。**

## Recovery / Completion Pass 3 — 最终完成

第三次 Recovery 的唯一产品回归是既有 Asset 删除主提示被 Phase 9 从
`请先解除绑定`改为`请先解除引用`。根因同时存在于统一后端 `AssetService` 错误消息和
Asset Detail 删除影响提示；不是旧测试错误，也不是 dark/light 页面各自的问题。

最终把统一用户主提示恢复为既有兼容契约`请先解除绑定`。没有修改旧测试 expected；
Storyboard 引用仍保留在 Asset details / impact list，且生命周期保护没有弱化：

```text
active Storyboard → DELETE Asset → 409 ASSET_IN_USE
active Storyboard → Asset type cannot change away from STORYBOARD_6GRID
```

`backend/tests/test_storyboards.py`在仅有 active Storyboard 引用的场景同时检查
`ASSET_IN_USE`、兼容主提示和 Storyboard 引用详情。旧 Asset Library dark/light原失败用例
先单独重跑，结果 **2/2 PASS**。

### 最终验证

| 验证项 | 最终结果 |
| --- | --- |
| 旧 Asset Library dark/light | **2/2 PASS**，exit 0 |
| Phase 9 Backend | **28/28 PASS**，exit 0 |
| Backend full | **314/314 PASS**，exit 0 |
| Phase 9 Browser | **6/6 PASS**，exit 0 |
| Browser production full | **62/62 PASS**，exit 0 |
| Browser development full | **64/64 PASS**，exit 0 |
| Frontend lint / build | **PASS / PASS**；仅既有 Rollup annotation / bundle-size warning |
| Ruff check / format --check | **PASS / PASS**，97 files |
| 独立 Alembic CLI | **PASS**：upgrade → downgrade → upgrade → check → current；`0009_storyboards (head)` |
| populated migration | **PASS**：0008 → 0009 → 0008 → 0009，Phase 0–8 数据保持 |
| Recovery 3生产保护 | **11/11 SHA-256 UNCHANGED**，发生在生产升级前 |

所有 Browser runner 都完整退出；受管 Phase 5 截图恢复为 Recovery 3 起始基线。
`test-results`、trace、fixtures、隔离 DB、临时 S13 验收脚本和 `dist` 均未进入正式修改。
两处图片断言继续使用精确 accessible name：`Storyboard V1 thumbnail`和
`Storyboard V1 original`，没有改回宽泛 locator。

### 真实 SPF / S13 隔离副本验收

从 `D:\AI-Video-Workspace`完整复制出的隔离 Workspace 使用真实 SPF/S13 旧数据，
生产 DB 在该验收前后未被测试服务打开写入。验收使用现有六宫格模板与隔离 Fake Provider，
没有调用真实或收费 AI：

- 确认 S13、风淋、10秒、风淋室、四项结构化需求、SPF培训女员工、6个CharacterState及
  `黄色 PPE + 双层手套`关系。
- 从真实 S13 source Prompt 导入 V1，V1自动Selected，thumbnail和original可用；导入V2后
  V1保留、V2自动Selected；人工选回V1后只有V1 Selected。
- 刷新后历史与Selected保持；停止首个服务并启动第二个独立后端进程后，历史、Selected、
  source Prompt和媒体文件继续保持。
- 解绑V1的ShotAssetLink后，Storyboard、Asset、thumbnail、original和ProjectAssetLink保持；
  ShotAssetLink不存在是合法状态。
- 此时删除Asset仍被仅存的active Storyboard阻止，UI与API主提示包含`请先解除绑定`，
  Storyboard和Asset均未改变。
- 删除V1 Storyboard只删除该关系；V1 Asset及ProjectAssetLink保持，V2不受影响，且不会
  自动回收Link或选择fallback。

### 生产保护、备份与迁移

Recovery 3在任何自动化前重新读取生产9个Workspace文件、Bootstrap和HANDOFF，建立
11项独立hash baseline；全部自动化和隔离验收结束后结果为 **UNCHANGED 11/11**。
升级前生产 DB SHA-256：

```text
6bcbefa34fd56937a7b315a76a4613bb73b64a73197a23d05b9070d7fc1778c5
```

满足全部前置条件后创建：

```text
D:\AI-Video-Workspace\backups\before-phase9-20260930-192304.db
```

源库与备份 SHA-256 均为上述值。随后对生产只执行 `alembic upgrade head`；没有 downgrade、
reset、drop、recreate、DELETE或人工SQL修复。升级后：

```text
revision = 0009_storyboards
PRAGMA integrity_check = ok
PRAGMA foreign_key_check = 0 rows
```

升级前对全部18个Phase 0–8表逐列逐行建立快照，升级后精确相等。SPF项目、S13、风淋、
10秒、风淋室、四项结构化需求、SPF培训女员工、6个状态和黄色PPE双层手套关系均保持。
生产 Prompt history 迁移前为0条、Selected为0条，迁移后保持相同；没有把隔离 Fake Prompt
写入生产。生产 `storyboards` 为0条：**Fake Production Storyboard records: NO**。

### 最终语义

- Storyboard属于Shot并直接引用Asset，可选引用同Shot的具体PromptRecord；媒体展示、历史、
  Selected、thumbnail和file lookup全部通过`Storyboard.asset_id → Asset`解析。
- version为每Shot正整数且唯一，软删除版本不复用。首次和新版本自动Selected并清除旧Selected；
  人工选择保持至刷新/重启，删除Selected不自动fallback。
- 导入事务依次建立Asset、确保ProjectAssetLink、确保ShotAssetLink、创建Storyboard；已有Link
  复用。事务一致性不代表生命周期所有权。
- Storyboard、ProjectAssetLink和ShotAssetLink是独立业务关系。删除Storyboard保留Asset/Link，
  解绑Reference保留Storyboard/Asset，同Asset可被多版本及其他关系复用；没有owner/source/
  purpose字段、引用所有权实体或自动回收。
- active Storyboard正式进入Asset in-use与类型变更保护；用户主提示继续使用Phase 0–8兼容文案，
  真实引用类型由details表达。

### 已知限制与边界

Storyboard历史本阶段未分页；恢复只有后端API，没有新增回收站UI。来源关联保存PromptRecord ID
而不复制Prompt文本，符合冻结规格。SQLite仍为单写者，跨进程争抢可返回busy/冲突并回滚；
没有后台任务、GenerationJob、图片/视频生成、分格、OCR或Phase10 VideoResult。
真实外部AI仍为 **PENDING USER EXPLICIT APPROVAL**。

用户原有`HANDOFF.md`保持未编辑、未恢复、未暂存、未提交，SHA-256为
`c42d15ff745ea67b90d10a1be80e652151deed57e805259698f424963b763a25`。

**Phase 9 COMPLETE。Phase 10 NOT STARTED。**
