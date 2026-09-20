# Phase 1：Database + Alembic + Storage Infrastructure

当前 Phase：1
前置条件：Phase 0 已完成并通过测试。

严格遵守 `PROJECT_PLAN.md`。

本阶段只实现数据库基础设施、Workspace 配置基础和 Storage 抽象。

**禁止提前实现 Project / Script / Scene / Shot 的业务页面和完整 CRUD。**

---

# 1. 本阶段目标

完成以下基础能力：

```text
SQLite
+
SQLAlchemy
+
Alembic
+
UUID
+
Base Model
+
Repository 基础结构
+
Workspace Root
+
StorageProvider
+
LocalStorageProvider
+
文件安全存储
+
基础测试
```

完成后，后续所有业务模块都应能够建立在这一基础上。

---

# 2. SQLAlchemy 基础设施

建立统一 Database 模块。

推荐：

```text
backend/app/core/database.py
```

至少提供：

```text
engine

SessionLocal

Base

get_db()
```

开发环境使用 SQLite。

数据库文件默认位于：

```text
<workspace_root>/data/workspace.db
```

禁止把数据库固定写死在源码目录。

---

# 3. UUID Base Model

所有未来核心业务表统一使用 UUID。

建立可复用 Base Model / Mixin，例如：

```text
UUIDMixin

TimestampMixin

SoftDeleteMixin
```

建议字段：

```text
id UUID

created_at

updated_at

deleted_at nullable
```

要求：

* Python 层优先使用 `uuid.UUID`
* SQLite 可使用 String(36) 或项目统一的 UUID TypeDecorator
* 必须保证未来迁移 PostgreSQL 时不需要修改上层业务代码
* UUID 默认由应用生成，不依赖数据库自增

---

# 4. Timestamp 规则

统一采用：

```text
created_at
updated_at
```

所有时间统一使用同一种标准。

推荐：

```text
UTC
```

后续前端负责本地化显示。

禁止不同 Model 自己定义不同时间行为。

---

# 5. Soft Delete 基础

实现通用：

```text
deleted_at
```

本阶段不需要完整 Recycle Bin UI。

但数据库基础和 Repository 设计必须能够支持：

```text
普通查询
→ 默认忽略 deleted_at != null

include_deleted 查询

soft_delete()

restore()
```

不要物理删除业务对象作为默认行为。

---

# 6. Alembic

配置 Alembic。

要求：

```text
alembic revision --autogenerate

alembic upgrade head

alembic downgrade
```

均可正常工作。

Alembic 必须能够发现 SQLAlchemy Metadata。

不要依靠启动应用时自动 `create_all()` 作为正式数据库 Schema 管理方案。

测试中可以根据需要使用独立测试数据库。

---

# 7. Phase 1 基础表

本阶段不要急着实现完整业务 Schema。

只建立真正属于基础设施的表。

建议至少：

## app_settings

用于保存普通应用设置。

例如：

```text
id
key
value
created_at
updated_at
```

注意：

API Key 等敏感数据后续不要混入普通项目 Export。

---

如当前架构更适合使用本地配置文件保存 Workspace Root，也可以。

原则：

```text
必须能够在数据库尚不存在之前找到 Workspace Root
```

因此：

**Workspace Root 本身不能只存在 workspace.db 中。**

否则会出现循环依赖：

```text
不知道 Workspace Root
→ 找不到数据库
→ 需要数据库才能知道 Workspace Root
```

需要设计独立 Bootstrap Config。

---

# 8. Bootstrap Config

设计一个非常小的本地启动配置。

用途只负责：

```text
当前 Workspace Root
```

例如存放在用户配置目录：

```text
%APPDATA%/AI-Video-Workspace/config.json
```

或其他合理的用户级配置位置。

不要存储项目业务数据。

示例：

```json
{
  "workspace_root": "D:\\AI-Video-Workspace"
}
```

首次启动：

```text
无配置
↓
使用合理默认 Workspace
↓
创建必要目录
↓
创建配置
```

后续 Settings 修改 Workspace Root 时修改这里。

---

# 9. Workspace Service

建议建立：

```text
WorkspaceService
```

负责：

```text
get_workspace_root()

set_workspace_root()

validate_workspace()

initialize_workspace()

get_database_path()

get_storage_path()

get_thumbnail_path()

get_temp_path()

get_export_path()

get_backup_path()
```

业务模块不得自行拼：

```python
"D:\\xxx\\storage\\..."
```

---

# 10. Workspace 目录

首次初始化自动创建：

```text
<workspace_root>/

├── data/
│   └── workspace.db
│
├── storage/
│   ├── assets/
│   ├── thumbnails/
│   └── temp/
│
├── exports/
│
└── backups/
```

重复初始化必须是幂等操作。

不能因为目录已经存在而失败。

---

# 11. StorageProvider

建立抽象接口：

```text
StorageProvider
```

不要让业务 Service 依赖具体磁盘实现。

接口至少考虑：

```text
save_file()

delete_file()

move_file()

exists()

get_absolute_path()

create_thumbnail()
```

如果本阶段缩略图实现过早，可以：

```text
定义接口
+
提供基础实现或明确 NotImplemented
```

但接口设计需要存在。

---

# 12. LocalStorageProvider

实现：

```text
LocalStorageProvider
```

负责 Managed Local Storage。

文件写入流程：

```text
外部文件
↓
验证
↓
生成内部文件名
↓
复制进入 storage
↓
返回 Storage Object / Relative Path
```

数据库及业务层优先保存：

```text
relative storage path
```

而不是绝对：

```text
D:\...
```

例如：

```text
assets/7d/7d...uuid.png
```

实际访问路径通过 StorageProvider + Workspace Root 解析。

这样未来切换 Workspace 或云端 Storage 更容易。

---

# 13. 文件命名

禁止直接以用户原始文件名作为唯一磁盘名称。

建议：

```text
UUID + 原扩展名
```

例如：

```text
8345f2b0-....png
```

原始文件名未来保存到 Asset Metadata。

本阶段 Storage 层至少要支持：

```text
original_filename
stored_filename / relative_path
```

概念上的分离。

---

# 14. 路径安全

LocalStorageProvider 必须防止路径穿越：

```text
../../
```

不能允许任何调用删除 Workspace Root 之外的文件。

所有：

```text
save
delete
move
```

操作必须验证最终路径位于受管理 Workspace 内。

这一点必须有测试。

---

# 15. 文件保存安全

建议采用：

```text
复制到 temp
↓
验证完成
↓
移动到最终位置
```

或者其他等价的安全方案。

目标：

如果复制过程中异常，不留下被数据库误认为有效的半文件。

本阶段虽然还没有 Asset 表，也要把 Storage API 设计成未来容易实现：

```text
DB transaction
+
File operation compensation
```

---

# 16. Repository Base

建立轻量 Repository 基础结构。

例如：

```text
backend/app/repositories/base.py
```

可以提供通用：

```text
get()

list()

add()

update()

soft_delete()

restore()
```

但不要设计一个过度复杂的 Generic Framework。

核心目标只是保持：

```text
Route
→ Service
→ Repository
```

边界。

---

# 17. API 错误结构

建立统一 App Exception / Error Response 基础。

格式：

```json
{
  "code": "ERROR_CODE",
  "message": "Human readable message",
  "details": {}
}
```

至少处理：

```text
400

404

409

422

500
```

为后续：

```text
ASSET_IN_USE
WORKSPACE_INVALID
FILE_NOT_FOUND
```

等错误做准备。

---

# 18. Workspace API

本阶段可以提供极小 Settings / Workspace API，方便验证基础设施。

例如：

```text
GET /api/settings/workspace
```

返回：

```json
{
  "workspace_root": "...",
  "database_path": "...",
  "initialized": true
}
```

以及：

```text
PUT /api/settings/workspace
```

注意：

本阶段的“修改 Workspace”只做：

```text
验证新目录
+
初始化 Workspace
+
切换配置
```

**禁止自动搬迁旧 Workspace 文件。**

---

# 19. Settings UI

本阶段不需要完整 Settings 产品页面。

如果已有 Settings 路由，可以提供最基础 Workspace Root 展示和切换能力。

如果会明显拖慢 Phase 1，可先用 API 测试。

Phase 1 的重点是 Backend Infrastructure。

---

# 20. 测试要求

至少覆盖以下测试。

## Database

```text
数据库初始化成功

Alembic upgrade 成功

UUID 能正常写入读取

Timestamp 工作正常

Soft Delete 基础行为正常
```

## Workspace

```text
首次初始化自动创建目录

重复初始化不会失败

切换 Workspace Root 成功

非法 Workspace 路径返回可读错误
```

## Storage

```text
文件可以保存

保存后原文件删除不影响 Managed File

重复文件名不会冲突

文件可以检查 exists

文件可以删除

无法删除 Workspace 外文件

阻止 ../ 路径穿越
```

## API

```text
Workspace API 返回正确结构

错误返回遵守统一 Error Schema
```

---

# 21. 不允许提前实现

Phase 1 禁止实现：

```text
Project CRUD

Script CRUD

Scene CRUD

Shot CRUD

Asset Library UI

Character

Prompt

AI API

Storyboard

Video Result

Project Export
```

这些属于后续 Phase。

---

# 22. 本阶段完成标准

Phase 1 只有同时满足以下条件才算完成：

```text
1. SQLite 正常运行

2. Alembic migration 可 upgrade / downgrade

3. UUID Base Model 可复用

4. Timestamp / Soft Delete 基础存在

5. Bootstrap Config 能确定 Workspace Root

6. WorkspaceService 正常工作

7. Workspace 文件夹可自动初始化

8. StorageProvider 抽象存在

9. LocalStorageProvider 已实现核心文件操作

10. Storage 使用相对路径，不让业务层依赖绝对路径

11. 路径安全测试通过

12. Repository 基础边界建立

13. 统一异常结构建立

14. 全部既有 Phase 0 测试仍通过

15. Phase 1 新测试通过

16. README 更新

17. DEVELOPMENT_STATUS.md 更新
```

---

# 23. Phase 完成后的报告

完成后只报告：

```text
实现内容

主要目录 / 架构变化

Alembic 状态

Workspace 测试结果

Storage 测试结果

所有测试结果

已知限制

下一阶段建议
```

不要自动进入 Phase 2。

Phase 2 必须等待确认后再开始。

---

# 24. 特别注意

当前项目目标是：

```text
快速投入使用
+
长期可维护
```

因此本阶段不要为了“架构漂亮”加入：

```text
复杂 DDD Framework

Event Bus

CQRS

依赖注入框架

Redis

Celery

Docker 强依赖

微服务
```

保持：

```text
简单
清晰
有边界
可测试
可扩展
```

即可。
