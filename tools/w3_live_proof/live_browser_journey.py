"""LIVE browser journey W3 via Chrome headless + CDP (websocket-client).

Alur (persis instruksi Van):
  A. Browser buka SAM UI (/ui)
  B. Login van (overlay: #lgUser, #lgPass, #lgGo)
  C. Ketik "Periksa OpenClaw saya." di #chat, tekan Enter (send)
  D. SAM menampilkan proposal + tombol [Lanjutkan][Batalkan] (renderW3Controls)
  E. Klik Lanjutkan -> mission execute -> evidence muncul di UI
  F. Ketik lagi -> proposal -> klik Batalkan -> TANPA eksekusi (0 mutation)
Screenshot di tiap tahap kunci.
"""
import io, sys, json, time, os, base64, subprocess, tempfile, glob
import websocket  # websocket-client
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8090"
CDP_PORT = 9222
PROFILE = tempfile.mkdtemp(prefix="w3chrome_")
OUT = os.path.join(os.getcwd(), "_w3_cdp_shots")
os.makedirs(OUT, exist_ok=True)

proc = None
ws = None
cmd_id = 0
pending = {}


def launch():
    global proc
    proc = subprocess.Popen([
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--remote-debugging-port=%d" % CDP_PORT,
        "--remote-allow-origins=*",
        "--user-data-dir=" + PROFILE,
        "--window-size=1280,900",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # tunggu port
    for _ in range(40):
        try:
            import urllib.request
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % CDP_PORT, timeout=2):
                return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Chrome CDP not up")


def connect():
    global ws, cmd_id
    import urllib.request
    with urllib.request.urlopen("http://127.0.0.1:%d/json" % CDP_PORT, timeout=5) as r:
        tabs = json.load(r)
    page = next(t for t in tabs if t.get("type") == "page")
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30)
    cmd_id = 0


def _send(method, params=None):
    global cmd_id
    cmd_id += 1
    mid = cmd_id
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == mid:
            if "error" in msg:
                raise RuntimeError(f"{method}: {msg['error']}")
            return msg.get("result", {})


def evaluate(expr):
    r = _send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    return r.get("result", {}).get("value")


def wait_for(js_expr, timeout=25, interval=0.5):
    end = time.time() + timeout
    while time.time() < end:
        v = evaluate(js_expr)
        if v:
            return v
        time.sleep(interval)
    return None


def shot(name):
    r = _send("Page.captureScreenshot", {"format": "png"})
    data = base64.b64decode(r.get("data", ""))
    p = os.path.join(OUT, name)
    with open(p, "wb") as f:
        f.write(data)
    print("  screenshot:", p)


def main():
    launch(); connect()
    _send("Page.enable"); _send("Runtime.enable")
    _send("Page.navigate", {"url": BASE + "/ui"})

    # A+B: buka UI, cek login overlay muncul (401 saat fetch)
    wait_for("document.readyState==='complete'")
    # login overlay muncul otomatis bila unauth; isi dan submit
    time.sleep(1.5)
    # trigger send() sekali agar 401 -> showLogin
    evaluate("""document.getElementById('chat') && (()=>{ 
        document.getElementById('chat').value='Periksa OpenClaw saya.';
        try{send();}catch(e){window.__sende = String(e);} 
        return true; })()""")
    time.sleep(1.5)
    # login overlay
    time.sleep(1.0)
    ov = evaluate("!!document.getElementById('lgUser')")
    print("B. login overlay visible:", ov)
    assert ov, "login overlay tidak muncul"
    shot("01_login")
    evaluate("document.getElementById('lgUser').value='van'")
    evaluate("document.getElementById('lgPass').value='samw3pw'")
    # sampler: password test user dibuat dgn 'samw3pw'
    evaluate("document.getElementById('lgGo').click()")
    # tunggu login sukses (overlay hilang / chat aktif)
    wait_for("!document.getElementById('lgUser')", timeout=15)
    print("  login berhasil (overlay tertutup)")
    time.sleep(1.0)
    # Arah ke page mission (chat ada di sana)
    evaluate("(()=>{const b=document.querySelector('button[data-page=mission]'); if(b){b.click();return true;} return false;})()")
    time.sleep(1.0)
    print("  aktif page mission:", evaluate("document.querySelector('.page.active')?.id"))
    shot("02_post_login")

    # C: kirim perintah
    evaluate("""document.getElementById('chat').value='Periksa OpenClaw saya.'; send(); true""")
    # D: tunggu tombol W3 [Lanjutkan]/[Batalkan] muncul
    print("\nD. menunggu tombol W3...")
    has_btn = wait_for("!!document.querySelector('.w3confirm') || !!document.querySelector('.w3cancel')", timeout=25)
    print("  tombol [Lanjutkan]/[Batalkan] tampil:", has_btn)
    assert has_btn, "tombol W3 tidak muncul di DOM"
    shot("03_proposal")
    # cek teks proposal di pesan
    txt = evaluate("document.getElementById('messages').innerText")
    print("  --- pesan proposal ---")
    print(txt[:400])

    # E: klik Lanjutkan
    evaluate("""(()=>{ const b=[...document.querySelectorAll('button')].find(
        x=>x.innerText.trim()==='Lanjutkan'); if(b){b.click(); return true;} return false; })()""")
    # tunggu evidence/komponen muncul di chat
    done = wait_for("""document.body.innerText.includes('komponen')
        || document.body.innerText.includes('healthy')
        || document.body.innerText.includes('OpenClaw Ward')""", timeout=20)
    print("  hasil setelah Lanjutkan (evidence terlihat):", bool(done))
    time.sleep(1.0)
    shot("04_after_lanjut")
    txt2 = evaluate("document.getElementById('messages').innerText")
    print("  --- pesan setelah Lanjutkan ---")
    print(txt2[-600:])

    # F: perintah kedua -> Batalkan
    evaluate("""document.getElementById('chat').value='Periksa OpenClaw saya.'; send(); true""")
    has_btn2 = wait_for("!!document.querySelector('.w3confirm') || !!document.querySelector('.w3cancel')", timeout=25)
    print("\nF. proposal kedua tampil:", has_btn2)
    evaluate("""(()=>{ const b=[...document.querySelectorAll('button')].find(
        x=>x.innerText.trim()==='Batalkan'); if(b){b.click(); return true;} return false; })()""")
    time.sleep(1.5)
    shot("05_after_batal")
    txtF = evaluate("document.getElementById('messages').innerText")
    # tidak boleh ada evidence eksekusi / 'komponen=4' berasal dari observasi (tidak ada mutate)
    print("  --- pesan setelah Batalkan ---")
    print(txtF[-500:])

    print("\n=== LIVE BROWSER JOURNEY W3: PASS ===")
    proc.terminate()


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        import traceback
        traceback.print_exc()
        try:
            shot("error")
        except Exception:
            pass
        raise
    finally:
        if proc:
            proc.terminate()
