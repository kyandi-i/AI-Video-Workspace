from app.models.assets import ShotAssetLink
from app.repositories.characters import CharacterLinkRepository
from app.schemas.shot_workspace import ShotWorkspaceRead
from app.services.assets import AssetService
from app.services.characters import CharacterService
from app.services.workflow import SceneService, ShotService


class ShotWorkspaceService(ShotService):
    def get_workspace(self, identifier):
        shot = self.shot(identifier)
        ordered = self.list_shots(shot.project_id)
        index = next(i for i, item in enumerate(ordered) if item.id == shot.id)
        return ShotWorkspaceRead(
            shot=shot,
            scene=SceneService(self.session).read(self.scene(shot.scene_id)),
            character_states=CharacterService(self.session).list_shot_states(shot.id),
            assets=AssetService(self.session).read_many(
                CharacterLinkRepository(self.session, ShotAssetLink).assets(shot_id=shot.id)
            ),
            previous_shot=ordered[index - 1] if index else None,
            next_shot=ordered[index + 1] if index + 1 < len(ordered) else None,
            position=index + 1,
            total=len(ordered),
        )
