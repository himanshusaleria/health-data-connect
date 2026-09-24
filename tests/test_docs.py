from pathlib import Path


def test_readme_covers_unverified_warning():
    txt = Path("README.md").read_text()
    assert "unverified" in txt.lower()
    assert "Advanced" in txt  # the click-through path users get stuck on
    assert "uvx health-data-connect auth" in txt


def test_operator_setup_flags_placeholder_swap():
    txt = Path("docs/operator-setup.md").read_text()
    assert "REPLACE_WITH_REAL_CLIENT_ID" in txt
    assert "Desktop app" in txt
