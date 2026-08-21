"""dashboard.py — Executive Access Control Interface (Tier 3 / Executive only).

Part of the unified security/access_control module.  Serves:

    GET /api/exec/access-control        → JSON snapshot of the monitored
                                          control surface + gateway status
    GET /api/exec/access-control/incidents → recent access-denied audit feed
    GET /api/exec/access-control/ui     → self-contained executive dashboard
                                          (HTML + vanilla JS, no build step)

Every endpoint is hard-gated behind the AccessGateway (Executive tier).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse

from .tiers import ACCESS_TIERS, registry_snapshot, rbac_hierarchy, _pattern_matches

logger = logging.getLogger("lcewai.access_control")

router = APIRouter(tags=["access-control"])

_gateway = None  # AccessGateway — bound by server.py before include_router


def bind(gateway) -> None:
    global _gateway
    _gateway = gateway


async def _require_executive(authorization: Optional[str] = Header(None)):
    """Hard dependency: Executive tier only (403 + audit log otherwise)."""
    gw = _gateway
    if gw is None:
        raise HTTPException(503, "Access control gateway not initialized")
    return await gw.authorize(authorization, "executive_access_control")


@router.get("/exec/access-control")
async def access_control_overview(user=Depends(_require_executive)):
    """Full registry snapshot with live firewall status and denial counts."""
    gw = _gateway
    stats = await gw.denial_stats(limit=500) if gw else {}

    controls = []
    for c in registry_snapshot():
        s = stats.get(c["key"], {})
        declared = c.get("routes") or []
        covered = 0
        for route in declared:
            methods, pattern = (route if isinstance(route, tuple) else (None, route))
            allowed_methods = set(methods) if isinstance(methods, (list, tuple, set, frozenset)) else None
            if isinstance(methods, str):
                allowed_methods = {methods}
            matches = [
                (method, live_pattern)
                for (method, live_pattern) in (gw._handler_requirements if gw else {})
                if (allowed_methods is None or method in allowed_methods)
                and _pattern_matches(pattern, live_pattern)
            ]
            if matches:
                covered += 1
        if not (gw and gw.active):
            firewall_status = "UNPROTECTED"
        elif not declared or covered == 0:
            firewall_status = "REGISTERED_UNVERIFIED"
        elif covered < len(declared):
            firewall_status = "PARTIAL"
        else:
            firewall_status = "ENFORCED"
        controls.append({
            **c,
            "firewall_status": firewall_status,
            "route_coverage": {"declared": len(declared), "verified": covered},
            "denials": s.get("denials", 0),
            "last_denied_at": s.get("last_denied_at"),
        })

    by_tier: dict = {}
    for c in controls:
        t = c["required_tier"]
        by_tier[t] = by_tier.get(t, 0) + 1

    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gateway": {
            "active": bool(gw and gw.active),
            "module": "backend/security/access_control",
            "tiers": {
                key: {k: v for k, v in t.items() if k not in ("roles",)} | {"roles": list(t["roles"])}
                for key, t in ACCESS_TIERS.items()
            },
        },
        "rbac": {
            "roles": rbac_hierarchy(),
            "note": "Canonical 7-role RBAC from backend/roles.py — compliance tiers are a derived view.",
        },
        "summary": {
            "controls": len(controls),
            "categories": len({c["category"] for c in controls}),
            "by_tier": by_tier,
            "total_denials": sum(c["denials"] for c in controls),
        },
        "controls": controls,
    }


@router.get("/exec/control/route-access")
async def route_access_overview(user=Depends(_require_executive)):
    """Return the complete authenticated route matrix from the live app."""
    if _gateway is None:
        raise HTTPException(503, "Access control gateway not initialized")
    return {
        "ok": True,
        "routes": await _gateway.route_access_snapshot(),
        "roles": [role for role, _rank in rbac_hierarchy() if role != "public"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.patch("/exec/control/route-access")
async def set_route_access(payload: dict, user=Depends(_require_executive)):
    """Set or reset one discovered route's exact allowed-role policy.

    The handler's own minimum role can never be loosened. Executive control
    routes also cannot be delegated below executive_admin, preventing the
    policy editor from granting away the keys that administer the policy.
    """
    if _gateway is None:
        raise HTTPException(503, "Access control gateway not initialized")
    route_key = (payload.get("route_key") or "").strip()
    if not route_key or " " not in route_key:
        raise HTTPException(400, "route_key must be '<HTTP_METHOD> <path_pattern>'")
    method, path_pattern = route_key.split(" ", 1)
    method = method.upper()
    entry = _gateway._handler_requirements.get((method, path_pattern))
    if entry is None:
        raise HTTPException(404, "Route is not in the live authenticated route table")

    allowed_roles = payload.get("allowed_roles")
    if allowed_roles is not None:
        if not isinstance(allowed_roles, list) or any(
            not isinstance(role, str) or role == "public" for role in allowed_roles
        ):
            raise HTTPException(400, "allowed_roles must contain stored RBAC role names")
        valid_roles = {role for role, _rank in rbac_hierarchy() if role != "public"}
        unknown = set(allowed_roles) - valid_roles
        if unknown:
            raise HTTPException(400, f"Unknown role(s): {sorted(unknown)}")

    enabled = payload.get("enabled", True)
    if not isinstance(enabled, bool):
        raise HTTPException(400, "enabled must be boolean")
    protected_admin_route = path_pattern.startswith(("/api/exec/control", "/api/exec/access-control"))
    if protected_admin_route and (not enabled or "executive_admin" not in (allowed_roles or ["executive_admin"])):
        raise HTTPException(400, "Executive control routes must remain enabled for executive_admin")

    now = datetime.now(timezone.utc).isoformat()
    if allowed_roles is None and enabled:
        result = await _gateway._db.route_access.delete_one({"route_key": route_key})
        action = "reset"
    else:
        result = await _gateway._db.route_access.update_one(
            {"route_key": route_key},
            {"$set": {
                "route_key": route_key,
                "method": method,
                "path_pattern": path_pattern,
                "allowed_roles": allowed_roles,
                "enabled": enabled,
                "updated_by": user.id,
                "updated_at": now,
            }},
            upsert=True,
        )
        action = "updated"
    await _gateway._audit_fn(
        user.id, f"exec.route_access.{action}", target=route_key,
        meta={"allowed_roles": allowed_roles, "enabled": enabled},
    )
    return {"ok": True, "route_key": route_key, "allowed_roles": allowed_roles,
            "enabled": enabled, "policy_source": "handler_default" if action == "reset" else "executive_override"}


@router.get("/exec/control/user-route-access")
async def user_route_access_overview(
    user_id: str = Query(..., min_length=1),
    actor=Depends(_require_executive),
):
    """Return per-user route overrides plus the handler defaults.

    The route matrix controls role access; this endpoint is the explicit
    per-user exception layer.  It is read from the same live route table, not
    from a hand-maintained feature list.
    """
    if _gateway is None or _gateway._db is None:
        raise HTTPException(503, "Access control gateway not initialized")
    target = await _gateway._db.users.find_one(
        {"id": user_id}, {"_id": 0, "id": 1, "email": 1, "full_name": 1, "role": 1, "feature_tier": 1}
    )
    if not target:
        raise HTTPException(404, "User not found")
    overrides = await _gateway._db.user_route_access.find(
        {"user_id": user_id}, {"_id": 0}
    ).to_list(length=10000)
    return {
        "ok": True,
        "user": target,
        "overrides": overrides,
        "routes": await _gateway.route_access_snapshot(),
    }


@router.patch("/exec/control/user-route-access")
async def set_user_route_access(payload: dict, actor=Depends(_require_executive)):
    """Set or reset one user's access to any discovered authenticated route."""
    if _gateway is None or _gateway._db is None:
        raise HTTPException(503, "Access control gateway not initialized")
    user_id = (payload.get("user_id") or "").strip()
    route_key = (payload.get("route_key") or "").strip()
    if not user_id or not route_key or " " not in route_key:
        raise HTTPException(400, "user_id and route_key '<HTTP_METHOD> <path_pattern>' are required")
    target = await _gateway._db.users.find_one({"id": user_id}, {"_id": 0, "id": 1})
    if not target:
        raise HTTPException(404, "User not found")
    method, path_pattern = route_key.split(" ", 1)
    method = method.upper()
    if (method, path_pattern) not in _gateway._handler_requirements:
        raise HTTPException(404, "Route is not in the live authenticated route table")
    protected_admin_route = path_pattern.startswith(("/api/exec/control", "/api/exec/access-control"))
    if not payload.get("enabled") and protected_admin_route:
        raise HTTPException(400, "Per-user overrides cannot disable executive control routes")
    enabled = payload.get("enabled")
    if not isinstance(enabled, bool):
        raise HTTPException(400, "enabled must be boolean")
    reason = (payload.get("reason") or "").strip()
    if not reason:
        raise HTTPException(400, "reason is required")
    now = datetime.now(timezone.utc).isoformat()
    await _gateway._db.user_route_access.update_one(
        {"user_id": user_id, "route_key": route_key},
        {"$set": {
            "user_id": user_id,
            "route_key": route_key,
            "method": method,
            "path_pattern": path_pattern,
            "enabled": enabled,
            "updated_by": actor.id,
            "updated_at": now,
            "reason": reason,
        }},
        upsert=True,
    )
    await _gateway._audit_fn(
        actor.id, "exec.user_route_access.updated", target=user_id,
        meta={"route_key": route_key, "enabled": enabled, "reason": reason},
    )
    return {"ok": True, "user_id": user_id, "route_key": route_key, "enabled": enabled}


@router.delete("/exec/control/user-route-access")
async def reset_user_route_access(
    user_id: str = Query(..., min_length=1),
    route_key: str = Query(..., min_length=3),
    actor=Depends(_require_executive),
):
    """Remove a per-user exception and restore the role/handler policy."""
    if _gateway is None or _gateway._db is None:
        raise HTTPException(503, "Access control gateway not initialized")
    result = await _gateway._db.user_route_access.delete_one(
        {"user_id": user_id, "route_key": route_key}
    )
    if result.deleted_count == 0:
        raise HTTPException(404, "User route override not found")
    await _gateway._audit_fn(
        actor.id, "exec.user_route_access.reset", target=user_id,
        meta={"route_key": route_key},
    )
    return {"ok": True, "user_id": user_id, "route_key": route_key, "policy_source": "role_or_handler_default"}


@router.get("/exec/access-control/incidents")
async def access_control_incidents(
    limit: int = Query(50, ge=1, le=200),
    user=Depends(_require_executive),
):
    """Recent access-denied audit entries — the compliance trail."""
    gw = _gateway
    rows = await gw.recent_denials(limit=limit) if gw else []
    incidents = []
    for row in rows:
        meta = row.get("meta") or {}
        incidents.append({
            "at": row.get("at"),
            "actor_id": row.get("actor_id"),
            "control": meta.get("control"),
            "control_label": meta.get("control_label"),
            "path": meta.get("path"),
            "method": meta.get("method"),
            "reason": meta.get("reason"),
            "user_role": meta.get("user_role"),
            "user_tier": meta.get("user_tier"),
            "required_tier": meta.get("required_tier"),
        })
    return {"ok": True, "incidents": incidents}


@router.get("/exec/access-control/ui", response_class=HTMLResponse)
async def access_control_ui(user=Depends(_require_executive)):
    """The master Executive interface (Tier 3 only)."""
    return HTMLResponse(content=_UI_HTML)


_UI_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WAI · Executive Access Control</title>
<style>
  :root{
    --bg:#0b0e1a; --panel:#12172a; --panel2:#171d36; --line:#232b4d;
    --ink:#e8eaf6; --dim:#8b93b5; --gold:#d4af37; --amber:#f5b942;
    --green:#3ddc97; --red:#ff5d73; --blue:#5aa9ff; --mono:"SF Mono",Consolas,Menlo,monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;padding:32px 20px 60px}
  .wrap{max-width:1180px;margin:0 auto}
  header{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:22px}
  h1{font-size:22px;letter-spacing:.5px}
  h1 .mark{color:var(--gold)}
  .sub{color:var(--dim);font-size:12.5px;margin-top:4px}
  .hdr-right{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
  .badge{font:11px var(--mono);padding:5px 10px;border-radius:999px;border:1px solid var(--line);color:var(--dim);background:var(--panel)}
  .badge.ok{color:var(--green);border-color:rgba(61,220,151,.4)}
  .badge.off{color:var(--red);border-color:rgba(255,93,115,.4)}
  .btn{font:12px var(--mono);padding:6px 12px;border-radius:6px;border:1px solid var(--gold);color:var(--gold);background:transparent;cursor:pointer}
  .btn:hover{background:rgba(212,175,55,.12)}
  .tiers{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0 22px}
  .tier{flex:1;min-width:170px;border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:var(--panel)}
  .tier .lv{font:11px var(--mono);color:var(--gold)}
  .tier .nm{font-weight:600;margin-top:2px}
  .tier .rl{color:var(--dim);font-size:11.5px;margin-top:4px;font-family:var(--mono)}
  .sec{margin:26px 0 10px;font-size:13px;text-transform:uppercase;letter-spacing:1.5px;color:var(--amber)}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px}
  .card{border:1px solid var(--line);border-radius:10px;background:var(--panel);padding:13px 14px;display:flex;flex-direction:column;gap:8px}
  .card .top{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}
  .card h3{font-size:13.5px}
  .card .src{color:var(--dim);font:10.5px var(--mono);margin-top:1px}
  .pill{font:10.5px var(--mono);padding:3px 8px;border-radius:999px;white-space:nowrap}
  .pill.t3{background:rgba(212,175,55,.14);color:var(--gold);border:1px solid rgba(212,175,55,.45)}
  .pill.t2{background:rgba(90,169,255,.12);color:var(--blue);border:1px solid rgba(90,169,255,.4)}
  .pill.t1{background:rgba(61,220,151,.1);color:var(--green);border:1px solid rgba(61,220,151,.35)}
  .pill.t0{background:rgba(139,147,181,.1);color:var(--dim);border:1px solid var(--line)}
  .fw{font:10.5px var(--mono);display:flex;gap:6px;align-items:center}
  .fw .dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 6px var(--green)}
  .fw .dot.off{background:var(--red);box-shadow:0 0 6px var(--red)}
  .routes{font:10.5px var(--mono);color:var(--dim);background:var(--panel2);border:1px solid var(--line);border-radius:6px;padding:6px 8px;word-break:break-all}
  .meta{display:flex;gap:12px;font:10.5px var(--mono);color:var(--dim)}
  .meta .den{color:var(--red)}
  table{width:100%;border-collapse:collapse;font-size:12px}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
  th{color:var(--dim);font-size:10.5px;text-transform:uppercase;letter-spacing:1px}
  td{font-family:var(--mono);font-size:11.5px}
  .red{color:var(--red)} .dim{color:var(--dim)} .gold{color:var(--gold)}
  .tok{display:flex;gap:8px;margin:14px 0}
  .tok input{flex:1;background:var(--panel2);border:1px solid var(--line);color:var(--ink);border-radius:6px;padding:8px 10px;font:12px var(--mono)}
  .rbac{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 4px;padding:11px 13px;border:1px solid var(--line);border-radius:10px;background:var(--panel);align-items:center}
  .rbac .lbl{font:10.5px var(--mono);color:var(--dim);margin-right:8px}
  .chip{font:11px var(--mono);padding:5px 9px;border-radius:6px;border:1px solid var(--line);color:var(--dim);background:var(--panel2)}
  .chip b{color:var(--gold)}
  .chip.base{opacity:.5}
  .chip.hi{color:var(--gold);border-color:rgba(212,175,55,.45)}
  #status{font:11.5px var(--mono);color:var(--dim)}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1><span class="mark">◆</span> WAI · EXECUTIVE ACCESS CONTROL</h1>
      <div class="sub">Unified Access Control Interface · Tier 3 only · backend/security/access_control</div>
    </div>
    <div class="hdr-right">
      <span id="status" class="badge">…</span>
      <button class="btn" onclick="load()">⟳ Refresh</button>
    </div>
  </header>

  <div class="tok">
    <input id="tok" type="password" placeholder="Paste a Bearer token (or it is read from the URL ?token= / localStorage)">
    <button class="btn" onclick="applyToken()">Apply</button>
  </div>

  <div class="sec">▸ Canonical RBAC — 7 roles</div>
  <div id="rbac" class="rbac"></div>
  <div id="tiers" class="tiers"></div>
  <div id="summ" style="color:var(--dim);font:12px var(--mono);margin-bottom:4px"></div>
  <div id="cats"></div>

  <div class="sec">▸ Recent Access Denials — Audit Trail</div>
  <div style="overflow-x:auto"><table id="incs"><thead>
    <tr><th>Time (UTC)</th><th>Control</th><th>Path</th><th>Reason</th><th>User tier → required</th></tr>
  </thead><tbody></tbody></table></div>
</div>
<script>
(function(){
  const TOKEN_KEYS=["token","lcewai_token","jwt","access_token"];
  let TOKEN=null;
  function loadToken(){
    const q=new URLSearchParams(location.search).get("token");
    if(q) return q;
    for(const k of TOKEN_KEYS){try{const v=localStorage.getItem(k); if(v) return v;}catch(e){}}
    return null;
  }
  function store(){ const el=document.getElementById("tok"); if(TOKEN) el.value=TOKEN; }
  window.applyToken=function(){ TOKEN=(document.getElementById("tok").value||"").trim(); if(TOKEN){try{localStorage.setItem("lcewai_token",TOKEN);}catch(e){}} load(); };
  function H(){ return TOKEN?{"Authorization":"Bearer "+TOKEN} :{}; }
  async function j(url){ const r=await fetch(url,{headers:H()}); if(!r.ok){ throw new Error(r.status+" "+ (await r.text()).slice(0,140)); } return r.json(); }
  function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
  window.load=async function(){
    const st=document.getElementById("status");
    try{
      const d=await j("/api/exec/access-control");
      st.className="badge ok"; st.textContent="GATEWAY ACTIVE · "+d.summary.controls+" controls · "+d.summary.total_denials+" denials";
      const rbac=document.getElementById("rbac"); rbac.innerHTML='<span class="lbl">ROLE → RANK</span>';
      (d.rbac.roles||[]).forEach(r=>{
        rbac.insertAdjacentHTML("beforeend",
          '<span class="chip'+(r.rank===7?' hi':'')+(r.stored?'':' base')+'">'+esc(r.role)+' <b>'+r.rank+'</b></span>');
      });
      rbac.insertAdjacentHTML("beforeend",'<span class="lbl" style="margin-left:auto">'+esc(d.rbac.note||"")+'</span>');
      const tiers=document.getElementById("tiers"); tiers.innerHTML="";
      Object.values(d.gateway.tiers).forEach(t=>{
        tiers.insertAdjacentHTML("beforeend",
          '<div class="tier"><div class="lv">TIER '+t.level+' · MIN ROLE '+esc(t.min_role)+'</div><div class="nm">'+esc(t.label)+'</div><div class="rl">'+t.roles.map(esc).join(" · ")+'</div></div>');
      });
      document.getElementById("summ").textContent=
        d.summary.controls+" monitored controls · "+d.summary.categories+" categories · enforced by ASGI middleware + per-route gate";
      const cats=document.getElementById("cats"); cats.innerHTML="";
      const byCat={}; d.controls.forEach(c=>{(byCat[c.category]=byCat[c.category]||[]).push(c);});
      Object.entries(byCat).forEach(([cat,list])=>{
        cats.insertAdjacentHTML("beforeend",'<div class="sec">▸ '+esc(cat)+'</div><div class="grid">'+list.map(c=>{
          const pill=c.required_tier_level===3?"t3":c.required_tier_level===2?"t2":c.required_tier_level===1?"t1":"t0";
          return '<div class="card"><div class="top"><div><h3>'+esc(c.label)+'</h3><div class="src">'+esc(c.source)+'</div></div>'+
            '<span class="pill '+pill+'">'+esc(c.required_tier_label)+'</span></div>'+
            '<div class="fw"><span class="dot'+(c.firewall_status==="ENFORCED"?"":" off")+'"></span>'+
            esc(c.firewall_status)+(c.min_role?' · min '+esc(c.min_role):"")+'</div>'+
            '<div class="routes">'+c.routes.map(esc).join("<br>")+'</div>'+
            '<div class="meta"><span class="den">'+c.denials+' denials</span>'+(c.last_denied_at?'<span>last '+esc(c.last_denied_at).slice(0,19)+'</span>':"")+'</div></div>';
        }).join("")+'</div>');
      });
      const inc=await j("/api/exec/access-control/incidents?limit=40");
      const tb=document.querySelector("#incs tbody"); tb.innerHTML="";
      if(!inc.incidents.length) tb.innerHTML='<tr><td colspan="5" class="dim">No access denials recorded. The firewall is holding.</td></tr>';
      inc.incidents.forEach(i=>{
        tb.insertAdjacentHTML("beforeend",
          '<tr><td class="dim">'+esc((i.at||"").slice(0,19))+'</td><td>'+esc(i.control_label||i.control||"")+'</td>'+
          '<td class="dim">'+esc(i.method||"")+" "+esc(i.path||"")+'</td><td class="red">'+esc(i.reason||"")+'</td>'+
          '<td class="dim">'+esc(i.user_tier||"—")+' → '+esc(i.required_tier||"—")+'</td></tr>');
      });
    }catch(e){
      st.className="badge off"; st.textContent="ACCESS DENIED / ERROR · "+esc(e.message);
    }
  };
  TOKEN=loadToken(); store(); if(TOKEN) load(); else load();
})();
</script>
</body>
</html>
"""
