# Phase 8 — Prompt Versioning / COMPLETE

最终收尾日期：2026-09-30。

日期：2026-09-29。接手 HEAD：`15b9607e0ee785595792c93d9ba4774aae71620d`（`feat: add AI prompt generation`）。Recovery / Completion Pass 已全部通过，Phase 8 COMPLETE，Phase 9 NOT STARTED。最终验收见末尾 Recovery；以下保留首次停止时的原始状态与结果。Phase 8 提交消息为 `feat: add prompt versioning`，实际 hash 见 Git log 与最终交付报告。

## 停止原因

按用户附件的 Failure-stop 与关键验收未通过即停止规则，在首次浏览器专项失败后停止开发及剩余测试，没有改断言后继续，没有提交或迁移生产。

命令：`npm --prefix frontend test -- prompts.spec.ts --grep 'Phase 8' --max-failures=1`。

结果：**1 failed，5 did not run，exit code 1；0/6 PASS**。用例 `Phase 8 history edit regenerate select Copy dark 1024` 已完成打开 V1、编辑、保存、刷新保持、Edited 显示，随后在 `frontend/tests/prompts.spec.ts:324` 的剪贴板逐字比较失败：预期 `中文编辑，保留换行！\n双门互锁；角色不看镜头。`，实际换行为 `\r\n`。运行于 Windows Chromium；目前证据只确认剪贴板读回换行差异，尚未完成进一步定位或修复，不将原因认定为产品内容损坏或纯测试问题。

失败现场为 Git 忽略目录 `frontend/test-results/prompts-Phase-8-history-ed-8d093-erate-select-Copy-dark-1024-chromium/` 内的 `error-context.md` 和 `trace.zip`。无 skip/xfail、删除 assertion、强制 exit 0 或旧迁移改写。

## 接手审计与边界

已读取任务附件、PROJECT_PLAN、MVP 规格、DEVELOPMENT_STATUS、README、Phase 6 / 7 状态以及实际模型、Repository、Service、Routes、Schemas、前端、测试与 0007 migration。Git status / log / show stat / name-status 确认目标 HEAD；生产只读确认 `0007_prompt_generation`，prompt_records=0，integrity=ok、foreign_key_check=0。用户原有修改只有 HANDOFF.md，未改写、暂存或提交。

范围仅线性 Prompt 版本、History、Edit、Regenerate、Select 与 Copy。未创建 Storyboard / VideoResult / GenerationJob / 队列 / 分支 / 审批或生成图片视频 API；未新增依赖或更换技术栈。

## 模型与事务规则（已实现，阶段尚未验收完成）

沿用表 `prompt_records`、UUID 主键及既有两外键 `shot_id → shots.id`、`template_id → prompt_templates.id`；两外键当前仍非空。保留原 shot_id / template_id 索引。

完整列：

```text
id UUID PK（成功 operation_id）
shot_id UUID FK
template_id UUID FK
template_name String(255)
template_content TEXT
prompt_type String(40)
context_json JSON
rendered_input TEXT
input_hash String(64)
generated_content TEXT
provider String(80)
model_name String(255)
created_at / updated_at UTC timestamp
deleted_at nullable UTC timestamp
version INTEGER NOT NULL
edited_content TEXT NULL
is_selected BOOLEAN NOT NULL
```

`effective_content` 为响应/模型计算属性，不增加数据库列：`edited_content` 非 null 时使用它，否则使用 `generated_content`；空字符串是有效人工编辑，null 可通过 API 清除编辑。编辑请求上限 500,000 字符，保留中文、全角标点和换行。

- 同一 shot_id + prompt_type 从 1 开始整数递增；已软删除记录仍参与最大版本计算，号码不复用。历史按整数 version 降序，再按 created_at / UUID 降序稳定排序，可筛选 prompt_type。
- DB 唯一约束 `uq_prompt_version(shot_id,prompt_type,version)`，CHECK version > 0；部分唯一索引 `uq_prompt_selected(shot_id,prompt_type)` 限定 is_selected=true 且 deleted_at IS NULL。SQLite 与 PostgreSQL 条件均定义。
- 仅 `is_selected` 表达最终采用，无另一个 final / active 状态。首次 Generate 和后续 Generate / Regenerate 成功均自动采用新版本；旧版本取消采用。手工 Select 原子清除旧选择、采用目标。
- Edit 保持同一记录，只修改 edited_content / updated_at；请求 schema 禁止生成事实和选择字段，PromptRepository 更新白名单仅 edited_content / is_selected。没有声明对绕过应用的任意 SQL 写入提供不可变触发器保护。
- Regenerate 使用来源记录的 template_id、该模板当前内容及最新保存 Shot Context，复用唯一 Renderer → AIService → AIProvider；保存新的全部快照和 Provider / Model，绝不把人工编辑当作 AI 输入。模板类型变化返回 409，模板删除不可重新生成，旧事实仍可读。
- Regenerate body 要求新 operation_id 与预览 input_hash；拒绝 operation_id 等于源记录 ID。成功 operation 重试返回原记录，不重复调用 Provider，也不抢回手工 Selected；失败操作无成功记录，可显式 Retry。
- Workspace 请求级锁和 session 事务覆盖清除 selection、计算最大 version、INSERT / update、commit。分配前执行写操作取得 SQLite writer lock；DB 约束兜底，异常回滚。没有新增并发框架。跨进程读取事务升级可能遇到 SQLite busy 而失败回滚，未实现跨进程自动重试或远端计费幂等保证。
- 保留 BaseModel 的 deleted_at，没有新增 Prompt 删除 / 回收站 API；Repository soft_delete 清除 selected，删除选中版本后不自动采用其他版本。Shot / Project 删除后通过已有父级可见性隐藏 Prompt。

## Migration

新增 `0008_prompt_versioning`，down_revision=`0007_prompt_generation`；没有改动旧迁移。

旧记录按 shot_id / prompt_type 分组，按 created_at / UUID 稳定回填 1…N，含软删除版本；每组最新非删除记录设为 Selected，edited_content 为 null。不会假设生产空表。downgrade 只丢失 Phase 8 三列及其约束，保留全部 Phase 7 生成事实。

专项测试验证 0 / 1 / 5 条旧记录、相同时间戳 UUID 排序、旧事实逐列不变、所有旧业务表逐行不变、回退回升、Alembic check / FK。完整旧迁移回归包含 downgrade base。独立 Alembic CLI upgrade / downgrade / upgrade / check / current **未执行**，不能声称最终 CLI 验收完成。生产未执行 0008。

## API

所有业务逻辑仍 Route → AIService → PromptRepository；AI 仍经 AIProvider。保留所有 Phase 7 endpoints，latest 仍表示最新成功记录，不改成 selected。

| 方法 / 路径 | 行为 |
| --- | --- |
| GET /api/shots/{shot_id}/prompts | 历史，支持可选 prompt_type |
| GET /api/prompts/{identifier} | 既有详情，新增 version/edit/selection/effective 字段 |
| PATCH /api/prompts/{identifier} | `{edited_content: string 或 null}` |
| POST /api/prompts/{identifier}/regenerate | `{operation_id, input_hash}`；来源模板 + 当前 Context |
| POST /api/prompts/{identifier}/select | 采用该版本 |
| POST /api/shots/{shot_id}/prompts/preview | 既有真实预览，为 Regenerate 获得最新 input_hash |
| POST /api/shots/{shot_id}/prompts/generate | 既有入口，新建下一版本并采用 |
| GET /api/shots/{shot_id}/prompts/latest | 兼容原最新成功结果语义 |

## UI

Shot Workspace 增加 Version History、Vn / Selected / Edited、模板 / 类型 / provider / model / 时间，支持查看旧版本、生成输入和原始事实、编辑保存、复制已保存有效内容、复制当前类型 Selected Prompt、Regenerate / Retry、手工采用。Regenerate 来源模板明确显示；Shot requirements 未保存时阻止生成，Prompt dirty 时阻止 Regenerate / Select / Generate。

Prompt 草稿接入已有 Shot Workspace useBlocker / useBeforeUnload，不新增第二个路由 blocker。历史切换沿用 Dialog + Stay / Discard 模式。提供 loading / empty / error / saving / selecting / regenerating 状态。上述为实现说明，浏览器验收尚未完成，不能报告全部交互通过。

## 实际验证

| 项目 | 结果 |
| --- | --- |
| Phase 8 Backend | **30/30 PASS**，14.12s，exit 0 |
| Backend FULL | **283/283 PASS**（旧253 + 新30），81.79s，exit 0 |
| Phase 7 Backend | 全量包含原52项并通过；生成事实、Retry、重启与快照断言保留 |
| Phase 8 Browser | **0/6 PASS；1 failed、5 did not run；exit 1** |
| Browser production FULL | 未执行 |
| Browser development FULL | 未执行 |
| Phase 7 Browser 7项 | 本轮未执行 |
| Frontend lint / build | PASS，exit 0；浏览器用例补齐后再次 lint PASS |
| Ruff check / format --check | PASS，90 files already formatted |
| 隔离 Alembic | pytest 迁移/数据回归 PASS；独立 CLI 未执行 |
| 真实 SPF S13 隔离副本 Fake 版本验收 | 未执行 |
| Real external AI | PENDING USER EXPLICIT APPROVAL，未调用 |

新测试覆盖人工编辑和 null/空白/长文本、不可更新生成字段、Context/Template/Provider/Model 历史稳定性、连续版本与整数排序、同实例并发生成、DB 唯一性/正数约束、Select 切换、operation replay、注入写失败回滚、Provider 错误/空输出、未知/已删除记录、跨项目模板、Shot/Type 隔离、删除版本不复用、旧数据迁移。

旧测试的范围断言有明确更新：Phase 7 “不存在 version/edit/selected”改为新字段精确值，浏览器“没有历史”改为历史入口可见，两个 schema 测试 head 改为0008；其他既有业务断言保留。这些调整在运行回归前完成，不是失败后删除断言。

首次 Ruff 检查发现新文件导入 fixture 名遮蔽与格式问题，执行前改为本地 fixture 并格式化，之后 Ruff 全部通过。不是 pytest collection failure。既有 TestClient 弃用及 Vite bundle / 注释警告仍存在，未新增依赖去处理。

## Production safety / SPF

自动化前后成功读取生产 Workspace 全部8个文件，另校验 Bootstrap Config 与 HANDOFF.md，共 **10/10 SHA-256 完全相同**，文件集合无增减。证据在忽略目录 `.workspace/phase8-audit/{before,after}.json`；JUnit 同目录。

生产数据库前后 SHA-256 均为：

```text
f1ccc50edb6457e2884dae36eb8745eab025c39616df7afab7c626980f582b36
```

- 生产 revision 前后均为 `0007_prompt_generation`；prompt_records=0。
- 接手只读检查 integrity_check=ok、foreign_key_check=0；自动化后 DB 字节哈希完全相同。
- SPF 旧数据安全证据为整个生产 DB 未变；未完成新的逐表业务验收或真实 S13 副本版本工作流，不能声称 S13 Phase 8 PASS。
- Phase 8 production backup path：**无，未创建**。source == backup SHA-256：**未执行**。没有在未全部通过时迁移真实库。
- 未修改真实资产/绑定、Bootstrap、用户环境变量、ACL、C fallback、TEMP_WORKSPACE_VERIFY 或旧备份。

## 文件与 Git

Phase 8-owned 修改 / 新增：

```text
backend/app/api/routes/prompts.py
backend/app/models/prompts.py
backend/app/repositories/prompts.py
backend/app/schemas/ai.py
backend/app/services/ai/service.py
backend/app/migrations/versions/0008_prompt_versioning.py (new)
backend/tests/test_prompt_versioning.py (new)
backend/tests/test_ai.py
backend/tests/test_bootstrap.py
backend/tests/test_database.py
frontend/src/features/prompts/api.ts
frontend/src/features/prompts/prompt-panel.tsx
frontend/src/features/prompts/prompts.css
frontend/src/features/prompts/version-workspace.tsx (new)
frontend/src/features/shots/shot-workspace.tsx
frontend/tests/prompts.spec.ts
README.md
DEVELOPMENT_STATUS.md
PROJECT_PLAN.md
docs/PHASE_8_STATUS.md (new)
```

Phase 8-owned working tree：未提交，不 clean。未暂存。Pre-existing user change：`M HANDOFF.md`，哈希前后相同，未改写/restore/checkout/reset/stage/commit。数据库、备份、AI 配置、测试输出、audit 和 dist 均未纳入提交；本轮没有已跟踪截图变化。

## 剩余工作与限制

恢复后先定位多行 Copy 的 Windows 换行行为，保留原始事实及完整复制语义，再执行六项专项和完整浏览器双模式回归、独立 Alembic、哈希复核、生产备份校验和只 upgrade、旧数据验证与真实 S13 隔离副本 Fake 验收。只有全部完成才可提交与标记 COMPLETE。

现有 Key 本机明文、AI 等待持有 Workspace 锁/读取事务、跨进程 SQLite busy、远端 timeout 重试可能重复计费、无队列/取消/streaming、无多标签人工编辑冲突处理继续为限制；历史目前无分页。Phase 8 UI 完整性仍受本次停工约束，未完成视觉截图验收。

**Phase 8 NOT COMPLETE / STOPPED。Phase 9 NOT STARTED。**

## Recovery / Completion Pass — 2026-09-29

用户明确授权继续当前工作树，保持已通过的版本业务规则，完成诊断、最终回归、备份迁移与S13隔离验收。本次没有重新设计或改写Prompt业务实现；恢复期间产品模型、Renderer、数据库正文和Copy实现保持不变。

### Clipboard root cause / fix

诊断使用隔离Fake Provider、真实Chromium和真实系统剪贴板。包装 `navigator.clipboard.writeText` 只记录实参并委托原生方法，没有mock复制结果。测试文本包含中文全角标点、连续空行、首尾空格和末尾换行。

逐字检查：

| 位置 | 实际结果 |
| --- | --- |
| 保存后的 edited_content | 与编辑输入逐字一致，LF |
| effective_content | 与 edited_content 逐字一致，LF |
| 页面 DOM textContent（刷新后） | 与输入逐字一致，LF |
| writeText 原生调用实参 | 与输入逐字一致，LF |
| readText 返回 | 与输入相比，每个 LF 变成 CRLF；无其他字符变化 |
| 原始 generated_content | 与首次生成结果逐字一致 |

同时验证 `read === input.replace(/\n/g, '\r\n')`、逻辑行数组相等及只替换CRLF后完整字符串相等。未出现多空行、少换行、trim、字符丢失/增加、标点变化或截断。根因明确为本机Windows Chromium Clipboard API的行尾表示转换。

最终修复仅在 `frontend/tests/prompts.spec.ts` 的 `expectClipboard` 中对实际值与期望值执行 `replace(/\r\n/g, '\n')` 后比较完整文本；不移除独立CR，不trim，不折叠空白，不修改产品内容。四个主题/宽度组合均验证：V1未编辑Copy原生成文本 → V1编辑后Copy编辑文本 → V2 Copy其有效内容 → 返回V1 Copy其编辑文本，另验证Copy Selected。

诊断 **1/1 PASS，exit0**，证据保存于忽略目录 `.workspace/phase8-recovery/clipboard-evidence.json`。诊断配置初次启动因临时配置目录导致相对Python路径错误，未进入测试；指定正确webServer cwd后通过，未改正式harness或业务代码。首次浏览器失败历史仍完整保留在本文前部。

### Final regression

| 项目 | 最终真实执行结果 |
| --- | --- |
| Phase 8 Backend | **33 passed**，16.44s，exit0 |
| Backend FULL | **286 passed**，93.76s，exit0（旧253 + Phase8 33） |
| Phase 7 Backend | 完整回归包含原52项，全部通过 |
| Phase 8 Browser | **6 passed**，13.2s，exit0 |
| Browser production FULL | **56 passed**，1.0m，exit0（旧50 + 新6） |
| Browser development FULL | **58 passed**，1.4m，exit0（旧52 + 新6） |
| Phase 7 Browser | 原7项在两种模式均通过 |
| Frontend lint / build | 重新运行PASS，exit0 |
| Ruff check / format --check | 重新运行PASS；90 files already formatted |
| isolated Alembic CLI | upgrade 0007 → upgrade head → downgrade 0007 → upgrade head → check → current，全部exit0 |
| Real S13 isolated Fake初次流程 | **1 passed**，6.1s，exit0 |
| Real S13新进程重启验证 | **1 passed**，4.8s，exit0 |

后端在原30项上增加3个实际case：明确Provider错误、Regenerate INSERT已执行后的故障、Regenerate commit前故障。均验证无phantom版本、旧Selected恢复、所有旧记录保持，以及解除故障后的同operation Retry只创建V2。既有DB冲突测试真实触发重复版本、多Selected和零版本约束；并发生成测试和Select切换仍通过。

Recovery没有修改旧业务assertion来适配结果；只对获准的Clipboard行尾比较作精确修正，并补充Copy路径和回滚覆盖。全部命令正常结束，无skip/xfail或强制成功退出。既有依赖/构建警告仍保留。

### Populated migration / final schema

最终revision为 **0008_prompt_versioning**；模型/字段/API和业务规则与本文前述保持一致。未修改0007或任何旧迁移，未增加Phase9字段。最终列为既有15列加 `version INTEGER NOT NULL`、`edited_content TEXT NULL`、`is_selected BOOLEAN NOT NULL`，共18列；effective_content为计算属性。

独立CLI验收在生产数据隔离副本的0007 schema中实际INSERT **6条旧生成事实**，分VIDEO_GENERATION / OTHER两组，包含一个已删除历史版本。升级后版本分别1…4与1…2；第一组V3被采用、已删除V4不采用，第二组V2被采用。旧生成文本、上下文和模板快照及全部18张旧表原列逐行保持。实际UPDATE触发重复版本和双Selected的IntegrityError并回滚。

随后downgrade0007只丢弃Phase8列/约束，所有Phase7事实和旧表逐行相等；再upgrade head后结果仍正确。`alembic check` 输出 **No new upgrade operations detected**；`current` 输出 **0008_prompt_versioning (head)**；integrity=ok、FK=0。日志为忽略目录 `.workspace/phase8-recovery/alembic.log`，测试脚本和数据库不提交。

### Production safety / backup / migration

本轮独立建立新baseline，未复用前次结果。全部自动化前后：生产8个文件 + Bootstrap + HANDOFF，**10/10文件集合与SHA-256相同**。此前备份和素材保持；5张被旧浏览器测试重写的受Git管理截图已备存后恢复到本轮开始时字节，最终不夹带无关截图改动。

所有门槛通过后才创建唯一新备份：

```text
D:\AI-Video-Workspace\backups\before-phase8-20260929-231526.db
source SHA-256 = backup SHA-256:
f1ccc50edb6457e2884dae36eb8745eab025c39616df7afab7c626980f582b36
```

只执行生产 **alembic upgrade head**，没有downgrade/reset/drop/recreate或手工SQL修数据。生产最终revision=`0008_prompt_versioning`；18张旧表原有所有列逐行相等；`integrity_check=ok`，`foreign_key_check=0`。

迁移后数据库SHA-256：

```text
6bcbefa34fd56937a7b315a76a4613bb73b64a73197a23d05b9070d7fc1778c5
```

这次DB哈希变化是测试后获准的迁移结果；生产其余文件哈希均保持，新增备份单独记录。源备份校验与升级日志、完整元数据只留忽略审计目录。

### SPF old data / S13 Fake acceptance

生产逐表比对及定向查询确认：SPF项目、S13 风淋、10秒、风淋室、main_action / key_constraints / negative_constraints / free_notes原文、SPF培训女员工、6个活跃CharacterState、S13 → 黄色 PPE + 双层手套全部保持。未添加或改变真实素材绑定。

从升级后的真实库复制到 `.workspace/e2e/phase8-real-s13/workspace`，Bootstrap和AI配置也仅位于隔离目录。复用真实S13 UUID、字段和已有 `SPF 六宫格分镜模板`，只注入Fake Provider。

实际浏览器完成：选真实模板 → 实际上下文含S13/10秒/风淋室/角色状态 → Generate V1 → History → Edit V1 → Save → Refresh → Copy编辑后有效内容 → 仅在隔离副本追加Free Notes → Regenerate V2 → 检查V1所有原始事实不变、V2新UUID/输入hash/Context → Select V1且只有V1采用 → Select V2且只有V2采用 → Refresh → Copy Selected。

结束初次服务PID17268后，第二次启动新服务PID24532；完整history响应与保存证据逐字段相等，V2仍Selected，V2/V1 Copy均正确。浏览器断言仅规范CRLF表示，保留全部业务字符。Prompt区域截图已人工检查，保存在忽略目录 `s13-final.png`，未提交真实业务截图。

整个S13隔离验收前后：包含新备份的生产9文件 + Bootstrap + HANDOFF，**11/11哈希相同**。生产prompt_records仍 **0条**；Fake V1/V2仅存在隔离副本。最终只读复核integrity=ok、FK=0。

**Real external AI manual acceptance: PENDING USER EXPLICIT APPROVAL。未调用真实收费模型。**

### Final files / limitations / Git boundary

Phase8文件清单保持本文“文件与Git”中的20个路径；Recovery进一步修改测试与四份文档，没有业务重写、新依赖或额外待提交产物。提交前检查diff/暂存清单，排除HANDOFF、AI配置、DB/backup、审计/trace/test-results、dist与临时脚本。

HANDOFF用户原有修改保持，审计哈希前后一致。Phase8提交消息为 `feat: add prompt versioning`。提交完成后的目标状态为Phase8-owned working tree clean，仅保留pre-existing `M HANDOFF.md`；最终实际状态和hash以交付报告为准。

已知限制继续保持：API Key独立本机明文；AI等待持有Workspace锁和读事务；跨进程SQLite busy可能使操作失败回滚；外部timeout Retry可能重复计费；无队列/取消/streaming；无多标签编辑冲突处理；历史暂未分页。Windows系统剪贴板行尾表示可能不同，逻辑文本与段落结构保持。

**Phase 8 COMPLETE。Phase 9 NOT STARTED。完成后停止。**
