"""Procedural loading accepts package keys without granting filesystem access."""

import pytest

from klaudia.core.skills.registry import SkillRegistry


@pytest.mark.parametrize(
    "name", ["../../README.md", "/etc/passwd", "resource-discovery.md", "unknown"]
)
def test_registry_rejects_arbitrary_paths_and_unknown_keys(name):
    """Only the exact registry keys can load content from the package."""
    with pytest.raises(ValueError, match="Unknown skill"):
        SkillRegistry().load(name)


def test_packaged_procedures_match_registry_versions():
    """Every advertised skill ships a nonempty procedure under its declared version."""
    registry = SkillRegistry()
    for description in registry.descriptions:
        loaded = registry.load(description.name)
        assert loaded["version"] == description.version
        assert loaded["content"].startswith("Procedure:")
        assert "Procedure:" not in description.description
