# Phase 3.1 — Workspace Migration 验收

日期：2026-09-22。范围仅 Workspace Migration；Phase 4 未开始。

## 基线与实机差异

开始时 `git status --short` 为空，HEAD 为 `50cd7c9 feat: complete Phase 3 unified asset library`。先阅读计划、MVP 规格与开发状态，再搜索定位 Bootstrap、WorkspaceService、StorageService、LocalStorageProvider、Settings、测试隔离与启动器。

当前进程检查没有本项目 FastAPI / Vite。C 盘保存真实 Phase 3 数据；D 盘已存在目录，但只有 24,576 字节、版本为 0001_app_settings 的空数据库。读取到的用户 Bootstrap 已指向 D，因此此前 README 的“已迁移”描述不代表真实数据完整迁移。本轮未把空 D 库覆盖回 C。

## 复制与保留

源：`C:\Users\Lenovo\AI-Video-Workspace`。
目标：`D:\AI-Video-Workspace`。

| 项目 | 源 | 复制校验后目标 |
| --- | ---: | ---: |
| 文件数 | 3 | 3 |
| 文件总字节 | 16,052,219（约 15.31 MiB） | 16,052,219 |
| data/workspace.db | 200,704 字节 | 200,704 字节 |
| storage/assets | 1 文件，15,787,864 字节 | 相同 |
| storage/thumbnails | 1 文件，63,651 字节 | 相同 |
| storage/temp / exports / backups | 空目录 | 全部保留 |

先完整备份旧 D 目录到 `D:\AI-Video-Workspace-before-phase3.1-20260922`（24,576 字节），再 COPY 源的全部内容。未按扩展名筛选，8 个子目录及3个文件均比较一致。源与目标不存在 DB WAL / SHM / journal。复制后逐文件 SHA-256 相等，DB 校验值：

```text
58ea53e6eb6e27906f6ed8bd2fc3ebf65e1895d2b4f1a5bd17e5a98a71ef20f0
```

校验成功后才调用项目原有 `BootstrapConfig.save(target)`。没有 MOVE 或删除源文件。人工上传及清理会合法改变目标数据库字节；最终采用完整逐表逐行相等验证业务记录，源数据库 hash 始终不变。

## Bootstrap 与路径

逻辑配置位置：`C:\Users\Lenovo\AppData\Roaming\AI-Video-Workspace\config.json`（`%APPDATA%`）。内容仅 `workspace_root`，现在为 `D:\AI-Video-Workspace`。本机 Codex 是 Windows 打包应用，`BootstrapConfig.path` 将重定向目录解析为：

```text
D:\WpSystem\S-1-5-21-2336341969-3287654707-1809469733-1001\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Roaming\AI-Video-Workspace\config.json
```

逻辑 Roaming 与 Package LocalCache 两个可见入口均读取到 D。未新增第二套配置。架构保持 Bootstrap Config → Workspace Root → data/workspace.db → managed storage。Bootstrap 位于 Workspace 之外；app_settings 不用于定位数据库。产品默认值仍为用户 home 下目录，未硬编码 D。

实际数据库：`D:\AI-Video-Workspace\data\workspace.db`。storage、thumbnails、temp、exports、backups 均从当前 root 解析。`StorageService.file()` 经过原有 Provider 解析为 D 盘绝对路径；数据库中的 storage_path / thumbnail_path 仍是 `storage/...` 相对路径，无需重写任何 Asset 字段。

## 数据与真实应用验收

清理验收资产后，D 与 C 的所有表、所有原有行完全相等。`PRAGMA integrity_check=ok`，`foreign_key_check` 无错误，Alembic 为 `0003_asset_library`。

| 数据 | 原有数量 | 迁移后 |
| --- | ---: | ---: |
| Project / Script | 1 / 1 | 1 / 1 |
| ScriptNode / Scene / Shot | 2 / 2 / 3 | 2 / 2 / 3 |
| Asset | 1 | 1 |
| Tags / AssetTag | 0 / 0 | 0 / 0 |
| ProjectAssetLink / ShotAssetLink | 0 / 0 | 0 / 0 |

通过实际生产应用的 Asset Library 打开原有图片：缩略图解码、4312×4300 原图、metadata 均正常；标签和绑定空态符合真实数据库。真实库无视频，未声称验证了真实视频播放；既有隔离视频回归已通过。非空标签、AssetTag、项目与镜头绑定的复制保留由新增隔离迁移用例验证。

## 新写入及清理

在真实页面导入独立32×24 PNG（这是本次用户要求的人工验收，不属于自动化回归数据）：

- Asset UUID：`7bd72d20-f653-46de-bce6-23262eebbb53`。
- 原图：`D:\AI-Video-Workspace\storage\assets\76\7629ac6e-bcfe-4cc0-8978-ffdb6f4f0715.png`。
- 缩略图：`D:\AI-Video-Workspace\storage\thumbnails\ae655aca-72f6-4b2f-be38-0de0c6920c99.jpg`。
- D 数据库能查到对应记录，两条路径均为 Workspace 相对路径，页面可预览。
- C 下不存在上述新文件，源全量文件清单与 SHA-256 未变。

验证后停止本轮应用，精确校验该 UUID / 名称 / 路径，仅清理此测试记录、两个生成文件及它产生的空 bucket。没有新增永久删除业务 API。最终数据恢复为原来的3个文件、16,052,219字节，全部原有记录相等。随后重新启动应用，GET Workspace 返回 D，Asset Library 返回原有1项。

验收脚本、manifest、临时图片、实机截图和进程日志位于 Git 忽略的 `.workspace/phase3.1-audit/`，不随提交保存；真实素材和数据库均不进入仓库。

## 最小实现变更

Settings 原来只有只读 Workspace 信息；后端原有 PUT API 已支持初始化新目录、切换、持久化与重启恢复。新增路径输入与保存按钮直接复用该 API。成功后整页加载 Settings，丢弃旧 root 的查询缓存和路由；失败保留输入并反馈。

明确区分 Switch 与 Migrate：选择空目录仍会得到空 Workspace，不自动搬迁文件。没有新增迁移 API、Workspace Manager、数据库 revision、Storage Provider 重写或其他业务模型。

## 回归

| 检查 | 结果 |
| --- | --- |
| frontend lint / build | PASS / PASS |
| pytest backend/tests | 111/111 PASS（原109 + 复制切换/重启2项） |
| Ruff check / format --check | PASS，52个Python文件 |
| browser production | 28/28 PASS（原26 + Settings切换/失败2项） |
| browser development | 30/30 PASS（原28 + 2项） |
| Alembic CLI upgrade head → downgrade base → upgrade head | PASS |
| Alembic current / check | 0003_asset_library (head)，No new upgrade operations detected |
| git diff --check | PASS |

使用仓库已有命令与虚拟环境（无新增依赖）：

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
backend/.venv/Scripts/ruff.exe check backend/app backend/tests scripts
backend/.venv/Scripts/ruff.exe format --check backend/app backend/tests scripts
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend test
$env:AVW_E2E_MODE = 'dev'
npm --prefix frontend test
```

Alembic CLI 单独指定 `.workspace/phase3.1-alembic/config.json` 和 `.workspace/phase3.1-alembic/workspace`，再执行 upgrade / downgrade / upgrade / current / check。pytest 沿用 autouse 临时 root / Bootstrap，新增测试明确断言隔离；Playwright 沿用每轮 `.workspace/e2e/run-*`，Settings UI 测试 mock 切换响应以避免影响并行用例，实际切换由后端集成用例验证。自动化回归没有向真实 D Workspace 写测试数据。

首次 pytest 因 Windows 临时目录沙箱权限失败，授权后完整回归通过。首次生产浏览器28项用例通过但服务退出阻塞，结束专用测试服务后退出0；沙箱外复跑28/28并正常退出，开发30/30正常退出。保留原有 Python 弃用、Vite chunk 和 Zod 注释警告，无新增依赖升级或掩盖警告。

## 保留与停止

旧 `C:\Users\Lenovo\AI-Video-Workspace` **仍存在且未修改**，总文件大小 **16,052,219字节（约15.31 MiB）**。当前运行应用已确认使用 D；C 仅作安全备份，须用户人工确认后才可删除。

本阶段完成，停止开发，等待验收；不进入 Phase 4。
