import json
import os
from pathlib import Path

from trace_chain import emit, merkle_root, verify


def test_emit_and_verify_chain(tmp_path):
    journal = tmp_path / "j.jsonl"
    os.environ["MRL_TRACE_JOURNAL"] = str(journal)
    from trace_chain import mrl_trace
    mrl_trace.DEFAULT_JOURNAL = str(journal)

    r1 = emit("test.one", {"a": 1}, layer="L0", journal=str(journal))
    r2 = emit("test.two", {"b": 2}, layer="L3", journal=str(journal))

    assert r1["prev_hash"] == "GENESIS"
    assert r2["prev_hash"] == r1["chain_hash"]

    result = verify(str(journal))
    assert result["ok"], result
    assert result["records"] == 2
    assert result["root"] != "EMPTY"


def test_tamper_detection(tmp_path):
    journal = tmp_path / "j.jsonl"
    from trace_chain import mrl_trace
    emit("a", {"x": 1}, layer="L0", journal=str(journal))
    emit("b", {"x": 2}, layer="L0", journal=str(journal))

    lines = journal.read_text().splitlines()
    tampered = json.loads(lines[0])
    tampered["payload"]["x"] = 999
    lines[0] = json.dumps(tampered)
    journal.write_text("\n".join(lines) + "\n")

    result = verify(str(journal))
    assert not result["ok"]
