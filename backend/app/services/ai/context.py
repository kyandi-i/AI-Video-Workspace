from app.services.shot_workspace import ShotWorkspaceService
from app.services.template_placeholders import PLACEHOLDERS


def text(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return format(value, ".15g")
    return str(value)


def block(pairs):
    return "\n".join(f"{label}: {text(value)}" for label, value in pairs if text(value))


def assets_context(assets):
    return "\n\n".join(
        block(
            [
                ("Asset", a.name),
                ("ID", a.id),
                ("Type", a.asset_type.value),
                ("Description", a.description),
                ("File", a.original_filename),
                ("Tags", ", ".join(sorted(t.name for t in a.tags))),
                ("Width", a.width),
                ("Height", a.height),
                ("Duration seconds", a.duration_seconds),
            ]
        )
        for a in sorted(assets, key=lambda a: str(a.id))
    )


def build_shot_context(session, shot_id):
    workspace = ShotWorkspaceService(session).get_workspace(shot_id)
    shot, scene = workspace.shot, workspace.scene
    context = {
        "shot_code": shot.shot_code,
        "shot_title": shot.title,
        "shot_description": shot.description,
        "duration_seconds": text(shot.duration_seconds),
        **{
            k: text(getattr(shot, k))
            for k in ("main_action", "key_constraints", "negative_constraints", "free_notes")
        },
        "scene_name": scene.name,
        "scene_description": scene.description,
        "scene_fixed_constraints": scene.fixed_constraints,
        "scene_negative_constraints": scene.negative_constraints,
        "characters_context": "\n\n".join(
            block(
                [
                    ("Character", s.character_name),
                    ("Character ID", s.character_id),
                    ("Character description", s.character_description),
                    ("Character notes", s.character_notes),
                    ("State", s.name),
                    ("State ID", s.id),
                    ("State description", s.description),
                    ("Character assets", assets_context(s.character_assets)),
                    ("State assets", assets_context(s.assets)),
                ]
            )
            for s in sorted(
                workspace.character_states, key=lambda s: (str(s.character_id), str(s.id))
            )
        ),
        "reference_assets_context": assets_context(workspace.assets),
    }
    context = {k: text(v) for k, v in context.items()}
    context["shot_context"] = block(
        [(p["label"], context[p["key"]]) for p in PLACEHOLDERS if p["key"] != "shot_context"]
        + [("Legacy creative requirement", shot.creative_requirement)]
    )
    return workspace.shot, context
