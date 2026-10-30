#!/usr/bin/env python3
"""Compile a CV payload (JSON) into a published cv.ryzeon.dev link plus an A4 PDF.

This is the compile step of the `ryzeon` CV template (templates/cv/ryzeon/).
The source file is the API payload documented at <base>/api/cv/schema/.

    python3 tools/ryzeon_cv.py build cv/main_acme_backend.json
    python3 tools/ryzeon_cv.py delete cv/main_acme_backend.json

`build` POSTs the payload the first time and PUTs it afterwards (the CV id is
kept next to the payload in `<file>.id`, so the link never changes while you
iterate). It then prints the page to `<file>.pdf` with headless Chrome and
reports the page count.

Configuration (environment):
    CV_API_TOKEN   bearer token for the API (required, or see RYZEON_CV_ENV)
    RYZEON_CV_ENV  path to a dotenv file holding CV_API_TOKEN
                   (default: ~/Development/@Ryzeon/ryz-cv-web/.env.local)
    CV_API_BASE    API origin (default: https://cv.ryzeon.dev)
    CHROME_BIN     Chrome/Chromium binary used to print the PDF
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

BASE = os.environ.get("CV_API_BASE", "https://cv.ryzeon.dev").rstrip("/")
DEFAULT_ENV = Path.home() / "Development/@Ryzeon/ryz-cv-web/.env.local"
CHROME = os.environ.get(
    "CHROME_BIN", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)


def token() -> str:
    if os.environ.get("CV_API_TOKEN"):
        return os.environ["CV_API_TOKEN"]
    env = Path(os.environ.get("RYZEON_CV_ENV", DEFAULT_ENV)).expanduser()
    if env.exists():
        for line in env.read_text().splitlines():
            m = re.match(r'\s*CV_API_TOKEN\s*=\s*"?([^"\n]+)"?', line)
            if m:
                return m.group(1).strip()
    sys.exit("CV_API_TOKEN not found: export it or point RYZEON_CV_ENV at a dotenv file")


def call(method: str, path: str, body: bytes | None = None) -> dict:
    req = urllib.request.Request(
        BASE + path,
        data=body,
        method=method,
        headers={"Authorization": f"Bearer {token()}", "content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        sys.exit(f"{method} {path} -> {e.code}\n{detail}")


def print_pdf(url: str, out: Path) -> int:
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             f"--user-data-dir={profile}", "--virtual-time-budget=8000",
             f"--print-to-pdf={out}", url],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    return len(re.findall(rb"/Type\s*/Page[^s]", out.read_bytes()))


def build(src: Path) -> None:
    payload = src.read_bytes()
    json.loads(payload)  # fail fast on invalid JSON
    id_file = src.with_name(src.name + ".id")
    if id_file.exists():
        cv_id = id_file.read_text().strip()
        call("PUT", f"/api/cv/{cv_id}/", payload)
    else:
        cv_id = call("POST", "/api/cv/", payload)["id"]
        id_file.write_text(cv_id + "\n")
    url = f"{BASE}/cv/{cv_id}/"
    pdf = src.with_suffix(".pdf")
    pages = print_pdf(url, pdf)
    print(f"url   {url}\npdf   {pdf}\npages {pages}")


def delete(src: Path) -> None:
    id_file = src.with_name(src.name + ".id")
    if not id_file.exists():
        sys.exit(f"no {id_file.name}: nothing published for {src}")
    call("DELETE", f"/api/cv/{id_file.read_text().strip()}/")
    id_file.unlink()
    print("deleted")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in {"build", "delete"}:
        sys.exit(__doc__)
    {"build": build, "delete": delete}[sys.argv[1]](Path(sys.argv[2]))
