from __future__ import annotations

import pytest

from allplan_mcp.skills import SkillsManager


@pytest.fixture(scope="module")
def skills() -> SkillsManager:
    return SkillsManager()


def test_bundled_skills_are_discovered(skills: SkillsManager) -> None:
    assert set(skills.entries) == {
        "api-reference",
        "architecture",
        "geometry",
        "rebar",
        "utilities",
    }


def test_the_architecture_skill_is_searchable_for_walls(skills: SkillsManager) -> None:
    # The model reaches for create_box unless something tells it walls are
    # tiered objects. This is that something.
    hits = skills.search("wall Schraffur tier", limit=3)

    assert any(hit["uri"].startswith("allplan://skills/architecture") for hit in hits)


def test_every_skill_has_a_description(skills: SkillsManager) -> None:
    assert all(entry.description for entry in skills.entries.values())


def test_documents_cover_skills_assets_and_scripts(skills: SkillsManager) -> None:
    kinds = {document["kind"] for document in skills.documents()}

    assert kinds == {"skill", "asset", "script"}


def test_every_document_uri_is_readable(skills: SkillsManager) -> None:
    for document in skills.documents():
        assert skills.read_uri(document["uri"]).strip()


def test_unknown_uri_names_the_discovery_tool(skills: SkillsManager) -> None:
    with pytest.raises(ValueError, match="list_allplan_skills"):
        skills.read_uri("allplan://skills/nope")


class TestSearch:
    def test_finds_the_rebar_skill(self, skills: SkillsManager) -> None:
        hits = skills.search("rebar bending shape")

        assert hits
        assert hits[0]["skill"] == "rebar"
        assert hits[0]["snippet"]

    def test_finds_geometry_for_a_solid_query(self, skills: SkillsManager) -> None:
        hits = skills.search("polyhedron cuboid solid")

        assert {hit["skill"] for hit in hits} & {"geometry"}

    def test_hits_are_ranked_by_score(self, skills: SkillsManager) -> None:
        hits = skills.search("placement")
        scores = [hit["score"] for hit in hits]

        assert scores == sorted(scores, reverse=True)

    def test_respects_the_limit(self, skills: SkillsManager) -> None:
        assert len(skills.search("allplan", limit=2)) <= 2

    def test_returns_uris_that_read_back(self, skills: SkillsManager) -> None:
        for hit in skills.search("reinforcement"):
            assert skills.read_uri(str(hit["uri"])).strip()

    def test_short_and_empty_queries_return_nothing(
        self, skills: SkillsManager
    ) -> None:
        assert skills.search("") == []
        assert skills.search("a of") == []

    def test_nonsense_query_returns_nothing(self, skills: SkillsManager) -> None:
        assert skills.search("zzzqqqxxyy") == []


class TestPathSafety:
    @pytest.mark.parametrize("name", ["../const.py", "..", ".hidden", "sub/dir.py"])
    def test_rejects_traversal_in_script_names(
        self, skills: SkillsManager, name: str
    ) -> None:
        with pytest.raises(ValueError):
            skills.script_path("geometry", name)

    @pytest.mark.parametrize("name", ["../SKILL.md", ".hidden", "a/b.md"])
    def test_rejects_traversal_in_asset_names(
        self, skills: SkillsManager, name: str
    ) -> None:
        with pytest.raises(ValueError):
            skills.asset_path("geometry", name)

    def test_unknown_skill_lists_the_available_ones(
        self, skills: SkillsManager
    ) -> None:
        with pytest.raises(ValueError, match="Available skills"):
            skills.skill_entry("nope")
