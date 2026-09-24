import json
import os
from importlib.resources import files

import pytest


@pytest.mark.skipif(os.environ.get("RELEASE") != "1", reason="release-only guard")
def test_bundled_client_is_real():
    data = json.loads(
        files("health_data_connect").joinpath("data/google_client.json").read_text()
    )
    cid = data["installed"]["client_id"]
    assert "REPLACE_WITH" not in cid, "Refusing to publish with placeholder client credentials"
    assert cid.endswith(".apps.googleusercontent.com")
