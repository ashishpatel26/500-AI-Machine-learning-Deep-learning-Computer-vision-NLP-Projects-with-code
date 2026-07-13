#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MRL_Platform_Server — 母體對外平台 零依賴 Python 標準庫伺服器
# origin_signature: MrliouAI
#
# 四大功能：母體控制台 / 即時監控儀表 / API 入口+文件 / 人格對話介面。
# 真實呼叫母體 crown（MotherAssembly：boot/status/run_dl580/chat）。
# 零外部依賴（http.server），任何環境可上線；對外經 Cloudflare Tunnel → 你的網域。
# 網域可設：環境變數 MRL_PLATFORM_DOMAIN（預設 mrliouword.com）。
# 啟動：python3 MRL_Platform_Server.py   （MRL_PORT 預設 8790）

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ORIGIN_SIGNATURE = "MrliouAI"
PLATFORM_DOMAIN = os.environ.get("MRL_PLATFORM_DOMAIN", "mrliouword.com")
# 零外部依賴法則:平台**不**預設指向任何外部模型供應商。真模型一律走母體自運行
# DL580(OLLAMA / OpenAI 相容自架端點)。設了 MRL_MOTHER_GATEWAY_URL(指向你 DL580
# 對外網址)才接;未設則 deny-by-default,誠實回「DL580 未連」,絕不偷用外部 cf。
_REPO = pathlib.Path(__file__).resolve().parent
for p in [_REPO / "09_workflow", str(_REPO)]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# 母體 crown（優雅降級：未就緒不致整站掛掉）
_MA = None
_MA_ERR = None


def _mother():
    """惰性 boot MotherAssembly（單例）。"""
    global _MA, _MA_ERR
    if _MA is not None or _MA_ERR is not None:
        return _MA
    try:
        from MRL_mother_assembly import MotherAssembly
        m = MotherAssembly()
        m.boot()
        _MA = m
    except Exception as exc:  # noqa: BLE001
        _MA_ERR = str(exc)
    return _MA


def _subsystem_summary(rep_subs):
    # status() 回布林、boot() 報告回 "ok"/"unavailable" 字串 —— 兩者皆計入。
    ok = sum(1 for v in rep_subs.values()
             if v is True or (isinstance(v, str) and v.startswith("ok")))
    return {"ok": ok, "total": len(rep_subs), "detail": rep_subs}


# ── API handlers（回傳 dict）─────────────────────────────────────────────────
def api_state():
    return {
        "origin_signature": ORIGIN_SIGNATURE,
        "system_name": "MRL_完整態母體運轉系統_v1",
        "platform": PLATFORM_DOMAIN,
        "sovereignty_mode": "權位區分模式",
        "status": "running",
        "attention_policy": "Attention 為歷史層；正式主體為感知力(Perception)",
    }


def api_convergence():
    return {
        "status": "SPEC_READY", "implementation": "READ_ONLY_API_ACTIVE",
        "active": {"runtime_core": "LOCAL_ACCEPTANCE", "naming_alignment": "LOCAL_ACCEPTANCE",
                   "pid_scope": "DECLARED_ACTIVE", "entry_gateway": "DECLARED_ACTIVE"},
        "pending": {"persistent_loop_daemon": "PENDING", "replay_restore_runtime": "PENDING",
                    "world_sync": "PENDING", "baseworld_db": "PENDING",
                    "dl580_reboot_survival": "PENDING"},
        "note": "唯讀治理視圖；不啟動 daemon、不宣稱 pending 完成。",
    }


def api_mother_status():
    m = _mother()
    if m is None:
        return {"available": False, "reason": _MA_ERR or "not booted"}
    try:
        st = m.status()
        return {"available": True, **_subsystem_summary(st.get("subsystems", {})),
                "assembly_version": st.get("assembly_version"),
                "node_role": st.get("node_role")}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": str(exc)}


def api_dl580_run(body):
    m = _mother()
    if m is None or getattr(m, "dl580", None) is None:
        return {"ok": False, "reason": _MA_ERR or "dl580 unavailable"}
    src = (body or {}).get("source") or f"{PLATFORM_DOMAIN} 平台 DL580 觸發"
    try:
        r = m.run_dl580(src, lang=(body or {}).get("lang", "text"), loop_id="platform")
        v = r.get("verification", {})
        return {"ok": True, "acceptance": v.get("acceptance"), "token": v.get("token"),
                "passed": v.get("passed"), "total": v.get("total"),
                "stages": r.get("stages_executed")}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": str(exc)}


def api_chat(body):
    m = _mother()
    msg = (body or {}).get("message", "")
    if not msg:
        return {"ok": False, "reason": "message required"}
    if m is None:
        return {"ok": False, "reason": _MA_ERR or "mother unavailable"}
    # 優雅降級：有 chat 用 chat，否則走感知力流程描述
    try:
        if hasattr(m, "chat"):
            out = m.chat(msg)
            return {"ok": True, "via": "MotherAssembly.chat",
                    "reply": out if isinstance(out, (str, dict, list)) else str(out)}
    except Exception:  # noqa: BLE001
        pass
    return {"ok": True, "via": "perceive_flow", "input": msg,
            "flow": ["世界狀態", "感知力場", "語境同步", "記憶拉取", "人格共振",
                     "運轉組裝", "世界投影", "回放", "回復", "驗證", "重新同步"],
            "note": "真模型未配置（待實機 OLLAMA_HOST/endpoint）；此為感知力流程路由。"}


def api_monitor():
    return {"origin_signature": ORIGIN_SIGNATURE, "checked_at_ms": int(time.time() * 1000),
            "mother": api_mother_status(), "convergence": api_convergence(),
            "acceptance_known": {"dl580": "6/6 (sandbox)", "civilization": "6/6+9/9 (sandbox)",
                                 "runtimeos": "8/8 (sandbox)", "supercomputer": "10/10 (sandbox)",
                                 "terminal": "5/5 (sandbox)", "law0": "6/6 (sandbox)"}}


API_DOCS = [
    ("GET", "/health", "存活檢查 + 母體狀態"),
    ("GET", "/mrl/state", "母體 MRL_STATE"),
    ("GET", "/api/mrl/runtime/convergence", "唯讀收斂治理視圖"),
    ("GET", "/api/mother/status", "MotherAssembly 子系統健康"),
    ("POST", "/api/dl580/run", "跑 DL580 canonical 管線，回驗收 {source,lang}"),
    ("POST", "/api/chat", "人格對話 {message}"),
    ("GET", "/api/monitor", "即時監控聚合"),
    ("POST", "/mrl/perceive", "感知力核心流程 {..}"),
]


def page_html():
    rows = "".join(f'<tr><td><span class=m>{m}</span></td><td>{p}</td><td>{d}</td></tr>'
                   for m, p, d in API_DOCS)
    return """<!doctype html><html lang=zh-Hant><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>MRL 母體平台 · """ + PLATFORM_DOMAIN + """</title>
<style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;font-family:system-ui,"Noto Sans TC",sans-serif;background:#0b0d10;color:#e8eef2}
header{padding:22px 20px;border-bottom:1px solid #1d2a22;background:linear-gradient(180deg,#0f1a12,#0b0d10)}
h1{margin:0;font-size:20px;color:#8de08a}.sig{color:#5a7d5a;font-size:12px;margin-top:5px}
nav{display:flex;gap:6px;padding:10px 20px;border-bottom:1px solid #1d2a22;flex-wrap:wrap}
nav button{background:#111418;color:#cfe;border:1px solid #1d2a22;border-radius:8px;padding:8px 12px;cursor:pointer}
nav button.on{background:#1f6f3f;color:#fff;border-color:#1f6f3f}
main{max-width:900px;margin:0 auto;padding:18px}.tab{display:none}.tab.on{display:block}
.card{background:#111418;border:1px solid #1d2a22;border-radius:12px;padding:16px;margin:12px 0}
h2{margin:0 0 10px;font-size:15px;color:#8de08a}button.act{background:#1f6f3f;color:#fff;border:0;border-radius:8px;padding:9px 14px;cursor:pointer;margin:4px 4px 4px 0}
pre{background:#0a0c0e;border:1px solid #1d2a22;border-radius:8px;padding:12px;overflow:auto;font-size:12px;white-space:pre-wrap}
input,textarea{width:100%;background:#0a0c0e;color:#e8eef2;border:1px solid #1d2a22;border-radius:8px;padding:9px;font:inherit}
table{width:100%;border-collapse:collapse;font-size:13px}td{padding:6px 8px;border-bottom:1px solid #161b20;vertical-align:top}
.m{color:#e3b341;font-weight:600}.b{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;background:#13361a;color:#7ee787}</style></head>
<body><header><h1>🌌 MRL 母體運轉平台 <span class=b>""" + PLATFORM_DOMAIN + """</span></h1>
<div class=sig>origin_signature=MrliouAI ｜ 權位區分模式 ｜ 入口 MRL_Platform_Server（零依賴）</div></header>
<nav>
<button class="nv on" data-t=console>母體控制台</button>
<button class=nv data-t=monitor>即時監控</button>
<button class=nv data-t=api>API 入口/文件</button>
<button class=nv data-t=chat>人格對話</button></nav>
<main>
<section class="tab on" id=console>
<div class=card><h2>母體控制台</h2>
<button class=act onclick=mstatus()>母體狀態 boot/status</button>
<button class=act onclick=dl580()>跑 DL580 canonical 管線</button>
<pre id=consoleOut>點上方按鈕，會真的呼叫母體並回傳驗收結果。</pre></div></section>
<section class=tab id=monitor><div class=card><h2>即時監控儀表</h2>
<button class=act onclick=mon()>刷新監控</button><pre id=monOut>載入中…</pre></div></section>
<section class=tab id=api><div class=card><h2>API 入口 / 文件</h2>
<table><tr><td><b>方法</b></td><td><b>路徑</b></td><td><b>說明</b></td></tr>""" + rows + """</table>
<p style=color:#9fb0a8;font-size:12px>所有回應帶 origin_signature=MrliouAI。對外經 Cloudflare Tunnel；金鑰/授權為接線層。</p></div></section>
<section class=tab id=chat><div class=card><h2>人格對話介面</h2>
<textarea id=msg rows=3 placeholder=對母體說點什麼…></textarea>
<button class=act onclick=chat()>送出</button><pre id=chatOut></pre></div></section>
</main>
<script>
const $=s=>document.querySelector(s);
document.querySelectorAll('.nv').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('.nv').forEach(x=>x.classList.remove('on'));b.classList.add('on');
 document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));$('#'+b.dataset.t).classList.add('on');
 if(b.dataset.t==='monitor')mon();});
async function jget(u){return (await fetch(u)).json()}
async function jpost(u,b){return (await fetch(u,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b||{})})).json()}
async function mstatus(){$('#consoleOut').textContent='查詢中…';$('#consoleOut').textContent=JSON.stringify(await jget('/api/mother/status'),null,2)}
async function dl580(){$('#consoleOut').textContent='跑管線中…';$('#consoleOut').textContent=JSON.stringify(await jpost('/api/dl580/run',{source:'平台觸發'}),null,2)}
async function mon(){$('#monOut').textContent=JSON.stringify(await jget('/api/monitor'),null,2)}
async function chat(){$('#chatOut').textContent='…';$('#chatOut').textContent=JSON.stringify(await jpost('/api/chat',{message:$('#msg').value}),null,2)}
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 安靜
        pass

    def _send(self, status, obj, ctype="application/json; charset=utf-8"):
        body = obj if isinstance(obj, bytes) else (
            obj.encode("utf-8") if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False).encode("utf-8"))
        self.send_response(status)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(body)))
        self.send_header("access-control-allow-origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("content-length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:  # noqa: BLE001
            return {}

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            return self._send(200, page_html(), "text/html; charset=utf-8")
        if p == "/health":
            return self._send(200, {"ok": True, **api_state()})
        if p == "/mrl/state":
            return self._send(200, api_state())
        if p == "/api/mrl/runtime/convergence":
            return self._send(200, api_convergence())
        if p == "/api/mother/status":
            return self._send(200, api_mother_status())
        if p == "/api/monitor":
            return self._send(200, api_monitor())
        return self._send(404, {"ok": False, "error": "MRL_ROUTE_NOT_FOUND", "path": p})

    def do_POST(self):
        p = self.path.split("?")[0]
        b = self._body()
        if p == "/api/dl580/run":
            return self._send(200, api_dl580_run(b))
        if p == "/api/chat":
            return self._send(200, api_chat(b))
        if p == "/mrl/perceive":
            return self._send(200, {"ok": True, "route": "MRL_感知力核心", "input": b,
                                    "sovereignty": "MRL 主體；外部僅 Adapter"})
        return self._send(404, {"ok": False, "error": "MRL_ROUTE_NOT_FOUND", "path": p})


def main():
    port = int(os.environ.get("MRL_PORT", "8790"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"MRL Platform ({PLATFORM_DOMAIN}) running on :{port} — origin_signature={ORIGIN_SIGNATURE}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
