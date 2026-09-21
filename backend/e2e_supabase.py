"""End-to-end smoke test against the live stack: Supabase Auth + Supabase DB + MinIO storage.

Flow: sign in -> /auth/me -> sign upload URL -> PUT to MinIO -> create report ->
inline AI pipeline (YOLOv8 detection) -> report detail + analytics.
"""

import json
import os
import sys
import time
import urllib.request
import uuid

import httpx

from app.config import settings

API = os.environ.get("E2E_API", "http://localhost:8000/v1")
SB = settings.SUPABASE_URL
SB_KEY = settings.SUPABASE_PUBLISHABLE_KEY  # client-safe publishable key
EMAIL = os.environ.get("E2E_EMAIL", "citizen@urbanlens.demo")
PASSWORD = os.environ.get("E2E_PASSWORD") or settings.SEED_DEMO_PASSWORD

OK, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(label: str, cond: bool, info: str = "") -> bool:
    results.append((OK if cond else FAIL, label, info))
    print(f"[{OK if cond else FAIL}] {label}" + (f" — {info}" if info else ""))
    return cond


def get_pothole_image() -> bytes:
    """Pull a real pothole JPEG from the public HuggingFace training dataset."""
    repo = "Ryukijano/Pothole-detection-Yolov8"
    base = "https://huggingface.co"
    exts = (".jpg", ".jpeg", ".png")

    def tree(path: str = ""):
        url = f"{base}/api/datasets/{repo}/tree/main" + (f"/{path}" if path else "")
        entries = json.loads(urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "urbanlens-e2e"}),
            timeout=30,
        ).read())
        return [(e["type"], "/".join(p for p in [path, e["path"].split("/")[-1]] if p))
                for e in entries]

    queue = [""]
    while queue:
        listing = tree(queue.pop(0))
        files = [p for t, p in listing if p.lower().endswith(exts)]
        if files:
            data = urllib.request.urlopen(
                urllib.request.Request(
                    f"{base}/datasets/{repo}/resolve/main/{files[0]}",
                    headers={"User-Agent": "urbanlens-e2e"}),
                timeout=60,
            ).read()
            if len(data) > 5000:
                print(f"  image: {files[0]} ({len(data)} bytes)")
                return data
        queue.extend(p for t, p in listing if t == "directory")
    raise RuntimeError("no pothole sample downloaded")


def main() -> int:
    stamp = uuid.uuid4().hex[:8]

    # 1. Supabase password login
    r = httpx.post(
        f"{SB}/auth/v1/token?grant_type=password",
        headers={"apikey": SB_KEY, "Content-Type": "application/json"},
        json={"email": EMAIL, "password": PASSWORD},
        timeout=30,
    )
    if not check("Supabase password login", r.status_code == 200, f"HTTP {r.status_code}"):
        return 1
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    # 2. FastAPI trusts the Supabase JWT against the Supabase DB
    r = httpx.get(f"{API}/auth/me", headers=auth, timeout=30)
    ok = r.status_code == 200 and r.json().get("email") == EMAIL
    check("GET /v1/auth/me via Supabase token", ok,
          json.dumps(r.json(), default=str)[:140] if ok else r.text[:140])
    uid = r.json().get("id") if ok else None
    import base64
    claims = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))
    check("local profile id == Supabase auth uid",
          bool(uid) and uid == claims.get("sub"), f"uid={uid} sub={claims.get('sub')}")

    r = httpx.get(f"{API}/auth/me", headers={"Authorization": "Bearer garbage"}, timeout=30)
    check("invalid token rejected", r.status_code == 401, f"HTTP {r.status_code}")

    # 3. Storage: signed upload into MinIO
    image = get_pothole_image()
    r = httpx.post(
        f"{API}/uploads/sign",
        headers=auth,
        params={"filename": f"e2e-{stamp}.jpg", "content_type": "image/jpeg",
                "size_bytes": len(image)},
        timeout=30,
    )
    ok = r.status_code == 200 and "upload_url" in r.json()
    if not check("POST /v1/uploads/sign", ok, r.text[:140]):
        return 1
    sign = r.json()
    put = httpx.put(sign["upload_url"], content=image,
                    headers=sign.get("headers") or {}, timeout=60)
    check("PUT object to storage", put.status_code in (200, 204), f"HTTP {put.status_code}")

    # 4. Create report -> inline AI pipeline
    body = {
        "issue_type": "pothole",
        "description": f"E2E Supabase check {stamp}: deep pothole on the service road.",
        "latitude": 19.0773,
        "longitude": 72.9986,
        "location_source": "manual_pin",
        "landmark": "Near Vashi Railway Station, Sector 9",
        "consent_location": True,
        "consent_training": False,
        "media": [{"object_key": sign["object_key"],
                   "mime_type": "image/jpeg", "kind": "image"}],
    }
    t0 = time.time()
    r = httpx.post(f"{API}/reports/", headers={**auth, "Content-Type": "application/json"},
                   json=body, timeout=180)
    if not check("POST /v1/reports/", r.status_code in (200, 201), f"HTTP {r.status_code} {r.text[:120]}"):
        return 1
    report = r.json()
    rid = report["id"]

    # 5. Detection ran inside the pipeline (async task — poll until it lands)
    deadline = time.time() + 180
    runs, detail = [], report
    while time.time() < deadline:
        detail = httpx.get(f"{API}/reports/{rid}", headers=auth, timeout=60).json()
        runs = detail.get("inference_runs", [])
        if any(x["task"] == "detection" for x in runs):
            break
        time.sleep(3)
    det = [x for x in runs if x["task"] == "detection"]
    detections = (det[0]["result"].get("detections") or []) if det else []
    for x in runs:
        print(f"    run: {x['task']:10} {x['model_name']}@{x['model_version']} "
              f"{x['latency_ms']}ms")
    check("inference runs recorded", len(runs) >= 2, f"{len(runs)} runs")
    check("YOLOv8 detected a pothole",
          any(d.get("class_name") == "pothole" and d.get("confidence", 0) > 0.4
              for d in detections),
          json.dumps(detections[:2]))
    check("report persisted with priority",
          detail.get("priority_score") is not None,
          f"priority={detail.get('priority_score')} status={detail.get('status')}")
    print(f"    pipeline wall-time: {time.time() - t0:.1f}s")

    # 6. Reads come from Supabase
    r = httpx.get(f"{API}/reports/", headers=auth, params={"mine": True}, timeout=30)
    check("GET /v1/reports (mine)", r.status_code == 200 and any(
        x["id"] == rid for x in r.json()), f"{len(r.json())} rows")
    r = httpx.get(f"{API}/analytics/summary", headers=auth, timeout=30)
    check("GET /v1/analytics/summary", r.status_code == 200 and
          r.json()["total_reports"] >= 11, json.dumps(r.json())[:160])
    r = httpx.get(f"{API}/incidents/", headers=auth, timeout=30)
    check("GET /v1/incidents", r.status_code == 200 and len(r.json()) >= 9,
          f"{len(r.json())} incidents")

    # 7. Moderator role gate works through Supabase identity
    rm = httpx.post(
        f"{SB}/auth/v1/token?grant_type=password",
        headers={"apikey": SB_KEY, "Content-Type": "application/json"},
        json={"email": "moderator@urbanlens.demo", "password": PASSWORD}, timeout=30,
    )
    mtok = rm.json().get("access_token")
    r = httpx.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {mtok}"}, timeout=30)
    check("moderator role preserved after login", r.json().get("role") == "moderator",
          f"role={r.json().get('role')}")

    failed = [x for x in results if x[0] == FAIL]
    print("\n" + "=" * 60)
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        for _, label, info in failed:
            print(f"  FAILED: {label} — {info}")
        return 1
    print("E2E against Supabase Cloud: ALL GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
