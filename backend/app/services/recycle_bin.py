from app.models import Character, Project, Shot
from app.repositories.recycle_bin import RecycleBinRepository
from app.schemas.recycle_bin import RecycleBinItem, RecycleBinPage


class RecycleBinService:
    def __init__(self, session):
        self.repository = RecycleBinRepository(session)

    def list(self, entity_type=None, search=None, offset=0, limit=100):
        items = []
        for kind, row in self.repository.deleted(entity_type):
            project_id = getattr(row, "project_id", None)
            context = "Workspace"
            name = getattr(row, "name", None) or getattr(row, "title", None)
            if kind == "projects":
                project_id = row.id
            elif kind == "character-states":
                character = self.repository.get(Character, row.character_id)
                project_id = character.project_id if character else None
                context = character.name if character else "父角色缺失"
            elif kind in {"storyboards", "video-results"}:
                shot = self.repository.get(Shot, row.shot_id)
                project_id = shot.project_id if shot else None
                context = f"{shot.shot_code} · {shot.title}" if shot else "父镜头缺失"
                name = f"{'Storyboard' if kind == 'storyboards' else 'Video'} V{row.version}"
            elif kind == "shots":
                name = f"{row.shot_code} · {row.title}"
            project = self.repository.get(Project, project_id)
            if project:
                context = (
                    project.name
                    + ("（项目已删除，请先恢复）" if project.deleted_at else "")
                    + (f" / {context}" if context != "Workspace" else "")
                )
            item = RecycleBinItem(
                entity_type=kind,
                entity_id=row.id,
                display_name=name,
                deleted_at=row.deleted_at,
                project_id=project_id,
                context=context,
            )
            if not search or search.casefold() in f"{name} {context}".casefold():
                items.append(item)
        items.sort(key=lambda i: (i.deleted_at, i.entity_type, str(i.entity_id)), reverse=True)
        return RecycleBinPage(items=items[offset : offset + limit], total=len(items))
