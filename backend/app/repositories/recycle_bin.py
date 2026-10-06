from sqlalchemy import select

from app.models import (
    Asset,
    Character,
    CharacterState,
    Project,
    PromptTemplate,
    Scene,
    Script,
    Shot,
    Storyboard,
    VideoResult,
)

SUPPORTED = {
    "projects": Project,
    "scripts": Script,
    "scenes": Scene,
    "shots": Shot,
    "assets": Asset,
    "characters": Character,
    "character-states": CharacterState,
    "prompt-templates": PromptTemplate,
    "storyboards": Storyboard,
    "video-results": VideoResult,
}


class RecycleBinRepository:
    def __init__(self, session):
        self.session = session

    def deleted(self, entity_type=None):
        return [
            (kind, row)
            for kind, model in SUPPORTED.items()
            if entity_type is None or kind == entity_type
            for row in self.session.scalars(select(model).where(model.deleted_at.is_not(None)))
        ]

    def get(self, model, identifier):
        return self.session.get(model, identifier) if identifier else None
