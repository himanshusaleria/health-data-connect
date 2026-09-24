from pathlib import Path


def test_privacy_states_ondevice_and_readonly():
    txt = Path("site/privacy.html").read_text().lower()
    assert "read-only" in txt
    assert "on your device" in txt or "on your machine" in txt
    assert "no server" in txt or "do not operate" in txt


def test_homepage_links_privacy():
    assert "privacy.html" in Path("site/index.html").read_text()
