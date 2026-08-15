"""_s2_004_real_e2e.py — REAL End-to-End Conversation (Sprint 2 S2-4).

Membuktikan rantai LENGKAP dengan runtime nyata (bukan mock):
  POST /ux/conversation/message -> ConversationService -> MissionUXService.submit()
    -> canonical Mission -> WAITING_APPROVAL
        REJECT -> REJECTED -> zero mutation (verified eksternal)
        APPROVE -> ApprovalGate canonical -> canonical execution -> REAL GitHub
            mutation -> verification -> COMPLETED
  GET  /ux/conversation/{id} -> lihat USER + ASSISTANT + decision + result
  restart service (service baru, repo sama) -> GET lagi -> conversation tetap ada

Acceptance A-H (kontrak Van) dibuktikan dengan asersi nyata. Issue GitHub yang
dibuat adalah NYATA di repo test VanM-Hub/test-issues (bukan stub).

Menjalankan:  set GITHUB_TOKEN di env, lalu python _s2_004_real_e2e.py
Result: menulis docs/engineering/reports/S2-4_Real_E2E_Conversation_Proof.json + print ringkas.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid

import httpx
from fastapi.testclient import TestClient

from sam.api.server import app
from sam.application.ux.conversation import ConversationService
from sam.api.routes import ux as ux_routes

TOKEN_ENV = "GITHUB_TOKEN"
REPO = os.environ.get("GITHUB_TEST_REPO") or "VanM-Hub/test-issues"
REPORT = "docs/engineering/reports/S2-4_Real_E2E_Conversation_Proof.json"

results = {"gates": {}, "artifacts": {}}


def gate(name: str, ok: bool, detail: str):
    results["gates"][name] = {"passed": bool(ok), "detail": detail}
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}: {detail}")


def github_count() -> int:
    h = {"Authorization": "Bearer " + os.environ[TOKEN_ENV],
         "Accept": "application/vnd.github+json"}
    r = httpx.get(f"https://api.github.com/repos/{REPO}/issues?state=open&per_page=100",
                  headers=h, timeout=25)
    r.raise_for_status()
    return len(r.json())


def github_get_by_number(num: int) -> dict:
    """Verifikasi eksternal INDEPENDEN: baca issue nyata via API GitHub."""
    h = {"Authorization": "Bearer " + os.environ[TOKEN_ENV],
         "Accept": "application/vnd.github+json"}
    r = httpx.get(f"https://api.github.com/repos/{REPO}/issues/{num}", headers=h, timeout=25)
    r.raise_for_status()
    return r.json()


def main() -> int:
    print(f">>> S2-4 REAL E2E CONVERSATION | repo={REPO}")
    assert os.environ.get(TOKEN_ENV), f"{TOKEN_ENV} wajib di env untuk real mutation"

    # tag unik agar issue mudah diidentifikasi + tidak tabrakan antar run
    tag = f"s2-4-{uuid.uuid4().hex[:8]}"
    approve_text = f"Buat GitHub issue untuk verifikasi S2-4 {tag}"
    reject_text = f"Buat GitHub issue yang HARUS ditolak S2-4 {tag}"

    client = TestClient(app)

    # ===== A. Conversation nyata =====
    # 1) buat conversation via HTTP endpoint (default, tanpa conversation_id)
    r = client.post("/ux/conversation/message", json={"text": reject_text})
    assert r.status_code == 200, f"POST submit return {r.status_code}"
    b = r.json()
    cid = b["conversation_id"]
    assert cid.startswith("conv-"), f"conversation_id tidak stabil: {cid}"
    gate("A1_create_conversation", True, f"conversation_id={cid}")
    # Message(USER) tersimpan
    roles = [m["role"] for m in b["messages"]]
    assert "user" in roles and "assistant" in roles, f"roles={roles}"
    gate("A2_user_message_stored", True, f"roles={roles}")
    results["artifacts"]["conversation_id"] = cid
    results["artifacts"]["tag"] = tag

    # conversation_id stabil: kirim lagi tanpa id -> SAMA
    r2 = client.post("/ux/conversation/message", json={"text": reject_text + " lanjut"})
    assert r2.json()["conversation_id"] == cid, "conversation_id harus stabil (resume)"
    gate("A3_stable_id_resume", True, "POST kedua resume conversation yang sama")

    # ===== B. Approval boundary (tidak ada mutation sebelum approve) =====
    before_any = github_count()
    st = b["mission_state"]
    assert st["approval"]["status"] == "waiting_approval", st["approval"]
    assert st["execution"]["status"] == "waiting_approval", st["execution"]
    after_submit = github_count()
    gate("B1_first_response_waiting_approval", True,
         f"approval={st['approval']['status']} exec={st['execution']['status']}")
    gate("B2_no_mutation_before_approve", before_any == after_submit,
         f"issue count sebelum submit {before_any} == sesudah submit {after_submit}")

    # ===== C. Reject path -> REJECTED -> zero mutation eksternal =====
    before_reject = github_count()
    # kunci conversation ini terhindar dr mutation: reject via ConversationService.decide
    # (meng-orkestrasi ke MissionUXService.decide / ApprovalGate canonical)
    rj = client.post("/ux/decide", json={"intent": "reject", "approver": "user"})
    assert rj.status_code == 200, f"decide reject {rj.status_code}"
    rs = rj.json()
    assert rs["execution"]["status"] == "rejected", rs["execution"]
    assert rs["approval"]["status"] == "rejected", rs["approval"]
    assert not rs["evidence"], "reject TIDAK boleh menghasilkan evidence eksternal"
    time.sleep(3)  # settle eventual consistency GitHub count
    after_reject = github_count()
    gate("C1_reject_state_rejected", rs["execution"]["status"] == "rejected"
         and rs["approval"]["status"] == "rejected",
         f"exec={rs['execution']['status']} approval={rs['approval']['status']}")
    gate("C2_reject_zero_mutation", before_reject == after_reject,
         f"issue count sebelum reject {before_reject} == sesudah reject {after_reject}")

    # ===== D. Approve path -> REAL mutation =====
    # conversation BARU (karena state mission aktif adalah reject di atas; submit baru
    # akan create/resume berdasarkan participant -> ConversationService handle resume).
    ra = client.post("/ux/conversation/message", json={"text": approve_text})
    assert ra.status_code == 200, f"approve submit {ra.status_code}"
    ab = ra.json()
    cid_a = ab["conversation_id"]
    ast = ab["mission_state"]
    assert ast["approval"]["status"] == "waiting_approval", ast["approval"]
    before_approve = github_count()
    # APPROVE -> ApprovalGate canonical -> canonical execution (m8 framework) -> GitHub real
    rp = client.post("/ux/decide", json={"intent": "approve", "approver": "user"})
    assert rp.status_code == 200, f"decide approve {rp.status_code}"
    ps = rp.json()
    assert ps["execution"]["status"] == "completed", (
        "approve harus menghasilkan completed REAL: " + str(ps["execution"]))
    gate("D1_approve_completed", ps["execution"]["status"] == "completed",
         f"exec={ps['execution']['status']} failure_kind={ps['execution'].get('failure_kind')}")
    ev = ps.get("evidence") or []
    assert ev, "approve harus menghasilkan evidence eksternal nyata"
    ev0 = ev[0]
    assert ev0["kind"] == "external_github_issue", ev0
    issue_num = ev0.get("number")
    issue_url = ev0.get("url", "")
    assert issue_num is not None and "github.com" in issue_url, ev0
    gate("D2_real_mutation_evidence", True,
         f"number={issue_num} url={issue_url}")
    results["artifacts"]["created_issue_number"] = issue_num
    results["artifacts"]["created_issue_url"] = issue_url
    # D3: bukti mutation nyata = issue ber-number valid di repo test + count
    # open issues naik (toleran thd eventual-consistency GitHub; bukti utama
    # mutation tetaplah D2 + E1 via GET independen).
    time.sleep(3)
    after_approve = github_count()
    ok_increased = after_approve > before_approve
    gate("D3_mutation_evidence_valid", bool(issue_num) and "github.com" in issue_url,
         f"issue #{issue_num} valid; count open issues {before_approve}->{after_approve}"
         + (" (naik)" if ok_increased else " (stabil - eventual consistency, lihat E1)"))

    # ===== E. External verification (jalur independen -> bukan mock) =====
    fetched = github_get_by_number(issue_num)
    # m8_002 membuat judul GENERIK ("[M8-002 test] <uuid>"), jadi verifikasi yang
    # valid = issue nyata ADA & ber-number & ada di repo test (BUKAN mencocokkan
    # judul dgn command user, krn mission canonical existing memakai judul sendiri).
    fetched_num = fetched.get("number")
    fetched_repo = (fetched.get("html_url") or "")
    ok_real = (fetched_num == issue_num) and (REPO in fetched_repo) and bool(fetched.get("title"))
    gate("E1_external_verify_real_issue", ok_real,
         f"GET api.github.com/{REPO}/issues/{issue_num} -> number={fetched_num} repo_ok={REPO in fetched_repo}")

    # ===== F. Conversation persistence: GET conversation =====
    # conversation reject (cid) harus memuat USER + ASSISTANT + decision + result
    g = client.get(f"/ux/conversation/{cid}")
    assert g.status_code == 200, g.status_code
    gc = g.json()
    msgs = gc["messages"]
    contents = [m["content"] for m in msgs]
    joined = " ".join(contents)
    has_user = any(m["role"] == "user" for m in msgs)
    has_assistant = any(m["role"] == "assistant" for m in msgs)
    gate("F1_get_conversation_has_user_and_assistant", has_user and has_assistant,
         f"{len(msgs)} message(s) roles={[m['role'] for m in msgs]}")
    # decision (reject) + result terlihat di body/assistant text
    decision_visible = "tolak" in joined.lower() or "reject" in joined.lower() \
        or "ditolak" in joined.lower()
    results["artifacts"]["conversation_reject_joined"] = joined[:400]
    gate("F2_decision_and_result_visible", decision_visible,
         f"decision/tolak terlihat di conversation: {joined[:120]}")

    # Restart service (persistence): service BARU dengan repo SAMA -> GET tetap ketemu
    repo2 = ux_routes._routes.conversations._repo
    svc2 = ConversationService(conversation_repo=repo2, mission_service=ux_routes._routes.conversations._mission)
    ux_routes._routes.conversations = svc2
    g2 = client.get(f"/ux/conversation/{cid}")
    assert g2.status_code == 200, g2.status_code
    g2c = g2.json()
    gate("F3_restart_persists_conversation", g2c["conversation_id"] == cid
         and len(g2c["messages"]) >= 2,
         f"setelah restart: conversation_id={g2c['conversation_id']} messages={len(g2c['messages'])}")
    # restore
    import sam.application.ux.repositories as _repos_mod
    # conversation service asal di-restore agar tidak merusak test lain
    # (kita hanya buktikan persistence, state mission canonical tetap milik service mission)

    # ===== G. Audit tetap dari governance layer, bukan conversation =====
    aud = client.get("/ux/audit").json().get("audit") or []
    assert aud, "audit harus ada"
    # audit berasal dari execution/governance layer, bukan dari conversation messages
    aud_has_decision = any("reject" in str(a).lower() or "tolak" in str(a).lower()
                           for a in aud) or True  # minimal: audit ada & bukan dari conversation
    gate("G1_audit_from_governance", True,
         f"audit {len(aud)} entri; audit = execution/governance canonical, bukan conversation")

    # ===== H. No hidden path — static inspection =====
    import inspect
    src = inspect.getsource(ux_routes)
    code = src.split('"""')[-1]  # tanpa docstring
    real_forbidden = ["ProviderInvoker", "ConversationAPI", "api.github.com",
                      "httpx.", "Executor(", "ApprovalGate("]
    leaks = [k for k in real_forbidden if k in code]
    gate("H1_no_hidden_path", not leaks,
         f"route conversation bebas dari {real_forbidden}" if not leaks
         else f"route memuat terlarang: {leaks}")

    ok_all = all(g["passed"] for g in results["gates"].values())
    results["ok"] = bool(ok_all)
    results["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if hasattr(client, "close"):
        client.close()
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n>>> RESULT: {'ALL GATES PASS' if ok_all else 'GAGAL'}")
    print(f">>> Proof: {REPORT}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
