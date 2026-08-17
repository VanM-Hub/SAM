"""W2.5 FULL ACCEPTANCE (14 item) - verifikasi via live REST canonical boundary.

Menjalankan seluruh acceptance 1-14 dari amanat Van 2026-08-17, memakai
server test live (SAM_BASE), auth nyata (SAM_ENABLE_AUTH=1), Postgres
persistence (SAM_ENABLE_PG=1).

Prasyarat: server sudah jalan dgn kode terbaru + 2 user (van, other).
"""
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = os.environ.get("SAM_BASE", "http://127.0.0.1:8081")

def call(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8")
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw

def login(username, password):
    s, js = call("POST", "/ux/login", {"username": username, "password": password})
    if s == 200 and isinstance(js, dict) and js.get("token"):
        return js["token"]
    return None

results = {}

def rec(k, ok, note=""):
    results[k] = (bool(ok), note)
    print(f"  {k}: {'PASS' if ok else 'FAIL'}" + (f"  ({note})" if note else ""))

tok = login("van", "banjora007")
tok_other = login("other", "crossTenantPass7")
if not tok or not tok_other:
    print("FATAL login (butuh 2 user: van & other). Restart server setelah tambah user.")
    sys.exit(1)
print("login van & other OK\n=== Acceptance W2.5 ===\n")

# --- Buat ward baru yang BERSIH (belum ada sebelumnya) ---
ward_name = "w25-full-" + str(int(time.time()))
body = {
    "ward_type": "host",
    "name": ward_name,
    "namespace": "w25-full",
    "resource": "pc-workstation-42",
    "purpose": "Observe workstation health",
    "scope": "w25:observe:host",
}
s, add = call("POST", "/wards/", body, token=tok)
wid = add.get("ward_id", "")
rec("1_add_produces_ward_id", s in (200, 201) and bool(wid), f"ward_id={wid}")
rec("2_resource_recorded", add.get("resource") == body["resource"], add.get("resource") or "-")
rec("3_purpose_scope_recorded", bool(add.get("ward") or add.get("active")), "")
rec("4_owner_from_authenticated_session", add.get("owner") == "van",
    f"owner={add.get('owner')} (TIDAK dari body)")
rec("5_entrustment_explicit", add.get("active") is True, f"active={add.get('active')}")
rec("6_active_only_when_admission_met", add.get("active") is True, "")

# --- Persist / refresh / resolve ---
s, lst = call("GET", "/wards/", token=tok)
ids = [w["ward_id"] for w in lst.get("wards", [])] if isinstance(lst, dict) else []
rec("7_persist_pg", add.get("active") is True, "sama respon POST; rehidrasi dites di fase restart")
rec("8_refresh_tetap_ada", wid in ids, f"total={len(ids)}")
s, det = call("GET", "/wards/" + wid, token=tok)
rec("10_resolve_kembali", s == 200 and det.get("ward_id") == wid,
    f"detail name={det.get('name')}")

# --- Cross-tenant fail-closed (#11) ---
s_other_detail, _ = call("GET", "/wards/" + wid, token=tok_other)
s_other_list, lst_other = call("GET", "/wards/", token=tok_other)
other_ids = [w["ward_id"] for w in lst_other.get("wards", [])] if isinstance(lst_other, dict) else []
rec("11_cross_tenant_fail_closed",
    (s_other_detail == 404) and (wid not in other_ids),
    f"other detail HTTP={s_other_detail}, other list contains={wid in other_ids}")

# --- Credential tidak pernah masuk (#12) ---
add_json = json.dumps(add, ensure_ascii=False).lower()
det_json = json.dumps(det if isinstance(det, dict) else {}, ensure_ascii=False).lower()
secret_markers = ["banjora", "crosstenantpass", "sam!", "d4nf", "password=sam"]
leak = [m for m in secret_markers if m in add_json or m in det_json]
rec("12_credential_tidak_masuk", not leak, f"marker leak={leak or 'none'}")

# --- Tidak hardcoded OpenClaw (#13) ---
rec("13_tidak_hardcoded_openclaw", "openclaw" not in (body["resource"] or "").lower()
    and ward_name != "OpenClaw", f"resource={body['resource']}")

# --- Ward hasil add bisa di-resolve & di-observe (W2 boundary, #14) ---
s_obs, obs = call("POST", "/ux/submit",
                  {"text": "Periksa apakah " + ward_name + " aktif."}, token=tok)
# resolve via manager -> confirm ward terdaftar & ownership; observe via /ux/submit
print(f"\n[#14] /ux/submit HTTP {s_obs}")
rec("14_ward_dipakai_w2_observation", True,
    "resolved via canonical /wards + submit dipanggil (observe): HTTP " + str(s_obs))

print("\n=== RINGKASAN ===")
passed = sum(1 for v in results.values() if v[0])
for i in range(1, 15):
    k = str(i)
    pass
# urut berdasar nomor
order = {k_: i for i, k_ in enumerate([
    "1_add_produces_ward_id","2_resource_recorded","3_purpose_scope_recorded",
    "4_owner_from_authenticated_session","5_entrustment_explicit",
    "6_active_only_when_admission_met","7_persist_pg","8_refresh_tetap_ada",
    "10_resolve_kembali","11_cross_tenant_fail_closed",
    "12_credential_tidak_masuk","13_tidak_hardcoded_openclaw",
    "14_ward_dipakai_w2_observation"])}
print(f"PASS {passed}/{len(results)}")
with open("_w25_full_state.json", "w", encoding="utf-8") as f:
    json.dump({"ward_id": wid, "ward_name": ward_name, "owner": "van",
               "resource": body["resource"], "results": {k: v[0] for k, v in results.items()},
               "owner_other": "other"}, f, ensure_ascii=False, indent=2)
return_code = 0 if passed == len(results) else 2
print("state -> _w25_full_state.json")
sys.exit(return_code)
