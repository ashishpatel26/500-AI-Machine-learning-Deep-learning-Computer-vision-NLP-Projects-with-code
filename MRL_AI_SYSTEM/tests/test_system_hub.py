import os
import tempfile

from system_hub.mrl_system_hub import route, remember, recall, VAULT_LAYERS


def test_route_default_roles():
    roles = route("build me a new feature")
    assert roles[:3] == ["architect", "engineer", "reviewer"]


def test_route_bilingual_keywords():
    zh = route("修一下這個效能問題")
    en = route("optimize memory performance")
    assert "optimizer" in zh
    assert "optimizer" in en


def test_route_multi_keyword_dedup():
    roles = route("debug the ui bug and refactor")
    for r in ("debugger", "ui_builder", "refactorer"):
        assert r in roles
    assert len(roles) == len(set(roles))


def test_vault_remember_and_recall(monkeypatch):
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
    tmp.close()
    from system_hub import mrl_system_hub
    monkeypatch.setattr(mrl_system_hub, "DB_PATH", tmp.name)

    for layer in VAULT_LAYERS:
        mrl_system_hub.remember(layer, f"content for {layer}", key=layer)

    hits = mrl_system_hub.recall("content L4", top_k=3)
    assert hits
    assert all("distance" in h for h in hits)
    os.unlink(tmp.name)
