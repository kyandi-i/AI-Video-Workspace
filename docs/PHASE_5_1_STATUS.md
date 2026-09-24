# Phase 5.1 — Workspace Root Recovery & Hardening 验收

日期：2026-09-24。基线 `f1128b9`（`feat: add shot production workspace`），开始时 `git status --short` 为空。

范围仅限 **Workspace Root / Bootstrap Config / 环境分叉 / fallback 自播种**。未进入 Phase 6，未新建 migration，未删除任何 Workspace。

## 1. 问题与根因

Phase 5.1 诊断确认：C / D 两套 Workspace 本身没有“谁更新”的问题，真正的问题是**两个运行环境读取了两份不同的 Bootstrap Config**：

| 环境 | Bootstrap Config | 指向 |
| --- | --- | --- |
| 普通 Windows 会话 | `C:\Users\Lenovo\AppData\Roaming\AI-Video-Workspace\config.json` | `C:\Users\Lenovo\AI-Video-Workspace` |
| Codex 打包应用（`%APPDATA%` 被 Junction 重定向） | `D:\WpSystem\S-1-5-21-…\LocalCache\Roaming\AI-Video-Workspace\config.json` | `D:\AI-Video-Workspace` |

Phase 3.1 / 4 / 5 全部在 Codex 环境内验收，因此报告读到 D；而普通会话的真实 Roaming 配置当时不存在。

**fallback 自播种**：`WorkspaceService.initialize_workspace()` 在解析 root 后无条件调用 `bootstrap.save(root)`。于是 2026-09-23 23:40:30 普通会话首次启动时：配置缺失 → 回退 `~/AI-Video-Workspace`（C）→ 建空目录 + 空库（`0005` head，0 行）→ **把回退结果正式写成 Roaming 配置**。此后普通会话永久使用空的 C，而 D 的真实数据只存在于 Codex 环境。

`NO CONFIG` 被错误地当成了“用户已选择默认 Workspace”。

## 2. 只读事实基线（未修改任何文件）

- D 真实性：`project=1`、`script=1`、`script_node=3`、`scene=3`、`shot=4`、`asset=1`、`character=1`、`character_state=6`、`shot_character_state_link=1`；S13 = 风淋 / 10 秒 / 场景风淋室，四个 Phase 5 字段齐全，绑定 `SPF培训女员工 → 黄色 PPE + 双层手套`；`integrity_check=ok`、`foreign_key_check` 空、`alembic_version=0005_shot_workspace`。
- C 真实性：除 `alembic_version` 外**全部 0 行**，`storage/assets`、`storage/thumbnails` 为空，目录与 `workspace.db` 的创建时间均为 2026-09-23 23:40:30。

## 3. 安全备份

修改配置前为真实 DB 建立额外安全备份（原库只读复制，不做 sqlite backup 重写，保证字节一致）：

```text
D:\AI-Video-Workspace\backups\before-workspace-config-fix-20260924-161401.db
```

| 项目 | 值 |
| --- | --- |
| 源 | `D:\AI-Video-Workspace\data\workspace.db` |
| 源 SHA-256 | `425A2564DCAD48B9598815790E62AD1C2190C2D88C6CBCC522071454E6750C9C` |
| 备份 SHA-256 | `425A2564DCAD48B9598815790E62AD1C2190C2D88C6CBCC522071454E6750C9C` |
| 一致 | 是（311,296 字节） |

已有的 `before-phase4-20260923.db`、`before-phase5-20260923.db` 未被覆盖，SHA-256 全程不变。

## 4. 代码变更（唯一功能改动）

`backend/app/services/workspace.py` → `initialize_workspace()` 删除 `self.bootstrap.save(root)`：

- 配置缺失时只在内存中使用默认 root，仍然正常初始化 Workspace（首次体验不变），但**绝不**创建/改写 Bootstrap Config。
- 只有显式用户动作 `set_workspace_root()`（`PUT /api/settings/workspace`）会写 Bootstrap Config。
- 配置损坏 / 形状非法 / root 非绝对路径仍然明确报 `BOOTSTRAP_INVALID`，不回退。

已复核全部 `bootstrap.save(...)` 调用点：仅剩 `set_workspace_root()`（显式用户动作）。`migrations/env.py` 只调用 `prepare_directories` / `validate_workspace`，从不写配置。无 schema 变更、无新 migration、未硬编码任何机器路径。

## 5. 恢复动作（先验证、再切换、后重启）

1. 只读确认 D 数据完整（见第 2 节）。
2. 启动真实应用（普通 Windows 会话）→ `GET /api/settings/workspace` = C（复现问题）。
3. **通过正式 API** `PUT /api/settings/workspace` 设置 `D:\AI-Video-Workspace` → 成功，未做任何 COPY / MOVE / RENAME / DB 覆盖。
4. 完全关闭并重新启动进程（非热重载）→ `GET /api/settings/workspace` = D，`database_path` = D。
5. 创建共享配置 `D:\AI-Video-Workspace-Config\config.json`（仅 `workspace_root` 一个键，52 字节，位于 Workspace 之外、仓库之外），并设置**用户级**（Current User，非 Machine）环境变量 `AVW_BOOTSTRAP_CONFIG_PATH`。

未修改 `APPDATA` / `HOME` / `USERPROFILE`，未新建 symlink / junction。

## 6. 最终验收证据

### A. 普通 Windows（Task Scheduler 全新进程，注册表派生的环境块）

```text
APPDATA                       = C:\Users\Lenovo\AppData\Roaming
AVW_BOOTSTRAP_CONFIG_PATH     = D:\AI-Video-Workspace-Config\config.json
bootstrap_config_path         = D:\AI-Video-Workspace-Config\config.json
resolve_bootstrap_root        = D:\AI-Video-Workspace
database                      = D:\AI-Video-Workspace\data\workspace.db
```

### B. Codex / 重定向 APPDATA（同一共享配置）

```text
APPDATA                       = D:\WpSystem\S-1-5-21-…\LocalCache\Roaming
bootstrap_config_path         = D:\AI-Video-Workspace-Config\config.json
resolve_bootstrap_root        = D:\AI-Video-Workspace
database                      = D:\AI-Video-Workspace\data\workspace.db
```

`AVW_BOOTSTRAP_CONFIG_PATH` 的优先级高于 `%APPDATA%` 默认位置（第 15 节铁约束满足）。

### C. 两者一致

```text
bootstrap_config_path equal = true    (D:\AI-Video-Workspace-Config\config.json)
workspace_root        equal = true    (D:\AI-Video-Workspace)
```

### D. 真实数据（启动后经正式 API）

```text
SPF project exists  = true     (SPF屏障设施培训视频)
S13 exists          = true     (风淋 / 10.0s / 场景 风淋室 / position 4 of 4 / prev S10)
Character exists    = true     (SPF培训女员工, state_count=6)
6 States exist      = true     (基础状态 / 发帽+口罩 / 黄色 PPE / 黄色 PPE+第一层手套 / 黄色 PPE+双层手套 / 退出状态)
Phase 5 fields      = true     (main_action / key_constraints / negative_constraints / free_notes 全部 PRESENT)
角色状态绑定         = true     (S13 → SPF培训女员工 → 黄色 PPE + 双层手套)
```

### E. 最小写入测试

通过正式 API 创建一条 `TEMP_WORKSPACE_VERIFY` 项目，再用正式 API `DELETE`（应用自身软删除语义，未使用任何直接 SQLite DELETE）：

```text
D projects 1 → 2 → 活跃 1（软删除 1）   write occurred in D = true
C workspace.db SHA-256 全程 4681CB2E…   C changed = false
```

唯一残留：D 中一条软删除的 `TEMP_WORKSPACE_VERIFY` 项目行（应用无硬删除 API）。除此之外 D 无其他业务数据变化。

### F. fallback 自播种已修复（真实全新进程）

```text
config_existed_before        = false
config_exists_after_boot     = false
used_root                    = <默认 Workspace>
db_created                   = true      （首次体验保持可用）
config_auto_created          = false
```

### G. C Workspace 状态

```text
C:\Users\Lenovo\AI-Video-Workspace\data\workspace.db
  size   311,296
  SHA-256 4681CB2E95B53DF22E3A23412B387242347C9E1B0B4CA12AB3AB84089DF21E0F
```

该哈希在切换、重启、写入测试、全部自动化回归前后**完全一致**；C 在恢复完成后不再被读取或写入。

### H. 自动化回归

| 检查 | 结果 |
| --- | --- |
| Backend | **157/157**（Phase 5 基线 148 + 新增 9） |
| Browser production | **36/36**（基线 36） |
| Browser development | **38/38**（基线 38） |
| Ruff check | PASS |
| Ruff format --check | PASS，65 个 Python 文件 |
| Frontend lint | PASS |
| Frontend build | PASS |
| Alembic（隔离 Workspace） | upgrade head → downgrade base → upgrade head PASS；`current` = `0005_shot_workspace (head)`；`check` = No new upgrade operations detected |

新增 9 项覆盖：缺失配置不落盘、显式切换持久化 + 重启恢复、`AVW_BOOTSTRAP_CONFIG_PATH` 压过 `APPDATA`、两个 APPDATA 环境共用同一配置、非法共享配置明确报错且不回退（4 组参数）、测试进程完全隔离在临时目录内。

Alembic 的 upgrade → downgrade → upgrade **只**作用于 `.workspace/phase5.1-alembic/workspace` 隔离库；真实 D 库从未执行 downgrade。

### I. 自动化测试未触碰真实数据

回归前后逐文件 SHA-256 一致：

```text
D:\AI-Video-Workspace\data\workspace.db                                          SAME
D:\AI-Video-Workspace\storage\assets\5b\5be67f8c-…png                            SAME
D:\AI-Video-Workspace\storage\thumbnails\69c6f8b9-…jpg                           SAME
D:\AI-Video-Workspace\backups\before-phase4-20260923.db                          SAME
D:\AI-Video-Workspace\backups\before-phase5-20260923.db                          SAME
D:\AI-Video-Workspace\backups\before-workspace-config-fix-20260924-161401.db     SAME
C:\Users\Lenovo\AI-Video-Workspace\data\workspace.db                             SAME
```

pytest 的 autouse fixture 与 Playwright 的 `webServer.env` 都显式注入独立的 `AVW_WORKSPACE_ROOT` / `AVW_BOOTSTRAP_CONFIG_PATH`，因此本机生产环境变量不会被自动化测试继承，也未被任何测试修改。

## 7. 旧配置的去向（均保留，未删除）

| 路径 | 内容 | 状态 |
| --- | --- | --- |
| `D:\AI-Video-Workspace-Config\config.json` | `D:\AI-Video-Workspace` | **当前生效**（由 `AVW_BOOTSTRAP_CONFIG_PATH` 指定） |
| `C:\Users\Lenovo\AppData\Roaming\AI-Video-Workspace\config.json` | `D:\AI-Video-Workspace` | 保留；已由正式 API 修正，但不再是有效来源 |
| `D:\WpSystem\…\LocalCache\Roaming\AI-Video-Workspace\config.json` | `D:\AI-Video-Workspace` | 保留；不再被读取 |

按本阶段约束，未删除任何旧配置、旧备份或审计文件。

## 8. 已知限制

- 迁移由用户级环境变量承载，因此**每个新会话**才会继承；已存在的旧终端不会自动获得（需重开终端或重启应用）。
- 本阶段未增加首启向导、强制 Workspace 选择器或启动弹窗。
- API 响应仍未暴露“当前 root 是否来自已保存选择”，前端无法区分“已保存”与“内存默认”。
- 应用没有硬删除 API，`TEMP_WORKSPACE_VERIFY` 验收记录只能软删除。

## 9. C Workspace 处置建议

**Safe to delete（需用户明确确认）**。C 只含一个 0 业务行的空库与空目录，不含任何唯一数据；Phase 3 时代的真实内容在 D 及其 `before-phase4` 备份中完整存在。本阶段**未删除** `C:\Users\Lenovo\AI-Video-Workspace`，等待用户确认。

## 10. 停止

Workspace 切换、共享配置、fallback 加固、测试、文档与提交均已完成，工作树干净。**立即停止开发，不进入 Phase 6 Prompt Template，等待用户确认。**
