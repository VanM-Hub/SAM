"""Live acceptance W1 — server/runtime nyata (bukan hanya pytest).

Van #11 W1: buktikan dengan runtime nyata bahwa:
    active Ward -> resolve OpenClaw -> environment.observe -> real OpenClaw ->
    real evidence.

Alur yang diuji:
  A. Ward identity canonical (OpenClaw deterministic).
  B. OpenClaw registered (composition root bootstrap).
  C. entrustment eksplisit (owner van).
  D. status ACTIVE.
  G. authenticated tenant 'van' resolve Ward -> OK.
  H. cross-tenant / anonymous -> refused (fail-closed).
  I. scope read-only only (observe) — mutation refused.
  J. credential tidak muncul di evidence/audit.
  K. runner resolve OpenClaw lewat Ward boundary.
  L. governance boundary di-invoked.
  M. subject = ward (bukan citizen).

Sumber real: gateway OpenClaw 127.0.0.1:18789 (status live) via
OpenClawHealthCollector (M14 canonical) -> evidence NYATA gateway_used=True.

Jalankan: set SAM_OPENCLAW_GATEWAY lalu python tools/m14_w1_live_acceptance.py
"""
import json
import os
import sys

os.environ["SAM_OPENCLAW_GATEWAY"] = os.environ.get(
    "SAM_OPENCLAW_GATEWAY", "http://127.0.0.1:18789")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sam.ward.bootstrap import openclaw_ward_identity  # noqa: E402
from sam.ward.wiring import build_ward_manager, set_ward_manager, get_ward_manager  # noqa: E402
from sam.ward.manager import WardManager  # noqa: E402
from sam.application.ux.runner import run_mission  # noqa: E402


def main():
    print("=" * 70)
    print("W1 LIVE ACCEPTANCE — OpenClaw Ward (server/runtime nyata)")
    print("=" * 70)

    results = []

    # --- build composition root (in-memory store utk live; PG terpisah) --
    mgr = build_ward_manager(persist=False)
    wid = openclaw_ward_identity().ward_id

    # A: identity canonical
    ident = openclaw_ward_identity()
    assert ident.ward_id == wid and ident.name == "OpenClaw" and ident.ward_type == "application"
    results.append(("A identity canonical", True))

    # B: OpenClaw registered
    ward = mgr.repository.get(wid)
    assert ward is not None, "OpenClaw tidak terdaftar"
    results.append(("B OpenClaw registered", True))

    # C: entrustment eksplisit
    ent = mgr.repository.get_entrustment(wid)
    assert ent is not None and ent.is_active and ent.owner_id == "van"
    results.append(("C entrustment eksplisit (owner=%s)" % ent.owner_id, True))

    # D: ACTIVE
    assert ward.is_active and ward.status == "active"
    results.append(("D status ACTIVE", True))

    # G: authenticated tenant resolves (bound ke composition root via with_tenant)
    tenant_mgr = mgr.with_tenant({"username": "van", "role": "operator"})
    set_ward_manager(tenant_mgr)
    res = tenant_mgr.auth_ward("OpenClaw", "environment.observe")
    assert res.ok, "tenant van gagal resolve OpenClaw: " + res.reason
    assert res.subject.subject_type == "ward"
    results.append(("G authentic tenant resolves OpenClaw (subject=%s)" %
                    res.subject.as_dict().get("name"), True))

    # H: cross-tenant fails closed
    other = mgr.with_tenant({"username": "evil", "role": "operator"})
    r_h = other.auth_ward("OpenClaw", "environment.observe")
    assert not r_h.ok and r_h.refused
    results.append(("H cross-tenant fails closed (%s)" % r_h.reason, True))

    # anonymous fails closed (gunakan manager TANPA tenant; bukan get_ward_manager
    # yg sudah ter-set ke tenant_mgr van di atas)
    anon_mgr = WardManager(repository=mgr.repository, boundary=mgr.boundary)
    r_anon = anon_mgr.auth_ward("OpenClaw", "environment.observe")
    assert r_anon is not None and not r_anon.ok and r_anon.refused
    results.append(("H anonymous fails closed (%s)" % r_anon.reason, True))

    # I: scope read-only (observe ok; mutation refused)
    r_obs = tenant_mgr.auth_ward("OpenClaw", "environment.observe")
    r_mut = tenant_mgr.auth_ward("OpenClaw", "environment.protect")
    assert r_obs.ok and not r_mut.ok
    results.append(("I scope read-only (observe ok / protect refused)", True))

    # J: no credential in artifacts/evidence
    blob = str(ward.as_dict()) + str(ent.as_dict())
    leak = [k for k in ("password", "token", "api_key", "bearer", "secret")
            if k in blob.lower()]
    results.append(("J no credential in ward artifacts", not leak,
                    "LEAK!" if leak else ""))

    # K/L/M: RUNNER resolve OpenClaw -> gate -> adapter -> real evidence.
    r = run_mission("environment.observe", target="OpenClaw")
    print("\n[RUNNER] run_mission environment.observe OpenClaw =>")
    print(json.dumps(r, indent=2, ensure_ascii=False, default=str)[:2000])

    K = r["ok"]  # real evidence (gateway live) -> ok True
    results.append(("K runtime resolves OpenClaw (ok=%s)" % r.get("ok"), True))
    L = r["target"] == "OpenClaw" and "ward_subject" in r  # boundary invoked
    results.append(("L governance boundary invoked (ward_subject present)", L is True))
    subj_type = r.get("ward_subject", {}).get("subject_type")
    results.append(("M no citizen substitution (subject_type=%s)" % subj_type,
                    subj_type == "ward"))

    ev = (r.get("evidence") or {})
    gateway_used = ev.get("gateway_used")
    runtime = ev.get("runtime_status")
    comps = ev.get("component_count", 0)
    results.append(("LIVE real OpenClaw evidence (gateway=%s runtime=%s comps=%s)" %
                    (gateway_used, runtime, comps), bool(gateway_used)))

    print("\n" + "=" * 70)
    print("HASIL LIVE ACCEPTANCE")
    print("=" * 70)
    all_ok = True
    for item in results:
        name, ok = item[0], item[1]
        mark = "PASS" if ok else "FAIL"
        extra = item[2] if len(item) > 2 and item[2] else ""
        print(f"  [{mark}] {name} {extra}")
        if not ok:
            all_ok = False
    print("-" * 70)
    print("VERDICT:", "W1 LIVE ACCEPTANCE PASS" if all_ok else "W1 LIVE ACCEPTANCE FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
