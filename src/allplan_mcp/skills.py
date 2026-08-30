from __future__ import annotations

import importlib.resources
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any


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
            raise ValueError(
                f"Unknown script '{script_name}' for skill '{skill_name}'. "
                f"Available scripts: {available}"
            )
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
            raise ValueError(
                f"Unknown asset '{asset_name}' for skill '{skill_name}'. "
                f"Available assets: {available}"
            )
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

    def documents(self) -> list[dict[str, str]]:
        """List every readable skill document with its resource URI"""

        documents: list[dict[str, str]] = []
        for entry in self.entries.values():
            documents.append(
                {
                    "uri": f"allplan://skills/{entry.name}",
                    "skill": entry.name,
                    "kind": "skill",
                    "name": "SKILL.md",
                    "description": entry.description,
                }
            )
            for asset_name in entry.assets:
                documents.append(
                    {
                        "uri": f"allplan://skills/{entry.name}/assets/{asset_name}",
                        "skill": entry.name,
                        "kind": "asset",
                        "name": asset_name,
                        "description": "",
                    }
                )
            for script_name in entry.scripts:
                documents.append(
                    {
                        "uri": f"allplan://skills/{entry.name}/scripts/{script_name}",
                        "skill": entry.name,
                        "kind": "script",
                        "name": script_name,
                        "description": "",
                    }
                )
        return documents

    def document_text(self, document: dict[str, str]) -> str:
        """Read the text behind one document descriptor"""

        kind = document["kind"]
        if kind == "skill":
            return self.skill_text(document["skill"])
        if kind == "asset":
            return self.asset_text(document["skill"], document["name"])
        return self.script_text(document["skill"], document["name"])

    def read_uri(self, uri: str) -> str:
        """Read one bundled document by its allplan:// resource URI"""

        for document in self.documents():
            if document["uri"] == uri:
                return self.document_text(document)

        raise ValueError(
            f"Unknown skill resource '{uri}'. Call list_allplan_skills to see valid URIs."
        )

    def search(
        self,
        query: Annotated[str, "Free text query"],
        limit: Annotated[int, "Maximum hits"] = 5,
        context_lines: Annotated[int, "Lines of context per snippet"] = 2,
    ) -> list[dict[str, Any]]:
        """Rank bundled skill documents against a free text query

        Deliberately a plain term frequency scan with no index and no
        dependencies. The corpus is under a thousand lines, so the cost of
        scanning it is far below the cost of the model guessing at the Allplan
        API because it never read these files.
        """

        terms = [term for term in re.split(r"\W+", query.lower()) if len(term) > 2]
        if not terms:
            return []

        hits: list[dict[str, Any]] = []
        for document in self.documents():
            try:
                text = self.document_text(document)
            except (OSError, ValueError):
                continue

            haystack = text.lower()
            score = 0
            for term in terms:
                score += haystack.count(term)
                if term in document["name"].lower() or term in document["skill"].lower():
                    score += 5
                if term in document["description"].lower():
                    score += 3

            if score == 0:
                continue

            hits.append(
                {
                    **document,
                    "score": score,
                    "snippet": self.snippet(text, terms, context_lines),
                }
            )

        hits.sort(key=lambda hit: (-int(hit["score"]), str(hit["uri"])))
        return hits[:limit]

    def snippet(
        self,
        text: str,
        terms: list[str],
        context_lines: int,
    ) -> str:
        """Build a small excerpt around the best matching line"""

        lines = text.splitlines()
        best_index = 0
        best_score = -1
        for index, line in enumerate(lines):
            lowered = line.lower()
            score = sum(lowered.count(term) for term in terms)
            if score > best_score:
                best_score = score
                best_index = index

        if best_score <= 0:
            return "\n".join(lines[: context_lines * 2 + 1])

        start = max(0, best_index - context_lines)
        end = min(len(lines), best_index + context_lines + 1)
        return "\n".join(lines[start:end])
