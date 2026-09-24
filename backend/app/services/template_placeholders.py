"""The sole placeholder registry and a non-recursive, plain-text renderer."""

import re
from collections.abc import Mapping

from app.core.exceptions import AppError

PLACEHOLDERS = [
    {"key": key, "label": label, "description": description, "group": group, "example": example}
    for key, label, description, group, example in (
        ("shot_code", "Shot Code", "镜头编号", "Shot", "S13"),
        ("shot_title", "Shot Title", "镜头标题", "Shot", "风淋"),
        ("shot_description", "Shot Description", "镜头描述", "Shot", "人员通过风淋室。"),
        ("duration_seconds", "Duration", "镜头时长（秒）", "Shot", "10"),
        ("main_action", "Main Action", "镜头主要动作", "Shot", "人物进入风淋室，站定并抬起双臂。"),
        ("key_constraints", "Key Constraints", "镜头必须满足的约束", "Shot", "保持服装一致。"),
        (
            "negative_constraints",
            "Negative Constraints",
            "镜头禁止内容",
            "Shot",
            "不要添加多余人物。",
        ),
        ("free_notes", "Free Notes", "镜头自由补充", "Shot", "固定机位。"),
        ("scene_name", "Scene Name", "场景名称", "Scene", "风淋室"),
        ("scene_description", "Scene Description", "场景描述", "Scene", "明亮的洁净区域。"),
        (
            "scene_fixed_constraints",
            "Scene Fixed Constraints",
            "场景固定约束",
            "Scene",
            "保持门的位置。",
        ),
        (
            "scene_negative_constraints",
            "Scene Negative Constraints",
            "场景禁止内容",
            "Scene",
            "无杂物。",
        ),
        (
            "characters_context",
            "Characters Context",
            "角色及状态汇总文本",
            "Characters",
            "员工：黄色防护服。",
        ),
        (
            "reference_assets_context",
            "Reference Assets Context",
            "参考资产描述汇总",
            "Assets",
            "风淋室参考图：双门结构。",
        ),
        (
            "shot_context",
            "Shot Context",
            "镜头聚合上下文文本",
            "Aggregated Context",
            "S13 风淋 · 10秒\n员工进入风淋室。",
        ),
    )
]
KEYS = frozenset(p["key"] for p in PLACEHOLDERS)
TOKEN = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
SAMPLE_CONTEXT = {p["key"]: p["example"] for p in PLACEHOLDERS}


def validate_content(content: str) -> None:
    unknown = sorted({m.group(1).strip() for m in TOKEN.finditer(content)} - KEYS)
    remainder = TOKEN.sub("", content)
    if "{{" in remainder or "}}" in remainder:
        unknown.append("Unclosed or unmatched placeholder braces")
    if unknown:
        raise AppError(
            "INVALID_TEMPLATE_PLACEHOLDER",
            "Unknown placeholder: " + ", ".join(unknown),
            400,
            {"unknown_placeholders": unknown},
        )


def render_content(content: str, context: Mapping[str, str | int | float | None]) -> str:
    validate_content(content)

    def replace(match):
        value = context.get(match.group(1).strip())
        return "" if value is None else str(value)

    return TOKEN.sub(replace, content)
