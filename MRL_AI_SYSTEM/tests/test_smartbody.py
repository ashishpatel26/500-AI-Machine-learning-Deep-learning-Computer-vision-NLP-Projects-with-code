from smartbody_v2.mrl_smartbody import sense_self, sense_system, evaluate_reflex


def test_sense_self_contains_pid():
    out = sense_self()
    assert "pid" in out
    assert out["origin_signature"] == "MrliouAI"


def test_sense_system_has_disk():
    out = sense_system()
    # On Linux/CI we should get loadavg + disk; both must be present as keys
    assert "disk" in out
    assert "loadavg" in out


def test_reflex_ping_hits():
    hit = evaluate_reflex("ping now")
    assert hit is not None
    assert hit["brain"] is False


def test_reflex_unknown_delegates_to_brain():
    hit = evaluate_reflex("please refactor the module")
    assert hit is None
