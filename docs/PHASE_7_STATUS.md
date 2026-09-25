# Phase 7 — AI Prompt Generation / COMPLETE

日期：2026-09-25。基线 HEAD：`14ecab0 feat: add prompt template management`。

当前状态：Recovery / Completion Pass 全部通过，Phase 7 COMPLETE，Phase 8 NOT STARTED。以下先保留首次停工记录，最终状态以末尾 Recovery 验收为准；用户原有 `M HANDOFF.md` 保持不变，排除 Phase 7 提交。

## 首次停工历史：停止原因

完整后端回归在 collection 阶段失败，exit 2：

```text
tests/test_shot_workspace.py:7
from test_characters import asset, post, setup
ModuleNotFoundError: No module named 'test_characters'
```

本轮新增 `backend/tests/__init__.py` 后，tests 成为 package，改变 pytest 导入方式，导致既有裸模块导入失效。这是本轮引入的测试代码回归，不是此前 WinError 5 权限问题。按用户 Failure-stop 规则立即停止；没有修复后继续、修改旧 assertion 或伪造通过。进行中的 production 浏览器全量已中止，退出 1，不计 PASS。

## 已实现但未完成最终验证的范围

- `AIService → AIProvider Protocol → OpenAICompatibleProvider`，具体 `/chat/completions` 请求仅在 Provider。标准库 HTTP，无新依赖；单 user message，非 streaming。
- Provider 限制响应大小、45 秒 socket timeout、拒绝重定向；认证、模型、HTTP、网络、timeout、格式错误映射到统一 Error Schema。Service 二次净化 Provider 异常，不回传 raw response / traceback。
- `AISettingsService → AISettingsStorageProvider → LocalAISettingsStorageProvider`；配置位于 Bootstrap 旁的 `ai-provider.json`，生产预期为 `D:\AI-Video-Workspace-Config\ai-provider.json`。本轮没有在生产创建该文件。
- 配置不在 Workspace / app_settings / 项目数据中；文件原子替换，文件名加入 Git ignore；本地配置内 Key 为明文，未宣称 OS 加密。内存使用 SecretStr；GET/PUT 响应只给 URL / model / configured flag。省略/null Key 保留，空串清除。URL 拒绝凭据、query、fragment；不写普通日志。未来 Project Export 必须保持不读取此独立配置。
- `build_shot_context` 直接调用 `ShotWorkspaceService`，读取 Shot、Scene、角色身份/状态、两类角色资产、Shot 资产与四项需求。角色按身份/状态 UUID、资产按 UUID、Tags 按名称排序；空值为空字符串，不序列化 None/null/undefined 占位。
- 复用 `PLACEHOLDERS` 与 `render_content`；未更改 Phase 6 Sample Preview。`shot_context` 按 Registry 顺序聚合，兼容非空 legacy creative requirement。
- 预览 input_hash 防止模板/上下文变动后提交旧预览；operation_id 作为记录 UUID，同一已完成操作重试返回原记录，不再次调用 Provider。未成功请求不写记录。外部 Provider 是否支持 Idempotency-Key 不保证，因此 timeout 后 Retry 仍可能产生额外费用。
- 已保存结果只读查看与 Copy；没有版本号、History、编辑、selected/final、Storyboard 或 VideoResult 行为。

## Schema

新增 revision 文件 `0007_prompt_generation`，down_revision=`0006_prompt_templates`；未修改旧 migration。

表 `prompt_records`：

```text
id UUID PK（operation_id）
shot_id UUID FK shots.id
template_id UUID FK prompt_templates.id
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
deleted_at nullable timestamp（复用 BaseModel；无删除接口）
```

shot_id / template_id 有索引。模板软删除不删除既有事实；读取记录校验 Shot 及父级可见性。无 version / edited_content / is_selected。

## API 与前端

```text
GET/PUT /api/settings/ai
POST /api/shots/{shot_id}/prompts/preview {template_id}
POST /api/shots/{shot_id}/prompts/generate {template_id, input_hash, operation_id}
GET /api/shots/{shot_id}/prompts/latest
GET /api/prompts/{identifier}
```

Settings 新增 URL / Model / 密码输入框、保留/清除 Key。Shot Workspace 在需求/资产之后显示 Prompt panel，复用 Template Picker，新增实际输入、Context 查看、Generate / Generating / Error / Retry、最新持久化结果及 Copy。未保存要求阻止预览和生成；结果普通文本显示。主题/图标沿用原系统。

## 测试事实

| 项目 | 实际结果 |
| --- | --- |
| 新增 Backend | 共 50 项；最初 47 项单独执行 PASS，后来新增 3 项未完成执行 |
| Backend FULL | collection ERROR，未得到 251/251 结果 |
| 新增 Browser | 7/7 PASS，正常 exit 0 |
| Browser production FULL | 50 项运行中按停止规则中止，非 PASS |
| Browser development FULL | 未执行 |
| Frontend lint / build | PASS |
| Ruff check | PASS（包含最终新增测试） |
| Ruff format | 早期 --check PASS，后续新增内容已运行 formatter；未完成最后整套复核 |
| isolated Alembic CLI | upgrade head → downgrade base → upgrade head → check → current PASS；head=0007 |
| 有数据 PromptRecord downgrade 测试 | 已写，因 full collection 失败未执行 |

新增测试初次执行时，大响应参数生成超长 pytest case name，引起 Windows 环境变量超过 32767 字符。仅添加短 case IDs 后原 47 项通过；输入和断言未改。这与最终旧测试 import 回归是两个不同问题。

测试 Provider 位于 tests；单独 E2E app 在创建应用前确认 Bootstrap/Workspace 均在 `.workspace/e2e`。`start_e2e.py` 复用启动器并注入测试 app；生产启动器默认仍 `app.main:app`。没有真实模型请求。

旧浏览器测试写入的 5 张 docs/screenshots PNG 已备存到忽略目录并恢复到本轮初始版本，未将其作为 Phase 7 修改保留。

## Production safety / migration / S13

- 自动化前成功取得生产 7 个文件 SHA-256，停止收尾后文件集合与全部哈希一致；Bootstrap 配置、HANDOFF.md 哈希也一致。
- 生产 DB SHA-256：`BA3A55AD8EA6E3881CD3B40261C0923E614902E01527FAEA33BC66851525F44C`，revision 仍 `0006_prompt_templates`。
- 未执行 Phase 7 生产 backup / upgrade；不能报告新 schema 已进入生产。
- SPF integrity=ok、foreign_key_check=0；旧业务表与 Phase 6 迁移前备份逐行一致。S13 风淋 / 10s / 风淋室、四项需求、SPF培训女员工 → 黄色 PPE + 双层手套完整，6 个状态保留。
- 真实 Shot / Character / State 资产为 0，未增加任何资产。
- 仅隔离构造的 S13 fixture 完成 Fake Generate → persistence → refresh → Copy（Dark/Light、1024/1280）。真实 SPF S13 的 Fake 验收尚未执行。
- 真实外部 AI 手工调用未执行，仍等待用户明确允许。

## 本轮文件

新增：

```text
backend/app/api/routes/prompts.py
backend/app/migrations/versions/0007_prompt_generation.py
backend/app/models/prompts.py
backend/app/repositories/prompts.py
backend/app/schemas/ai.py
backend/app/services/ai/{__init__,context,provider,service,settings}.py
backend/tests/{__init__,e2e_app,fake_ai,test_ai}.py
frontend/src/features/prompts/{api.ts,prompt-panel.tsx,prompts.css}
frontend/src/features/settings/ai-settings.tsx
frontend/tests/prompts.spec.ts
scripts/start_e2e.py
docs/PHASE_7_STATUS.md
```

修改：`.gitignore`、backend/app/main.py、backend/app/models/__init__.py、backend/tests/test_bootstrap.py、backend/tests/test_database.py、frontend/playwright.config.ts、frontend/src/api/client.ts、frontend/src/features/settings/settings-page.tsx、frontend/src/features/shots/shot-workspace.tsx、frontend/src/features/templates/template-picker.tsx、scripts/start.py、README.md、DEVELOPMENT_STATUS.md、PROJECT_PLAN.md。

两处既有 schema 测试仅新增准确的 prompt_records 表与新 head，保留完整集合断言。没有把 HANDOFF.md、真实数据、配置、审计文件、临时 DB 或 build/test artifacts 纳入提交。

## 后续门槛与已知限制

必须先明确获准恢复后处理测试导入回归，再运行完整回归、有数据迁移测试与生产哈希复核；所有条件满足才允许备份和只 upgrade 生产。当前代码未提交，Phase 7-owned changes 不 clean。

现有 Workspace session 在请求期间持有锁，AI 等待会串行阻塞同实例的 DB 操作；未引入后台任务系统。配置为用户本地明文文件，依赖目录访问权限；未修改 ACL。无 streaming、取消、跨刷新操作状态恢复或远端绝对幂等保证。

**Phase 7 NOT COMPLETE / STOPPED。Phase 8 NOT STARTED。**

## Recovery / Completion Pass — 2026-09-25

### Import regression fix

新增 tests 包标记让 pytest 使用 `tests.test_characters` 模块名，旧测试的 `from test_characters import ...` 因而失败。已移除非必需 `backend/tests/__init__.py`，没有修改旧裸导入、PYTHONPATH、assertion 或 production code 来规避问题。

共享 Fake 与 guarded E2E entry 移至独立 `backend/test_support/{__init__,fake_ai,e2e_app}.py`。`test_ai.py` 和 `start_e2e.py` 使用该包，原有 tests 目录保持非 package。完整收集恢复；首次全量 251/251 PASS，新增事务回滚验证后最终 253/253 PASS。

此前文件列表中的 `backend/tests/{__init__,fake_ai,e2e_app}.py` 不属于最终文件；以 `backend/test_support` 三文件替代，其余实现、范围、schema / API 保持上述定义。

### Final regression

| 项目 | 最终实际输出 / 结果 |
| --- | --- |
| Backend FULL | **253 passed**, 68.84s，exit 0；原有 201 + Phase 7 52 |
| Phase 7 Backend | JUnit 核对 `test_ai` **52/52 PASS**，无 skip |
| Phase 7 Browser | **7 passed**, 18.0s，exit 0 |
| Browser production FULL | **50 passed**, 1.0m，exit 0（原 43 + 7） |
| Browser development FULL | **52 passed**, 1.4m，exit 0（原 45 + 7） |
| Frontend lint / build | PASS，exit 0 |
| Ruff check / format --check | PASS；`backend scripts` 共 88 个格式文件 |
| isolated Alembic | upgrade 0006 → upgrade head → downgrade 0006 → upgrade head → check → current 全部 exit 0；head=0007 |

最终 CLI 验证 0006 无 prompt_records，0007 有全部 15 列、2 外键和 3 索引（含主键）；无待生成操作。完整 backend 还覆盖 downgrade base 的既有迁移回归。所有 downgrade 只作用于隔离 DB。

上一轮后补的三项，已在本次完整回归与 JUnit 中逐项确认：

| Test | Purpose | Result |
| --- | --- | --- |
| `test_key_in_unused_context_never_enters_generation_record` | 未被模板引用的 context 字段包含当前 Key 时也阻止生成 / 持久化 | PASS |
| `test_actual_preview_reuses_validation_even_for_corrupt_stored_template` | 存储模板被损坏时仍走唯一 Phase 6 placeholder 校验 | PASS |
| `test_populated_generation_downgrade_preserves_all_old_tables` | 含成功事实的隔离库 0007 → 0006 → 0007，全部旧表逐行不变 | PASS |

新增 `test_database_write_failure_rolls_back_generation_fact[after-insert]` 与 `[before-commit]` 均 PASS。通过 SQLAlchemy 事件在真实 INSERT 已执行后、事务 commit 前注入故障；没有 mock Repository 或跳过 SQL。新的连接确认 0 条记录；解除故障后相同操作重试只保存 1 条。已有 Provider error / timeout / empty / malformed response 用例也验证无记录，正常 Retry 可成功。

### Architecture / security recheck

Route 只委托 AIService / AISettingsService；AIService 只调用 AIProvider Protocol，厂商 HTTP 逻辑集中于 OpenAICompatibleProvider。数据库经 Repository，AI 私密配置经独立 StorageProvider。没有第二套 renderer / placeholder 语义；未引入 Phase 8 字段和行为。

GET / PUT 均采用仅含 URL / Model / configured flag 的 response schema；验证错误只返回字段名；Provider 异常二次净化，无原始响应 / traceback。日志检查、Fake secret 测试与 Git 内容检查通过。生产未创建 `ai-provider.json`；测试凭据明确为 synthetic，只在隔离配置中使用。未来导出功能不在本阶段，独立配置不属于项目存储。

AI 请求继续持有原有 Workspace 串行锁与 SQLAlchemy 请求级读取事务。Provider 调用前没有 PromptRecord INSERT，网络完成并校验成功后才 flush / commit；失败由既有 session context rollback。此次没有为此重构并发框架。慢请求会阻塞同实例 DB 操作，读取事务也可能阻塞其他 SQLite writer，属于明确的并发 / 性能限制；现有失败与回滚测试未见数据损坏。

### Production safety / migration

自动化开始前成功记录生产 7 个文件；全部自动化正常退出后再次逐文件计算，**7/7 before == after**。5 张既有 Browser 截图产物备存至忽略目录并恢复为开始时的 HEAD 字节，未加入提交。

全部验证通过后才创建备份：

```text
D:\AI-Video-Workspace\backups\before-phase7-20260925-154932.db
SHA-256 source = backup:
ba3a55ad8ea6e3881cd3b40261c0923e614902e01527faea33bc66851525f44c
```

真实库只执行 `alembic upgrade head`，revision=`0007_prompt_generation`。17 张旧业务表逐行相等；`integrity_check=ok`，`foreign_key_check=0`。prompt_records 新建且 0 行，15 列 / 2 外键正确。

关键数据：SPF / S13 风淋 / 10s / 风淋室、四项 requirements、SPF培训女员工、6 个 CharacterState、S13 → 黄色 PPE + 双层手套均完整。未删除 TEMP_WORKSPACE_VERIFY，未操作 ACL 或 C 盘 fallback Workspace，旧备份未改。

迁移后 DB SHA-256：`f1ccc50edb6457e2884dae36eb8745eab025c39616df7afab7c626980f582b36`。生产备份和 revision 升级是自动化哈希比对完成后的授权写入，不能与测试污染混为一谈。

### Real S13 / Fake acceptance

采用生产升级后真实 SPF 数据的隔离副本，保留真实 UUID、requirements、Scene、角色 / State 与现有 `SPF 六宫格分镜模板`。Agent 实际驱动浏览器并检查截图，完成选择模板 → actual rendered input → Fake Generate → result → SQLite persistence → 页面刷新 → Copy / 读取剪贴板比对，**PASS**。

输入包含 S13 / 风淋 / duration_seconds=10 / 风淋室 / 全部四项 requirements / SPF培训女员工 / 黄色 PPE + 双层手套；Shot / Character / State 的素材绑定均 0，reference_assets_context 为空，未添加任何假素材。完整上下文仍从真实复制数据的 Service / Repository 聚合，不使用 SAMPLE_CONTEXT。

Fake 结果明确含 FAKE，provider=`fake-test-provider`，model=`fake-acceptance-model`。生成事实仅留在隔离副本；生产 prompt_records 仍 0 行。验收前后生产 **8/8 文件 SHA-256 相等**（包含新备份）。原 HANDOFF.md SHA-256 前后均为 `C42D15FF745EA67B90D10A1BE80E652151DEED57E805259698F424963B763A25`。

**Real external AI manual acceptance: PENDING USER EXPLICIT APPROVAL。未调用真实收费 API。**

### Known limitations / Phase 8 boundary

- Key 本机明文保存、无 OS keychain / encryption dependency；依赖本地目录访问权限。
- 网络等待期间持有原有 Workspace 锁和读取事务；45 秒为 socket timeout，非总墙钟 deadline。没有后台队列、取消或 streaming。
- 外部 Provider 不保证 Idempotency-Key；timeout 后重试可能再次计费。本地已完成 operation UUID 则返回原事实。页面刷新不恢复未完成 operation ID。
- 构建存在既有依赖注释 / 大 bundle 警告；Backend 有 TestClient 依赖弃用警告，均未导致失败或被隐藏。
- UI 只展示最新成功事实与其输入，不提供历史 / 版本 / 编辑 / selected / final / Storyboard / Video Result。

本轮不新增依赖、不更改旧 migration。验收证据 / 临时 DB / S13 数据 / 截图 / AI 配置均在 Git 忽略范围，HANDOFF.md 排除提交。

**Phase 7 COMPLETE。Phase 8 NOT STARTED。**
