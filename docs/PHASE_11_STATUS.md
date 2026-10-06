# Phase 11 — Export / Recycle Bin

日期：2026-10-06。状态：COMPLETE。提交主题：`feat: add project export and recycle bin`。

## 冻结范围与边界

Project Export、统一Recycle Bin与既有Restore；不增加Project Import、Permanent Delete、Hard Delete、Purge或Empty Trash。无schema变更、无0011 migration、无依赖升级。维持Local-first、SQLite、UUID、Managed Storage及Route → Service → Repository / StorageProvider。真实图片/视频生成API不在范围内。

`PHASE_11_SCOPE_FREEZE.md`原样保留为2026-10-04历史审计。其待决提案已被用户后续冻结指令及本报告取代，不应解读为当前未开始。

## Project Export contract v1

`POST /api/projects/{project_id}/export`。目标必须为活跃项目。成功返回`application/zip`、RFC5987安全文件名、`Cache-Control: no-store`及`nosniff`。UI先Export Project，生成后Download ZIP；失败显示可读API消息。

| ZIP条目 | 内容 |
| --- | --- |
| `manifest.json` | format_version=1、exported_at、project_id/name、application_version=0.1.0、source_schema_revision、active_only、snapshots_only、regenerate_on_import |
| `project.json` | 唯一目标Project |
| `metadata/entities.json` | Script、ScriptNode、Scene、Shot、Character、CharacterState、Asset、Tag、Storyboard、VideoResult |
| `metadata/relations.json` | Project/Shot/Character/State资产绑定、ShotCharacterStateLink、AssetTag |
| `prompts/templates.json` | 活跃的目标PROJECT模板实体 |
| `prompts/records.json` | 活跃PromptRecord的生成事实、快照、编辑内容、版本、Selected和来源 |
| `assets/<Asset UUID>/original` | 实际托管原文件，无扩展名；类型由metadata提供 |

仅包含活跃且属于目标项目可达graph的记录；删除子树与已删除实体及其无效绑定被排除。跨项目共享Asset只收集本项目引用，按Asset UUID打包一次；不是按内容hash跨UUID合并。保留当前schema中各实体notes等业务字段，不虚构独立Note表。

GLOBAL模板实体不进入ZIP，PromptRecord.template_name/template_content/context_json/rendered_input等历史事实保留。Prompt / Storyboard / VideoResult额外带`source_references`：原始UUID、entity_type和`included`或`external_identity`。当历史来源实体因GLOBAL或删除策略不打包时，archive-local FK置null，原始身份存于source_references；不修改数据库，不制造悬空archive FK。已包含来源保留原FK。VideoResult的Storyboard来源与Prompt来源独立保存。

序列化保留业务UUID、版本、Selected、时间戳与字段值；Asset的storage_path/thumbnail_path不输出，original_filename去目录部分，另给安全相对media_path。缩略图不打包，manifest声明未来导入时重建。应用设置、AI配置、Bootstrap、数据库、备份均不属于导出graph。

StorageProvider staging负责临时ZIP；ZIP64/ZIP_STORED，1MiB分块读取并验证size/checksum，完整打包成功后才响应。缺失/越界媒体、校验不符、I/O错误返回失败并清理暂存文件。响应关闭也释放staging。生产Workspace不永久保存导出文件。

## Recycle Bin / Restore

`GET /api/recycle-bin`支持entity_type、search（名称/上下文）、offset/limit；返回items/total。UI每页100条，显示类型、名称/编号、删除时间和项目/父级上下文。Restore成功使记录从当前回收列表消失并刷新缓存。

| 类型 | entity_type / 既有恢复入口 |
| --- | --- |
| Project | projects |
| Script | scripts |
| Scene | scenes |
| Shot | shots |
| Asset | assets |
| Character | characters |
| CharacterState | character-states |
| PromptTemplate | prompt-templates |
| Storyboard | storyboards |
| VideoResult | video-results |

入口统一为`POST /api/{entity_type}/{id}/restore`，复用既有服务，无新恢复语义。父级/关联记录不可用时继续按原API拒绝，先恢复所需父级；级联与资产引用保护保持。恢复不重新建立已解除的关系，Storyboard/Video恢复不自动Selected。ScriptNode只随原有层级服务间接恢复；PromptRecord、Tag及Link不新增独立回收站恢复能力。

永久删除：OUT。没有Delete Forever、Purge、Empty Trash或hard-delete API。

## 验证证据与历史

| 检查 | 结果 |
| --- | --- |
| Phase11 backend | 20/20 PASS |
| Backend full | 362/362 PASS |
| Phase11 browser | 5/5 PASS |
| Browser production | 72/72 PASS |
| Browser development | 74/74 PASS |
| Frontend lint/build | PASS |
| Ruff check / format --check | PASS，115 files（含2个test-only验收helper） |
| 真实浏览器下载ZIP | 4/4 PASS |
| 导出/安全专项重验 | 9/9 PASS，11 deselected |
| Production-derived + synthetic isolated acceptance | PASS |
| 本轮验收清理 | PASS |
| Production/Bootstrap/HANDOFF哈希 | 13/13一致 |

上述执行均正常exit0，不以断言完成代替进程退出。Backend20/full362沿用2026-10-04 Ruff recovery证据；浏览器和lint/build为后续test-only recovery实际运行。本轮仅扩展test-only helper，按用户授权不重复全量自动化，重新检查Ruff及产品文件hash。

命令：

```powershell
uv run --locked --project backend pytest backend/tests/test_project_tools.py -x -q
uv run --locked --project backend pytest backend/tests -x -q
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend test -- project-tools.spec.ts --max-failures=1 --workers=1
npm --prefix frontend test -- --max-failures=1
$env:AVW_E2E_MODE = 'dev'
npm --prefix frontend test -- --max-failures=1
uv run --locked --project backend ruff check backend scripts
uv run --locked --project backend ruff format --check backend scripts
```

Browser新增5项：Dark/Light × 1024/1280的Export下载与Recycle筛选/恢复/空列表闭环，另有真实缺失媒体错误UX。真实API构建Project/Shot/Prompt/Storyboard/Video，精确可访问名称定位，无`.first()`/`nth(0)`；长名称和水平溢出检查通过。人工查看Dark1024导出、Light1280回收站截图，控制可见。5张旧测试重写截图已从运行前副本恢复。

独立`phase11_artifacts`打开4份实际ZIP，验证完整性、manifest、所有剩余FK、UUID、media size/hash、Prompt/Video双来源、version/Selected、安全相对路径及配置/凭据缺失。9项既有导出测试显式复核快照、GLOBAL排除、active-only、缺失/变更/越界/绝对路径/I/O失败及临时ZIP清理。

停止历史：初始实现遇24处E501后停止；Ruff recovery仅格式化7个文件，AST一致，然后恢复验证。因缺Browser专项暂停后获授权补齐。初次真实副本验收缺引用媒体及三类生成事实，仅PARTIAL，未标记完成。测试helper曾有1处E501输出文本，拆行后通过，不涉及业务变化。此前审计Browser teardown中止不计入本阶段最终PASS证据。

## 生产派生副本补充验收（两类事实明确区分）

### A. Production-derived real-data coverage：PASS

全新复制生产Workspace，复制前后DB hash相等；独立Bootstrap与Workspace显式注入测试进程。使用真实SPF项目`c1e2f332-45b0-44b7-bbf0-201a47d726b1`及真实S13，不新建Fake Project。原有1 Script / 3 ScriptNode / 3 Scene / 4 Shot / 1 Character / 6 State及所有原有数据库记录逐字段保持。

真实Asset `93b715b4-03b4-46f1-81b3-37f518b1ca79`保持IMAGE/image/png与原始metadata。只在副本新增Project/Shot绑定；文件15,787,864 bytes，SHA-256 `30a75b4a170e53a24fba4d37d46d4affaf9594409ae6ad23be58836dab4a88cc`。导出媒体与真实派生源文件逐字节相等，大小/hash一致，不改为Storyboard或VIDEO类型。

### B. Production-copy synthetic augmentation：PASS

仅副本内通过正式API + FakeAIProvider创建明确`acceptance / test-only`数据：GLOBAL Storyboard模板及其Prompt V1、PROJECT Video模板及其Prompt V1；测试PNG导入为STORYBOARD_6GRID并生成Storyboard V1；测试MP4导入为VIDEO并生成VideoResult V1。VideoResult指向Storyboard V1及另一个Video Prompt V1，二者来源Prompt UUID不同。生成快照、edited_content（含空白）、notes、版本与Selected逐字段保持。

最终ZIP有3个Asset、2个PromptRecord、1个Storyboard、1个VideoResult、3个ProjectAssetLink及3个ShotAssetLink；GLOBAL模板实体未导出，其Prompt快照存在。测试软删除Character未导出；另一个测试Character完成回收站出现/恢复/消失。全部原生产派生记录逐字段未变。

实际ZIP由正常Export API生成；完整性、引用、媒体、UUID、版本、双来源、安全路径及secret sentinel排除通过。数据库integrity=ok、FK=0、revision=0010。没有调用真实AI或图片/视频生成API。

以上是synthetic acceptance data in production-derived isolated copy only，**不是生产原生Prompt/Storyboard/VideoResult验收**。

### 清理与生产保护：PASS

TestClient和数据库连接/ZIP句柄关闭后，只删除明确校验位于仓库`.workspace`下的本轮唯一目录`phase11-real-0cab946b5e7f4433b68b16be49a03363`，包含Workspace、Bootstrap、AI测试配置、ZIP与测试媒体；删除后确认目录不存在。不复用、不删除前一轮副本，不写生产。

清理后生产11个文件+Bootstrap+HANDOFF共13项SHA-256与本轮基线完全一致。生产DB hash `d0226a65c89bccaeada79e678ede430c67e93ce988ca53db06c230e8da3e1f49`，revision仍`0010_video_results`；只读复核PromptRecord=0、Storyboard=0、VideoResult=0。没有Fake数据写回。HANDOFF hash `a04b393c2c84a5aab9d0b16f75768dd6c29a2ce7f91d590396cc6845394e8e5c`，保留用户修改，不stage/commit/restore。

## 限制与收尾

Export是项目活跃工作集归档，不是整个Workspace数据库备份；不包含回收记录、GLOBAL实体、缩略图、机器配置。Import尚未实现；versioned ZIP为未来Import提供基础，不能宣称现有导入已验证。

后端流式读媒体/传响应，但前端下载前使用Blob保留完整ZIP，大型项目仍受浏览器内存与本地磁盘容量限制。回收站查询当前在服务端汇总筛选，UI分页不等于数据库级分页优化。无后台导出任务、导出进度百分比或永久清空。

最终只提交Phase11产品、测试及文档文件，不提交任何ZIP/DB/media/log/trace/dist/secret配置；HANDOFF维持用户原有修改。完成后停止，不开启新Phase。
