from __future__ import annotations

import importlib.resources
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated


def skills_root() -> Path:
    """Return the bundled skills root"""
    root = importlib.resources.files("allplan_mcp").joinpath("allplan_skills")
    return Path(str(root))


def skill_description(skill_file: Path) -> str:
    """Read the skill description from frontmatter"""
    try:
        content = skill_file.read_text(encoding="utf-8")
    except OSError:
        return ""

    text = content.lstrip("\ufeff")
    if not text.startswith("---"):
        return ""

    parts = text.split("---", 2)
    if len(parts) < 3:
        return ""

    for line in parts[1].splitlines():
        current = line.strip()
        if current.startswith("description:"):
            return current.removeprefix("description:").strip().strip('"').strip("'")
    return ""


@dataclass(frozen=True)
class SkillEntry:
    """Hold one skill folder"""

    name: str
    description: str
    skill_file: Path
    assets_dir: Path
    assets: tuple[str, ...]
    scripts_dir: Path
    scripts: tuple[str, ...]


class SkillsManager:
    """Read bundled skill files and scripts"""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or skills_root()
        self.entries: dict[str, SkillEntry] = {}
        self.scan()

    def scan(self) -> None:
        """Index bundled skills"""
        self.entries.clear()
        if not self.root.is_dir():
            return

        for child in sorted(self.root.iterdir()):
            skill_file = child / "SKILL.md"
            assets_dir = child / "assets"
            scripts_dir = child / "scripts"
            if not child.is_dir() or not skill_file.is_file() or not scripts_dir.is_dir():
                continue

            assets = (
                tuple(
                    asset.name
                    for asset in sorted(assets_dir.iterdir())
                    if asset.is_file() and asset.suffix == ".md"
                )
                if assets_dir.is_dir()
                else ()
            )
            scripts = tuple(
                script.name
                for script in sorted(scripts_dir.iterdir())
                if script.is_file() and script.suffix == ".py"
            )
            self.entries[child.name] = SkillEntry(
                name=child.name,
                description=skill_description(skill_file),
                skill_file=skill_file,
                assets_dir=assets_dir,
                assets=assets,
                scripts_dir=scripts_dir,
                scripts=scripts,
            )

    def skill_entry(self, skill_name: Annotated[str, "Skill folder name"]) -> SkillEntry:
        """Resolve one skill"""
        entry = self.entries.get(skill_name)
        if entry is None:
            available = ", ".join(sorted(self.entries)) or "none"
            raise ValueError(f"Unknown skill '{skill_name}'. Available skills: {available}")
        return entry

    def script_path(
        self,
        skill_name: Annotated[str, "Skill folder name"],
        script_name: Annotated[str, "Script file name"],
    ) -> Path:
        """Resolve one sample script"""
        entry = self.skill_entry(skill_name)
        if "/" in script_name or script_name.startswith("."):
            raise ValueError("Invalid script name")
        if script_name not in entry.scripts:
            available = ", ".join(entry.scripts) or "none"
            raise ValueError(f"Unknown script '{script_name}' for skill '{skill_name}'. Available scripts: {available}")
        return entry.scripts_dir / script_name

    def asset_path(
        self,
        skill_name: Annotated[str, "Skill folder name"],
        asset_name: Annotated[str, "Asset file name"],
    ) -> Path:
        """Resolve one asset file"""
        entry = self.skill_entry(skill_name)
        if "/" in asset_name or asset_name.startswith("."):
            raise ValueError("Invalid asset name")
        if asset_name not in entry.assets:
            available = ", ".join(entry.assets) or "none"
            raise ValueError(f"Unknown asset '{asset_name}' for skill '{skill_name}'. Available assets: {available}")
        return entry.assets_dir / asset_name

    def index_text(self) -> str:
        """Build the skill index"""
        lines = [
            "# ALLPLAN skills",
            "",
            "These skills are exposed through MCP resources",
            "Read the skill first, then read asset notes, then read sample scripts when needed",
            "",
            "## Skills",
            "",
        ]

        for entry in self.entries.values():
            lines.append(f"- `{entry.name}`")
            lines.append(f"  - {entry.description}")
            lines.append(f"  - Resource: `allplan://skills/{entry.name}`")
            if entry.assets:
                lines.append("  - Assets:")
                for asset_name in entry.assets:
                    lines.append(f"    - `allplan://skills/{entry.name}/assets/{asset_name}`")
            else:
                lines.append("  - Assets: none")
            if entry.scripts:
                lines.append("  - Scripts:")
                for script_name in entry.scripts:
                    lines.append(f"    - `allplan://skills/{entry.name}/scripts/{script_name}`")
            else:
                lines.append("  - Scripts: none")
        return "\n".join(lines)

    def skill_text(self, skill_name: Annotated[str, "Skill folder name"]) -> str:
        """Read one skill file"""
        return self.skill_entry(skill_name).skill_file.read_text(encoding="utf-8")

    def asset_text(
        self,
        skill_name: Annotated[str, "Skill folder name"],
        asset_name: Annotated[str, "Asset file name"],
    ) -> str:
        """Read one asset file"""
        return self.asset_path(skill_name, asset_name).read_text(encoding="utf-8")

    def script_text(
        self,
        skill_name: Annotated[str, "Skill folder name"],
        script_name: Annotated[str, "Script file name"],
    ) -> str:
        """Read one sample script"""
        return self.script_path(skill_name, script_name).read_text(encoding="utf-8")
