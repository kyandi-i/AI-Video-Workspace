# Phase 10 — Video Result / COMPLETE

日期：2026-10-01。基线 HEAD：`baab8a2bad9855eeb3cc3f08f07eebb3ed99f6e2`。

用户已冻结双 nullable provenance、VIDEO Asset、整数版本、Selected 和独立 Link 生命周期。后端、界面、完整回归、生产隔离副本独立 OS 进程重启、生产备份与升级均验证通过。**Phase 10 COMPLETE；Phase 11 NOT STARTED。**

## Schema / migration

新增 `0010_video_results`，down_revision=`0009_storyboards`。不改旧 migration 或 AssetType。

- `id` UUID PK；`shot_id` FK shots.id、`asset_id` FK assets.id，均非空。
- `source_storyboard_id` nullable FK storyboards.id。
- `source_prompt_record_id` nullable FK prompt_records.id。
- `version` INTEGER NOT NULL，CHECK > 0，UNIQUE(shot_id, version)。
- `is_selected` BOOLEAN NOT NULL；partial unique index 每 Shot 最多一条 `is_selected=1 AND deleted_at IS NULL`。
- `notes` nullable TEXT，输入上限 10,000 字符。
- BaseModel 的 UUID、UTC created_at/updated_at、nullable deleted_at。
- 四个 FK 字段各有索引；无媒体 binary/base64/path 副本，无冗余 project_id。

## Provenance / version / selection

两条来源独立，支持均空、仅 Storyboard、仅 Prompt、两者均有。创建时必须引用当前 Shot 的有效来源，拒绝跨 Shot 和不存在/已删除来源，不要求两条 Prompt ID 相等，不增加 Prompt 类型限制。

保存具体历史 ID，Selected 变化不会漂移；不复制 Prompt 文本。历史读取和恢复允许读取已软删除的来源，Storyboard 来源显示 Deleted，保持历史结果可读。Prompt edited_content 可变，来源 ID 不变，不宣称保存了编辑时文本快照。

每 Shot 从 V1 递增；MAX 包含软删除版本，不复用。先清除 Selected 获取 SQLite writer lock，再分配版本，事务和 DB 唯一约束共同保护。首次及后续创建自动采用；手工 Select 清除旧采用。删除采用无 fallback；恢复被删除记录不 Selected、不抢占当前采用。没有覆盖历史媒体/来源的 PATCH。

## Storage / Asset lifecycle

只接受 AssetType.VIDEO。StorageService 保留既有 staging、metadata、thumbnail、512 MiB 限制及文件补偿路径，增加同一 Asset 写入事务中的结果创建回调；没有新 Storage 框架。五个故障点验证 Asset/ProjectLink/ShotLink/VideoResult INSERT 后及 outer commit 前均回滚并清理导入文件。

导入和 Use Existing 均确保 ProjectAssetLink/ShotAssetLink，已存在 Link 复用。结果与 Link 生命周期独立；删除结果不删 Asset、Link、视频或 thumbnail。恢复要求 Asset 有效且为 VIDEO，不重建 Link。父级软删除仍保留引用保护。

AssetService 统一 ASSET_IN_USE 检查包含 active VideoResult；禁止改离 VIDEO。Asset Detail 返回视频引用及 Shot Workspace 链接，保留旧“请先解除绑定”兼容主提示。

## API

```text
GET  /api/shots/{shot_id}/video-results[?include_deleted=true]
POST /api/shots/{shot_id}/video-results
     {asset_id, source_storyboard_id?, source_prompt_record_id?, notes?}
POST /api/shots/{shot_id}/video-results/import
     ?filename=...&source_storyboard_id=...&source_prompt_record_id=...&notes=...
     raw video request body
GET  /api/video-results/{id}[?include_deleted=true]
POST /api/video-results/{id}/select
DELETE /api/video-results/{id}
POST /api/video-results/{id}/restore
```

Route 委托 Service，SQL 留在 Repository，媒体访问通过现有 StorageService/Provider 和 Asset file endpoint。

## UI

Requirements → Prompt → Storyboard → Video Results → Production Status。

Video Results 包含 Current Selected、History、两条独立来源选择（默认不关联）、notes、Import Video/拖入、Use Existing Video Asset、Select、Delete，以及本面板 Show deleted videos / Restore。未扩展全局 Recycle Bin。

History 只展示 thumbnail；主动打开 Preview 才挂载 `<video controls preload="metadata">`，无 autoplay，关闭卸载。播放失败提供原文件链接。导入 pending 纳入 Shot 页面离开保护。Dark/Light、1024/1280 截图已检查，布局紧凑且无水平溢出；使用现有公共组件与 Lucide。

## Validation completed this run

| 检查 | 结果 |
| --- | --- |
| `uv run --locked --project backend pytest backend/tests/test_video_results.py -x -q` | 28 passed，exit 0 |
| `uv run --locked --project backend pytest backend/tests -x -q` | 342 passed，exit 0 |
| Ruff check / format --check | PASS；recovery 最终 106 files formatted，exit 0 |
| Frontend lint / build | PASS，exit 0 |
| `npm --prefix frontend test -- video-results.spec.ts --max-failures=1` | 5 passed，exit 0 |
| production Browser FULL | 67 passed，exit 0 |
| development Browser FULL | 69 passed，exit 0 |
| isolated Alembic CLI | 0009 → head → 0009 → head → check → current PASS；0010_video_results (head) |
| populated migration | 后端专项中 PASS；含 Prompt、Storyboard、视频 Asset 的旧库回退/回升，旧表逐行不变 |
| Production protection | 自动化前后 12/12 SHA-256 一致；finalization 升级前再次核验通过 |
| independent process restart | PASS；两个独立 OS 进程 exit 0，完整业务断言、清理、最终哈希通过；脚本 exit 0 |

后端测试含四种来源组合、来源稳定性、版本/Selected、软删除恢复、Asset 类型/引用保护、独立 Link、并发、真实 DB 约束冲突、五个事务故障点、有数据迁移和新 TestClient 持久化。浏览器覆盖实际视频播放、两个版本/切换、双来源、notes、删除无 fallback、恢复不 Selected、刷新、已有视频和无效导入后显式重试。

新 TestClient 不等于新后端进程；追加验收使用真实生产隔离副本与两个独立 Uvicorn OS 进程，经 API 验证重启后的完整历史、Selected、notes、双 provenance、Asset / ProjectAssetLink / ShotAssetLink、视频 file 与 thumbnail。浏览器播放由此前 Browser 测试覆盖，不把 API 验收称作新浏览器运行。

保留既有 TestClient 弃用、Rollup 注释及 bundle-size warning。production browser 日志出现一次 Windows ConnectionResetError，但全部断言通过且进程正常 exit 0。没有跳过测试、修改旧功能 expected 或削弱断言；仅两处旧 schema/head 断言准确纳入新表和 revision。

## Failure-stop / recovery history

准备通过 `.workspace/phase10/restart-acceptance.mjs` 在 `.workspace/e2e/phase10-s13-*` 复制生产 Workspace、使用 guarded Fake app 和两个独立后端 PID 完成真实 S13 浏览器验收。写入该脚本的 apply_patch 返回 **`patch rejected by user`**，无进程退出码；文件未创建，脚本未运行。未换工具绕过拒绝。

之后用户授权创建正式验收工具 `scripts/accept_video_restart.py` 与 `backend/test_support/restart_server.py`，复用 `.workspace/e2e` 隔离边界、Fake provider 和现有媒体夹具，不新增业务测试接口。

首次完整执行两个 Backend（PID 4944 / 34968）均 exit 0，业务断言通过，但清理时 SQLite connection 未显式关闭导致 WinError 32，脚本 exit 1；按 Failure-stop 停止，未备份或迁移。独立补核保护哈希 12/12 不变。

用户授权 recovery 后，连接改为显式 closing，检查 HTTP/file/pipe 生命周期，主失败与清理失败分别记录，清理异常也尽量完成 hash/report。未修改任何业务断言或业务代码。重新从新副本完整运行，PID 31584 / 30148 均 exit 0、脚本 exit 0，所有断言 PASS；新旧隔离目录完整删除，保护哈希 12/12 不变，Ruff PASS。本地证据保存在忽略目录 `.workspace/phase10/phase10-restart-zbjjkzeu/`，不提交。

复现命令（仅适用于待升级的 0009 生产来源；不会修改来源）：

```powershell
uv run --locked --project backend python scripts/accept_video_restart.py --source <0009-workspace> --bootstrap <source-bootstrap-config>
```

该工具保留为正式 Phase 10 acceptance infrastructure，当前生产已升至 0010，不能直接拿当前生产重复此 0009 基线验收。

## Production / Git

- Production：`D:\AI-Video-Workspace`；Bootstrap：`D:\AI-Video-Workspace-Config\config.json`。
- Production migration：`0009_storyboards → 0010_video_results`，正式 `uv run --locked --project backend alembic -c backend/alembic.ini upgrade head` exit 0；显式指定生产 Bootstrap，未 downgrade 或手工 schema SQL。
- Backup：`D:\AI-Video-Workspace\backups\before-phase10-20261001-161901.db`。
- 迁移前源与 Backup SHA-256：`54da9298e132c8857763ba8761073111895167f329bf6b187ad179145c0df64c`，复制前后源 hash 与 backup 均相等。
- 迁移后 DB SHA-256：`d0226a65c89bccaeada79e678ede430c67e93ce988ca53db06c230e8da3e1f49`；正式 schema migration 后改变属于预期。
- 实际读取 revision=`0010_video_results`，integrity_check=ok、foreign_key_check=0，video_results=0；没有 Fake 数据。
- 19 个 Phase 0–9 表全部行/字段与升级前快照一致：Project 2、Script 1、ScriptNode 3、Scene 3、Shot 4、Asset 1、Character 1、CharacterState 6、ShotCharacterStateLink 1、PromptTemplate 2；PromptRecord、Storyboard、Tags/AssetTags、两类 AssetLink、Character/State AssetLinks 与 app_settings 原本为 0，升级后仍为 0。没有将空历史描述为非空历史。
- 自动化期间生产+Bootstrap+HANDOFF 12/12 不变；迁移后除预期 DB 变化与新增备份外，其余保护文件不变。完整快照及验证结果位于忽略目录，不提交。
- 本轮独立基线含全部生产文件、Bootstrap、HANDOFF 共 12 个，保存在忽略目录 `.workspace/phase10/before.json`。
- HANDOFF 原有用户修改未编辑、暂存或提交；本轮初始 SHA-256 为 `A04B393C2C84A5AAB9D0B16F75768DD6C29A2CE7F91D590396CC6845394E8E5C`。
- 旧浏览器测试重写的五张受 Git 管理截图已从本轮备存原件恢复。
- Phase 10 交付提交使用 `feat: add video result workflow`；只包含实现、测试、正式验收工具与文档，不包含 HANDOFF、配置、DB、媒体 fixture、trace、dist、临时截图或本地验收证据。最终提交 ID 以 Git history / 最终报告为准。

## Known limitations

历史暂未分页；notes 在创建时保存，没有编辑既有结果的接口。浏览器播放受本机 codec 支持限制；没有转码/HLS。Prompt 来源关联不是文本快照。SQLite 单写者和跨进程 busy/冲突沿用现有边界；文件补偿不提供进程崩溃原子性。没有 GenerationJob、视频生成 API、队列、视频编辑器或 Phase 11 功能。
