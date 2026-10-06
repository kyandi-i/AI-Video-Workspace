# Phase 11 Audit Result

日期：2026-10-04  
范围：只读审计与 Scope Freeze；本轮未实现 Phase 11 功能、未创建 migration、未修改 Production。

## 1. Repository Baseline

- HEAD：`013ae712ddff1058acd259c5353949f1db06bd27` (`feat: add video result workflow`)
- Baseline Working Tree：仅 `M HANDOFF.md`。该文件是用户自己的交接文档，本轮未编辑、恢复、暂存或提交。审计报告完成后新增的预期文档变更为 `README.md`、`DEVELOPMENT_STATUS.md` 与本文件；没有其他代码/截图变更。
- Production Workspace：`D:\AI-Video-Workspace`
- Bootstrap：`D:\AI-Video-Workspace-Config\config.json`
- Production DB：`D:\AI-Video-Workspace\data\workspace.db`
- Production Revision：`0010_video_results`
- Integrity：`integrity_check = ok`
- Foreign Keys：`foreign_key_check = 0`
- Production 当前业务计数与 Phase 10 记录一致：2 Projects、1 Script、3 Scenes、4 Shots、1 Asset、1 Character、6 CharacterStates、2 PromptTemplates、1 ShotCharacterStateLink；PromptRecord / Storyboard / VideoResult 均为 0。

Phase 10 的正式生产后基线 DB SHA-256 为 `d0226a65c89bccaeada79e678ede430c67e93ce988ca53db06c230e8da3e1f49`；本轮只读复核得到相同值。当前 Asset、thumbnail、Bootstrap Config 与 HANDOFF 也与既有记录相符。

## 2. Recovered Runtime Facts

冻结依赖与运行时：

- Node `v24.13.0`，npm `11.6.2`，uv `0.9.11`，Python `3.12.11`。
- FastAPI `0.141.1`、SQLAlchemy `2.0.54`、Alembic `1.20.0`、Pydantic `2.13.5`、Pillow `12.3.0`、PyAV `18.1.0`。
- 后端依赖由 `backend/pyproject.toml` / `backend/uv.lock` 冻结；前端由 `frontend/package.json` / `frontend/package-lock.json` 冻结；本轮未升级依赖。

启动命令：

```powershell
uv run --locked --project backend python scripts/start.py
uv run --locked --project backend python scripts/start.py --dev
```

验证命令与结果：

- `uv run --locked --project backend pytest backend/tests`：342 passed，exit 0。
- `uv run --locked --project backend ruff check backend scripts`：PASS。
- `uv run --locked --project backend ruff format --check backend scripts`：PASS，106 files formatted。
- `npm --prefix frontend run lint`：PASS。
- `npm --prefix frontend run build`：PASS；保留既有 Rollup chunk-size / annotation warning。
- Production Browser：本轮 67 个断言均显示 passed，但 Playwright 在 Windows web-server 清理阶段未返回退出码，随后安全中止；因此本轮不把它声明为 exit 0。Phase 10 已记录同一套 production 67/67、development 69/69 且 exit 0 的正式证据。
- 自动化使用 `frontend/playwright.config.ts` 的隔离 Workspace / Bootstrap；本轮浏览器测试曾重写 5 张跟踪截图，已用 Phase 10 审计前副本恢复，最终没有遗留截图或代码测试副作用。

现有启动、测试、Alembic 与依赖边界见 [README.md](../README.md)、[Phase 10 状态](PHASE_10_STATUS.md)。

## 3. Current Delete / Restore Matrix

| Entity | Soft Delete | Restore API | Restore UI | In-use Protection | Permanent Delete |
| --- | --- | --- | --- | --- | --- |
| Project | Yes；级联 Script / ScriptNode / Scene / Shot / Character / State | Yes | No | Parent cascade；无永久删除 | No |
| Script | Yes；级联其节点、Scene、Shot | Yes | No | Parent relation；无永久删除 | No |
| ScriptNode | Yes；内部随 Script / Scene 级联 | 间接由 Script / Scene restore | No | 内部结构节点 | No |
| Scene | Yes；级联 ScriptNode / Shot | Yes | No | Parent cascade；无永久删除 | No |
| Shot | Yes；解除角色状态使用关系、保持其他历史引用 | Yes | No | 删除本身不要求解除 Asset / Prompt / Result 引用 | No |
| Asset | Yes；保留原文件、thumbnail、标签/关系历史 | Yes | No | Yes：Project、Shot、Character、CharacterState、Storyboard、VideoResult | No |
| Tag | BaseModel 有 `deleted_at`；当前无独立删除流程 | No public API | No | 仅在 AssetTag 关系层处理 | No |
| Character | Yes；级联 State、解除关系但不删 Asset | Yes | Yes；显示已删除 / 恢复 | 删除时级联，不阻止 | No |
| CharacterState | Yes；解除 Shot / Asset links | Yes | Yes；角色详情显示已删除 / 恢复 | Yes；被 Shot 使用时拒绝删除 | No |
| PromptTemplate | Yes | Yes | Yes；模板页显示已删除 / 恢复 | 无；PromptRecord 保留生成快照 | No |
| PromptRecord | Repository 支持 soft delete；当前无 public delete route | No public API | No | 生成事实/来源关系由 ID 保持 | No |
| Storyboard | Yes；保留 ProjectAssetLink / ShotAssetLink / Asset / 文件 | Yes | No；当前 UI 可删除但不能显示已删除并恢复 | 删除允许，VideoResult 来源可读为 deleted；Asset 删除会保护它 | No |
| VideoResult | Yes；不删 Asset、文件或 links | Yes | Yes；History 有 Show deleted / Restore | Asset 删除会保护 active VideoResult | No |

关系表的解绑/级联删除也使用 `deleted_at`，但没有统一的独立 Recycle Bin 或逐条 restore UI；重新绑定会复用并恢复已有 link。没有任何永久删除 route、service 或 UI。

## 4. Existing Export Infrastructure

目前已有：

- `WorkspaceService` 只负责预创建 `exports/`、`backups/` 目录，并暴露路径；没有导出业务。
- `StorageProvider` / `LocalStorageProvider` 已提供受控相对路径校验、流式读写、文件存在性、临时文件与失败补偿，可复用为导出读取层。
- Asset 文件当前通过 `GET /api/assets/{id}/file` 与 thumbnail endpoint 单文件返回；没有 ZIP、manifest 或 Project Export route。
- 所有 Repository 默认忽略软删除记录，查询可显式 `include_deleted=true`；这可以复用于 Export / Recycle Bin，但不能直接等价为最终导出策略。
- AI Provider 配置写在 Bootstrap Config 同级的 `ai-provider.json`，API Key 不从公共 API 回显，也不属于 Workspace DB。

缺失：

- `ExportService` / export Repository 查询编排 / ZIP writer / manifest schema。
- Project Export API、Project 页面入口、下载响应与 `exports/` 生命周期清理。
- Recycle Bin 聚合查询、筛选、统一恢复页面。
- Permanent Delete、引用图保护、文件/thumbnail 清理与失败补偿。

## 5. Phase 11 — IN

以下是可实际开发和验收的建议范围；其中带“需确认”的项目在用户决定前不进入实现：

1. **Project Export**：从单个 Project 导出可携带 ZIP；只收集该 Project 图谱及其实际引用内容，不导出整个 Workspace。
2. **未来可恢复的 Export contract**：保留 UUID、关系 ID、版本号、Selected 状态、Prompt snapshot、Storyboard / VideoResult provenance 与相对文件路径；本 Phase 不实现 Import。
3. **Recycle Bin 收尾**：复用现有 soft-delete / restore service，补齐统一聚合视图或现有恢复入口的 UX；统一页面的 entity 范围需用户确认。
4. **UX Finalization**：只收尾现有页面的 empty/loading/error、删除确认、恢复入口、长内容、1024/1280、Dark/Light、可访问名称、键盘焦点和 dialog/sheet 行为；不重新设计应用。
5. **Export / Recycle Bin 的隔离测试、artifact 校验和安全边界测试**。
6. **Migration 判断**：先按现有字段和关系实现；若用户确认的范围不新增持久化字段，则不创建 0011。

## 6. Phase 11 — OUT

- Project Import / full restore implementation；本 Phase 只要求 Export 对未来 Import 可恢复。
- Workspace clone、Cloud Sync、Multi-user、Auth、Permissions、SaaS。
- Desktop app、Video editor、Image/Video generation API、GenerationJob、队列、Approval workflow、Plugin marketplace。
- 全局删除系统重写、owner/source 字段、新的 Asset ownership 模型。
- 未经用户明确确认的 Permanent Delete / cascade purge。
- 导出 API Key、`ai-provider.json`、Bootstrap Config、真实 Workspace DB / backup DB、machine-specific absolute paths。
- 大规模视觉重设计、新 design system、新 icon library、marketing dashboard、animation framework。

## 7. Project Export Scope

### 包含的 entities

Project graph 应包含：

- Project、Script、ScriptNode、Scene、Shot。
- Project 实际引用的 Asset metadata。
- ProjectAssetLinks、ShotAssetLinks。
- Character、CharacterState、CharacterAssetLinks、CharacterStateAssetLinks、ShotCharacterStateLinks。
- Project 相关 Tags / AssetTags，以及被导出 Asset 实际使用的 Tag entity。
- PromptRecords；每条记录保留 generated / edited / effective content、template snapshot、context_json、rendered_input、provider/model、version、Selected 与 provenance ID。
- Project PromptTemplates，以及被 Project 的 PromptRecord 实际引用的 Global PromptTemplate 是否作为 entity 额外导出——**待用户确认**。
- Storyboard metadata 与 VideoResult metadata；二者引用的 Asset metadata 通过同一 Asset 记录表达。
- notes、metadata、created_at、updated_at、deleted_at（是否收录 deleted 记录待用户确认）。

### 只导出 Project 引用内容

默认边界是 Project Export，不是 Workspace clone。共享 Asset 若被当前 Project 合法引用，在 ZIP 内复制一份；不改变 Workspace 内统一 Asset ownership，也不因导出而创建新 Workspace Asset。

### physical files

- 所有被 Project graph、Storyboard 或 VideoResult 实际引用的 Asset original file 必须包含；同一 Asset 只复制一次。
- thumbnail 属于派生文件，可由 Import 重新生成；若实现阶段决定附带，必须作为明确的 derived file 列出，不能隐式依赖。
- Asset 的原始 filename 只作为 metadata 保存；ZIP 内部路径不得直接采用用户文件名。

### soft-deleted 是否包含

**UNRESOLVED — 用户决定。** 规格要求“当前项目实际引用的本地文件”，但没有规定 Export 默认 active-only 还是包含 `deleted_at != NULL` 的历史对象。两种选择都会影响 future restore、Selected 语义和是否导出已删除媒体，不能静默拍板。

### Global template 处理

PromptRecord 已保存 template name/content snapshot，因此恢复 Prompt 内容不依赖实时 Global entity。是否额外打包被引用的 Global PromptTemplate entity，应采用“只打包实际引用的 Global entity”还是“只保留 snapshot”，**待用户决定**；不得把全部 Global templates 打入每个 Project。

### 明确排除

API Key、`ai-provider.json`、Bootstrap Config、真实 Workspace DB、backup DB、`D:\...` 等绝对路径、进程信息、操作系统用户名均不进入 ZIP。导出 metadata 中只保留 portable relative asset path。

## 8. Proposed ZIP Contract

以下作为实现前的 v1 提案，满足规格的最小目录并保留未来 Import 所需事实：

```text
<safe-project-name>.zip
├── project.json
├── assets/
│   └── <asset-uuid>/original.<safe-extension>
├── prompts/
│   ├── templates.json
│   └── records.json
└── metadata/
    ├── entities.json
    ├── relations.json
    └── files.json
```

`project.json` 应至少包含：

```json
{
  "format_version": 1,
  "exported_at": "UTC ISO-8601",
  "project_id": "UUID",
  "project_name": "display name",
  "application_version": "0.1.0",
  "schema_revision": "0010_video_results",
  "soft_delete_policy": "explicitly recorded",
  "entities": {"...": "..."},
  "files": [{"asset_id": "UUID", "zip_path": "assets/...", "sha256": "..."}]
}
```

Contract rules：

- UUID 原样保留；relations 使用 UUID，不用名称猜关系。
- ZIP internal paths 使用固定 ASCII-safe UUID 目录与受限 extension；禁止 `..`、绝对路径、重复归一化路径、用户原始 filename 作为目录成员。
- `files.json` 记录 asset UUID、portable ZIP path、原始 filename、mime、size、checksum；导出时流式复制，不把大媒体读为 base64。
- `records.json` 保留 Prompt snapshot、Prompt version、Storyboard / VideoResult provenance、notes、Selected 与版本信息。
- 每一个 ZIP entry 必须在临时导出目录内构造并校验；失败时删除临时 ZIP，不能留下半成品并伪装为成功。
- `format_version` 是必需字段；未来 Import 必须拒绝未知 major version，而不是猜测字段。

该 contract 本轮只冻结为实现提案，不写 ZIP、不创建 endpoint。

## 9. Future Restore Compatibility

- UUID：所有导出 entity 与 link 保持原 UUID，避免依赖名称或导出顺序。
- Relations：显式保存所有 relation rows，包含 Project/Shot/Character/State/Prompt/Storyboard/VideoResult 的 FK。
- Provenance：保留 `PromptRecord.template_id` 与 snapshot；Storyboard `source_prompt_record_id`；VideoResult 两条 nullable provenance。
- Version：保留 Prompt / Storyboard / VideoResult 的 per-Shot version，不重编号、不复用。
- Selected：保存每类 active Selected；若导出包含软删除记录，同时保存 deleted 状态并禁止把 deleted record 当作 active Selected。
- Relative paths：只保存 ZIP relative path 与 Asset locator metadata，不保存本机绝对路径；导入时用 UUID 映射并重新生成 thumbnail。
- Shared Asset：ZIP 内只出现一次，关系表引用相同 Asset UUID；导入时由 Import 决定如何映射到目标 Workspace，不把 ZIP 副本误判为新的 Workspace ownership。

## 10. Recycle Bin Scope

当前不是统一 Recycle Bin：Projects / Scripts / Scenes / Shots / Assets 只有 API restore，Characters / States / PromptTemplates / VideoResults 有部分恢复 UI，Storyboard API 有 restore 但 UI 没有恢复入口；PromptRecord / Tag 没有 public restore path。

推荐的可验收方向是 **Option A：统一 Recycle Bin UI**，但以下边界必须先由用户确认：

- 是否覆盖 Project、Script、Scene、Shot、Asset、Character、CharacterState、PromptTemplate、Storyboard、VideoResult 全部公开实体。
- PromptRecord、Tag、关系表是否只作为历史/关系数据，不作为一等 Recycle Bin item。
- 是否支持 entity-type filter、名称/编号搜索、按 deleted_at 排序；默认隐藏 active records。
- Restore 是否继续调用每个 entity 现有 service，保留父级先恢复、级联时间戳、Asset/State 引用保护等语义。
- 是否采用 Option B（只补既有 entity 的恢复 UX）而不做聚合 API。

**Option C：Permanent Delete 当前不纳入默认提案，需单独确认。**

## 11. Permanent Delete Semantics

当前决定：**OUT — USER DECISION REQUIRED**。

规格提到 Permanent Delete，并给出 Asset permanent API 的示例，但现有 PROJECT_PLAN 没有把“所有实体永久清理”定义为 Phase 11 的可验收边界，代码也没有任何实现。若用户确认纳入，必须另行冻结：

- Asset：检查 Project / Shot / Character / CharacterState / Storyboard / VideoResult 及 link 引用；关系、DB 行、原文件、thumbnail 的顺序、事务边界和失败补偿必须明确。
- Project / Script / Scene / Shot：明确子实体、Prompt、Storyboard、VideoResult、Asset links 的 cascade 规则；不得直接 `DELETE FROM`。
- Prompt / Storyboard / VideoResult：处理历史来源、Selected、版本唯一性与被其他记录引用。
- 所有 purge 必须二次明确确认、原子更新关系、清理文件并验证没有 partial state；没有成熟规则前不实现 cascade purge。

## 12. UX Finalization Scope

### IN

- Project / Script / Scene / Shot：补齐被删除记录的可发现性与恢复入口，或在统一 Recycle Bin 中提供恢复；保留现有父级先恢复语义。
- Asset Library / Asset Detail：补齐已删除 Asset 的筛选、恢复入口、缺失文件/引用保护错误态；保留当前解除引用而非删除文件的语义。
- Character / CharacterState：保留当前已删除筛选与恢复；核对长名称、错误态、焦点回归。
- Prompt Templates：保留当前 Show deleted / Restore；核对 Global / Project 空态、冲突错误和 dialog focus。
- Storyboard：补齐 Show deleted / Restore 或统一 Recycle Bin 入口；删除仍只软删除版本，不回收 Asset/file/link。
- Video Results：保留当前 Show deleted / Restore；核对 deleted source、empty history、播放失败和恢复不 Selected。
- Shared empty/loading/error surfaces：覆盖 Project、Asset Library、Shot Workspace、Storyboard、Video Results 的空、加载、网络错误、Retry。
- 1024px / 1280px、Dark / Light、长标题/长 notes、表格横向滚动、dialog/sheet focus、accessible names 与 keyboard navigation。

### OUT

全应用视觉重设计、全新设计系统、图标库、营销 Dashboard、动画框架、页面信息架构重做。

## 13. Migration Decision

**NO MIGRATION REQUIRED（当前提案）**。

理由：现有 `0010_video_results` 已提供所有实体的 UUID、timestamps、`deleted_at`、关系表、Prompt snapshot、Storyboard / VideoResult provenance、版本与 Selected 字段。Project Export、只读 Recycle Bin 聚合和复用现有 restore API 不需要改数据模型。

只有在用户确认的长期设计引入 export history、purge audit log、恢复批次/删除原因等新持久化事实时，才重新评估 `0011_<name>`；本轮不创建 migration。

## 14. API Plan

### Export

建议：`POST /api/projects/{project_id}/export`。

原因：导出会建立临时/持久 ZIP artifact、执行文件复制并可能失败，属于有副作用的命令；响应使用 `application/zip` 与安全 `Content-Disposition`，不返回机器绝对路径。可以在 `exports/` 使用临时文件后原子发布，但本轮不实现。

### Recycle Bin

若用户选择 Option A：`GET /api/recycle-bin?entity_type=&search=&limit=&offset=` 作为只读聚合；restore 继续复用现有 `/restore` endpoint 与各自 service，不复制一套删除语义。若选择 Option B，则不新增聚合 domain，只补现有页面。

### Permanent Delete

当前不提供 endpoint；待用户明确纳入及引用/文件语义后再设计。

## 15. Test Plan

### Backend / Export

- ZIP 创建成功，`Content-Type`、`Content-Disposition` 与安全文件名正确。
- `project.json` manifest 可解析，`format_version` / schema revision / project UUID 正确。
- ZIP 只含目标 Project graph；Workspace 中无关 Project、Global templates（未被引用时）、无关 Asset 不出现。
- 所有 entity UUID 与 relation rows 可重建；ProjectAssetLink、ShotAssetLink、Character/State links、Prompt/Storyboard/Video provenance 均存在。
- PromptRecord 的 generated、edited、snapshot、context、rendered input、version、Selected 与 notes 保留。
- Storyboard / VideoResult metadata 与各自 Asset physical file 均存在；共享 Asset 在 ZIP 内只出现一次。
- UTF-8 中文名称、notes、metadata 正确；原始危险 filename 不形成 ZIP path。
- soft-deleted 行按最终用户决定的 policy 验证；active-only 时 deleted 对象及文件不泄露。
- missing media、broken DB reference、duplicate/collision、partial failure、temp cleanup、磁盘错误均返回可读错误且不留下成功假象。
- API Key、`ai-provider.json`、Bootstrap、SQLite DB、backup DB、绝对路径不出现。
- ZIP traversal、绝对路径、反斜杠绕过、重复 normalized path、symlink/reparse point 与大媒体安全性测试。
- 大媒体用 stream/file copy，不转 base64、不一次性载入内存。

### Recycle Bin

- soft-deleted item 出现，active item 默认不出现。
- entity-type filter / search / ordering 按最终范围工作。
- restore 调用现有 service；父级先恢复、Asset in-use、State in-use、Storyboard/VideoResult 不自动 Selected 等语义不回归。
- 当前不同 entity 的删除与恢复后代规则保持；关系表不被错误物理删除。
- Permanent Delete 只有用户批准后才测试：二次确认、引用保护、transaction、文件清理、failure compensation。

### Browser / UX

- Dark / Light；1024 / 1280；长标题、长 notes、无数据、加载、错误、Retry。
- Project / Asset / Character / Template / Storyboard / VideoResult 的删除确认和恢复焦点回归。
- Dialog / Sheet focus trap、关闭后焦点归还、键盘导航、accessible names、无水平溢出。
- Recycle Bin filter/search、恢复成功后列表刷新与错误保留。

### Production safety

- 自动化前后记录 Production、Bootstrap、HANDOFF、真实 Asset、thumbnail 与 backups 的 SHA-256；测试只用隔离 Bootstrap / Workspace / DB / storage / exports。
- 禁止向 `D:\AI-Video-Workspace\exports` 写测试 ZIP；禁止 migration upgrade/downgrade、INSERT/UPDATE/DELETE 生产业务数据。
- 任意 production hash、真实 asset、secret、路径泄露、migration 或已有回归异常即 failure-stop。

## 16. Security / Data Risks

- ZIP traversal：用户 filename 不能直接成为 archive path；只允许 deterministic UUID path 与受限 extension。
- Secret leak：禁止导出 API Key、AI provider private config、Bootstrap 内容。
- Absolute path leak：DB 的 `storage/...` locator 转成 ZIP relative path；不把 `D:\...` 写入 manifest。
- Missing files：DB metadata 与 physical file 必须在创建成功前完整核对；缺失时失败并清理临时 ZIP。
- Partial export：先写 temp，再校验 manifest、entries、size、checksum，最后原子发布。
- Large media：流式复制、大小上限/剩余磁盘检查、避免内存膨胀。
- Destructive delete：本阶段不实现 Permanent Delete；未来必须先做引用图、事务、文件补偿与二次确认。
- Shared Asset：导出副本不改变 Workspace ownership；同一 Asset 需去重且关系引用保持一致。

## 17. Unresolved Questions

1. **Soft-deleted export policy**：Project Export 默认 active-only，还是连同当前 Project 关联的 soft-deleted records / historical media 一起导出？
2. **Recycle Bin level**：选择 Option A 统一聚合 UI，Option B 仅补现有 entity restore UX，还是 Option C 同时加入 Permanent Delete？本报告推荐 A，但不替用户冻结。
3. **Recycle Bin entity boundary**：PromptRecord、Tag、关系表是否排除在一等回收站 item 之外，只作为历史/关系数据？
4. **Global PromptTemplate export**：只导出 PromptRecord 中已有的 template snapshot，还是对实际被引用的 Global PromptTemplate entity 也导出一份；明确不导出全部 Global templates。
5. **Permanent Delete**：是否纳入 Phase 11；若纳入，必须先批准各实体引用保护、cascade、文件清理与失败补偿语义。

## 18. Decision

**STOPPED — USER DECISION REQUIRED**

原因：上述决定会改变 Export 的长期可恢复性边界与 Recycle Bin / destructive scope。按照规格与交接规则，本轮不自行实现、不创建 `0011`、不修改 Production；等待用户明确决定后，才能开始 Phase 11 implementation。
