# -*- coding: utf-8 -*-
"""E2E verifikasi register via server test nyata (auth aktif)."""
import os, sys, json, time, urllib.request, urllib.error, http.client, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def req(method, path, body=None, token=None, cookie=None):
    url = f"http://127.0.0.1:{PORT}{path}"
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token: r.add_header("Authorization", f"Bearer {token}")
    if cookie: r.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(r, timeout=8) as resp:
            raw = resp.read().decode('utf-8')
            return resp.status, json.loads(raw) if raw else None, resp.headers.get('Set-Cookie')
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8')
        try: j = json.loads(raw)
        except Exception: j = raw
        return e.code, j, e.headers.get('Set-Cookie')

PORT = int(os.environ.get("T_PORT", "8081"))

# 1. /ux/me tanpa token -> 401 (auth aktif)
st, j, _ = req("GET", "/ux/me")
print(f"[1] /ux/me tanpa token -> {st} (harus 401)"); assert st == 401, j

# 2. register user baru
st, j, ck = req("POST", "/ux/register", {"username": "e2e_user", "password": "e2e-pass-1"})
print(f"[2] /ux/register e2e_user -> {st} created={j and j.get('created')} user={j and j.get('user')}")
assert st == 200 and j["created"] is True
assert ck and "sam_session=" in ck, "harus set cookie httpOnly"

# 3. auto-login via session cookie -> /ux/me authenticated
cookie = ck.split(";")[0]
st, j, _ = req("GET", "/ux/me", cookie=cookie)
print(f"[3] /ux/me pakai cookie -> {st} authenticated={j and j.get('authenticated')} user={j and j.get('user')}")
assert st == 200 and j["authenticated"] is True and j["user"]["username"] == "e2e_user"

# 4. register duplikat -> 409
st, j, _ = req("POST", "/ux/register", {"username": "e2e_user", "password": "e2e-pass-2"})
print(f"[4] /ux/register duplikat -> {st} (harus 409)")
assert st == 409

# 5. register password pendek -> 400
st, j, _ = req("POST", "/ux/register", {"username": "short", "password": "123"})
print(f"[5] /ux/register password pendek -> {st} (harus 400)")
assert st == 400

# 6. login dengan user baru (persist ke file)
st, j, ck2 = req("POST", "/ux/login", {"username": "e2e_user", "password": "e2e-pass-1"})
print(f"[6] /ux/login e2e_user -> {st} user={j and j.get('user')}")
assert st == 200 and j["user"]["username"] == "e2e_user"

print("\nSEMUA E2E PASS ✔")
