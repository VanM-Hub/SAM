"""E2E W3 LIVE browser-sim: cookie sesi (SAM_ENABLE_AUTH=1) via HTTP nyata :8090.

Meniru persis perilaku UI `postChatText`:
  - login (cookie httpOnly sam_session)
  - POST /ux/conversation/message "Periksa OpenClaw saya."  -> w3.pending=True, tombol
  - POST 'ya' (tombol Lanjutkan)  -> mission execute, evidence
  - percobaan kedua: ketik ulang -> w3.pending=True
  - POST 'tidak' (tombol Batalkan) -> dibatalkan, TANPA eksekusi (0 mutation)
Ranah: challenge-request tidak perlu CSRF di GET; POST mutation butuh CSRF token
(ambil dari /ux/me response csrf, kirim header X-CSRF-Token, pakai cookie).
"""
import io, sys, json, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
warnings.filterwarnings("ignore")
import urllib.request
import http.cookiejar

BASE = "http://127.0.0.1:8090"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def req(method, path, body=None, csrf=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if csrf:
        r.add_header("X-CSRF-Token", csrf)
    try:
        with opener.open(r, timeout=60) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw) if raw else {}
        except Exception:
            return e.code, {"raw": raw}


# 1) LOGIN (cookie)
st, d = req("POST", "/ux/login", {"username": "van", "password": "samw3pw"})
print("LOGIN:", st)
assert st == 200, d
print("  cookies:", [c.name for c in cj])

# /ux/me -> csrf + identitas
st, me = req("GET", "/ux/me")
print("ME:", st, "| user:", (me.get("user") or {}).get("username"), "| auth:", me.get("authenticated"))
csrf = me.get("csrf")
print("  csrf:", bool(csrf))
assert st == 200 and me.get("authenticated"), me

# 2) KETIK "Periksa OpenClaw saya."
st, r1 = req("POST", "/ux/conversation/message", {"text": "Periksa OpenClaw saya."}, csrf=csrf)
print("\n[1] PERINTAH:", st)
print("  w3:", r1.get("w3"))
w3 = r1.get("w3")
assert w3 and w3.get("pending") is True, f"w3={w3}"
assert w3.get("kind") == "read_only", f"kind={w3.get('kind')}"
assert w3.get("ward") == "OpenClaw"
cid = r1.get("conversation_id")
# UI tombol [Lanjutkan]/[Batalkan] akan tampil karena w3.read_only pending.
msgs = r1.get("messages") or []
print("  SAM:", msgs[-1]["content"][:180])
print("  >> UI menampilkan [Lanjutkan][Batalkan]")

# 3) KLIK LANJUTKAN -> kirim 'ya'
st, r2 = req("POST", "/ux/conversation/message", {"text": "ya", "conversation_id": cid}, csrf=csrf)
print("\n[2] LANJUTKAN ('ya'):", st)
print("  w3:", r2.get("w3"))
assert r2.get("w3") and r2.get("w3").get("pending") is False
stt = r2.get("mission_state") or {}
ev = stt.get("evidence") or []
print("  status (execution):", (stt.get("execution") or {}).get("status"))
print("  evidence:", [(e.get('kind'), e.get('runtime_status'), e.get('component_count')) for e in ev])
assert any(e.get("kind") == "openclaw_ward_observation" for e in ev), "harus evidence openclaw_ward_observation"
# read-only -> tanpa mutation (0 eksekusi eksternal selain observasi read)
print("  >> mission dieksekusi, OpenClaw diobservasi, evidence openclaw_ward_observation")

# 4) PERCOBAAN KEDUA -> BATALKAN
st, r3 = req("POST", "/ux/conversation/message", {"text": "Periksa OpenClaw saya."}, csrf=csrf)
print("\n[3] PERINTAH KEDUA:", st)
w3b = r3.get("w3")
assert w3b and w3b.get("pending") is True, f"w3={w3b}"
cid2 = r3.get("conversation_id")
print("  w3:", w3b, ">> UI menampilkan [Lanjutkan][Batalkan]")
st, r4 = req("POST", "/ux/conversation/message", {"text": "tidak", "conversation_id": cid2}, csrf=csrf)
print("\n[4] BATALKAN ('tidak'):", st)
print("  w3:", r4.get("w3"))
stt4 = r4.get("mission_state") or {}
# Batalkan -> tidak ada eksekusi, mission_state kosong/proyeksi
print("  status (execution):", (stt4.get("execution") or {}))
op = (stt4.get("understanding") or {}).get("operation")
print("  operation:", op)
assert r4.get("w3") and r4.get("w3").get("pending") is False
# tidak boleh ada eksekusi: operation kosong / tidak ada evidence eksekusi
assert op in ("", None), f"tidak boleh ada eksekusi, operation={op}"
print("  >> dibatalkan, TANPA eksekusi (0 mutation)")

print("\n=== LIVE BROWSER-SIM W3: ALL PASS ===")
