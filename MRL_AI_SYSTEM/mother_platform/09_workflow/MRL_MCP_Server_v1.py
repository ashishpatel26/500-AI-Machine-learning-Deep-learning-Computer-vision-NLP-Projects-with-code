#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_MCP_Server_v1.py — 母體對外 MCP 閘口（rl_13 出口即入口 / rl_19 MCP 基座)
origin_signature: MrliouAI
layer: L0 ROOT (出入口) + L4 WORLD

把母體能力(MotherAssembly)暴露為 Model Context Protocol 工具,讓任何 MCP 客戶端
(Claude Desktop / IDE / 其他 agent)能接進母體 —— 母體成為可被呼叫的標準閘口。

設計:
  - 零外部依賴:純 stdlib,JSON-RPC 2.0 over stdio(MCP 標準傳輸)。
  - 出口即入口(rl_13):同一個 server,initialize/tools/list(出)、tools/call(入)同門。
  - 經海關(rl_11):每個 tool 結果帶 origin_signature,溯源歸母體。
  - no_proof:母體未就緒時誠實回錯,不偽造。

MCP 方法:initialize / tools/list / tools/call / ping
工具:mother_status / mother_chat / dl580_run / law_engine_loop

啟動:python3 09_workflow/MRL_MCP_Server_v1.py   (讀 stdin 的 JSON-RPC,寫 stdout)
"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrliouAI"
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "MRL_Mother_MCP"
SERVER_VERSION = "1.0.0"

# ── 工具定義（暴露給 MCP 客戶端的能力清單）─────────────────────────────────────
TOOLS: List[Dict[str, Any]] = [
    {
        "name": "mother_status",
        "description": "母體健康狀態:子系統、rootlaw 版本、node 角色。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "mother_chat",
        "description": "與母體對話。deny-by-default:無真引擎/未開 mock 會誠實回錯,不偽造。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "對話訊息"},
                "session_id": {"type": "string", "description": "可選,延續既有 session"},
            },
            "required": ["message"],
        },
    },
    {
        "name": "dl580_run",
        "description": "跑 DL580 canonical 運轉管線,回驗收 token。",
        "inputSchema": {
            "type": "object",
            "properties": {"source": {"type": "string"}, "lang": {"type": "string"}},
            "required": ["source"],
        },
    },
    {
        "name": "law_engine_loop",
        "description": "跑母體律法活引擎一次閉環自驗(Observe→Resolve→Mirror→Verify→Loop)。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
]


class MRL_MCPServer:
    """母體 MCP 閘口。惰性 boot 母體,JSON-RPC over stdio。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self._mother = None
        self._mother_err: Optional[str] = None

    # 惰性 boot(優雅降級:母體未就緒不致 server 崩潰)
    def _mom(self):
        if self._mother is not None or self._mother_err is not None:
            return self._mother
        try:
            import os
            here = os.path.dirname(os.path.abspath(__file__))
            if here not in sys.path:
                sys.path.insert(0, here)
            from MRL_mother_assembly import MotherAssembly
            m = MotherAssembly()
            m.boot()
            self._mother = m
        except Exception as exc:  # noqa: BLE001
            self._mother_err = str(exc)
        return self._mother

    # ── MCP 方法分派 ───────────────────────────────────────────────────────────
    def handle(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = req.get("method")
        rid = req.get("id")
        # notifications(無 id)不回應
        if method == "initialize":
            return self._ok(rid, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION,
                               "origin_signature": ORIGIN_SIGNATURE},
            })
        if method == "ping":
            return self._ok(rid, {})
        if method in ("notifications/initialized", "initialized"):
            return None
        if method == "tools/list":
            return self._ok(rid, {"tools": TOOLS})
        if method == "tools/call":
            return self._tools_call(rid, req.get("params", {}))
        if rid is not None:
            return self._err(rid, -32601, f"method not found: {method}")
        return None

    def _tools_call(self, rid: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        args = params.get("arguments", {}) or {}
        try:
            result = self._dispatch_tool(name, args)
        except Exception as exc:  # noqa: BLE001 — 誠實回錯,不偽造
            return self._err(rid, -32603, f"{type(exc).__name__}: {exc}")
        # 出口即入口:結果帶母體簽章溯源(rl_11)
        if isinstance(result, dict):
            result.setdefault("origin_signature", ORIGIN_SIGNATURE)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        return self._ok(rid, {"content": [{"type": "text", "text": text}],
                              "isError": False})

    def _dispatch_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        m = self._mom()
        if m is None:
            return {"error": f"mother unavailable: {self._mother_err or 'not booted'}"}
        if name == "mother_status":
            st = m.status()
            return {"booted": st.get("booted"), "rootlaw_version": st.get("rootlaw_version"),
                    "node_role": st.get("node_role"),
                    "subsystems_ok": sum(1 for v in st.get("subsystems", {}).values() if v),
                    "subsystems_total": len(st.get("subsystems", {}))}
        if name == "mother_chat":
            msg = args.get("message", "")
            if not msg:
                return {"error": "message required"}
            return m.chat(msg, session_id=args.get("session_id"))
        if name == "dl580_run":
            if getattr(m, "dl580", None) is None:
                return {"error": "dl580 unavailable"}
            r = m.run_dl580(args.get("source", "MCP trigger"), lang=args.get("lang", "text"))
            v = r.get("verification", {})
            return {"acceptance": v.get("acceptance"), "token": v.get("token"),
                    "passed": v.get("passed"), "total": v.get("total")}
        if name == "law_engine_loop":
            if getattr(m, "law_engine", None) is None:
                return {"error": "law_engine unavailable"}
            rep = m.law_engine.self_acceptance()
            return {"verified": rep.get("verified"), "token": rep.get("token"),
                    "rootlaw_version": rep.get("mirror", {}).get("rootlaw_version")}
        return {"error": f"unknown tool: {name}"}

    # ── JSON-RPC 包裝 ──────────────────────────────────────────────────────────
    @staticmethod
    def _ok(rid: Any, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    @staticmethod
    def _err(rid: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}

    # ── stdio 主迴圈(MCP 標準傳輸:一行一個 JSON-RPC 訊息)──────────────────────
    def serve_stdio(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                sys.stdout.write(json.dumps(self._err(None, -32700, "parse error")) + "\n")
                sys.stdout.flush()
                continue
            resp = self.handle(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()


def main() -> int:
    MRL_MCPServer().serve_stdio()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
