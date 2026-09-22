from app.models.characters import (
    CharacterAssetLink,
    CharacterStateAssetLink,
    ShotCharacterStateLink,
)
from app.repositories.characters import CharacterRepository, CharacterStateRepository
from app.repositories.workflow import WorkflowRepository


class CharacterLifecycle:
    """Used inside the owner's atomic transaction. Deleted links require explicit rebind."""

    def __init__(self, session):
        self.session = session
        self.characters = CharacterRepository(session)
        self.states = CharacterStateRepository(session)

    def detach(self, model, timestamp, **filters):
        repo = WorkflowRepository(self.session, model)
        for link in repo.matching(**filters):
            repo.mark_deleted(link, timestamp)

    def delete_state(self, state, timestamp):
        self.detach(CharacterStateAssetLink, timestamp, character_state_id=state.id)
        self.detach(ShotCharacterStateLink, timestamp, character_state_id=state.id)
        self.states.mark_deleted(state, timestamp)

    def delete_character(self, character, timestamp):
        for state in self.states.matching(character_id=character.id):
            self.delete_state(state, timestamp)
        self.detach(CharacterAssetLink, timestamp, character_id=character.id)
        self.characters.mark_deleted(character, timestamp)

    def delete_project(self, project_id, timestamp):
        for character in self.characters.matching(project_id=project_id):
            self.delete_character(character, timestamp)

    def delete_shot(self, shot_id, timestamp):
        self.detach(ShotCharacterStateLink, timestamp, shot_id=shot_id)

    def restore_character(self, character):
        timestamp = character.deleted_at
        if timestamp is None:
            return
        self.characters.restore(character)
        for state in self.states.matching(character_id=character.id, include_deleted=True):
            if state.deleted_at == timestamp:
                self.states.restore(state)
        self.normalize(character.id)

    def restore_project(self, project_id, timestamp):
        for character in self.characters.matching(project_id=project_id, include_deleted=True):
            if character.deleted_at == timestamp:
                self.restore_character(character)

    def normalize(self, character_id):
        for index, state in enumerate(self.states.matching(character_id=character_id)):
            self.states.update(state, order_index=index)
