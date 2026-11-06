"""End-to-end check of the auth flow against the RUNNING servers.

Unlike the pytest tests, this talks to the real backend over HTTP (which uses
the real `inspektorati` database) and checks that the frontend dev server
serves the app. It sends the browser's Origin header, so CORS is checked too.
The users it creates are deleted at the end.

Needs:
- backend running:  cd backend ; venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000
- frontend running: cd frontend ; npm run dev
- seed users:       cd backend ; venv\\Scripts\\python.exe scripts\\seed_users.py

Run from the project root:
    backend\\venv\\Scripts\\python.exe test\\e2e_auth_flow.py
If Vite started on another port (it says so on start), set it first, e.g.:
    $env:E2E_FRONTEND = "http://localhost:5174"
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db.connection import get_connection

API = "http://localhost:8000"
# Vite prints its address on start; it is 5174 when 5173 is already in use.
FRONTEND = os.getenv("E2E_FRONTEND", "http://localhost:5173")
ADMIN = ("admin@vushtrri.rks-gov.net", "Admin!2026")
PASSWORD = "E2e!Fjalekalim1"
STAMP = int(time.time())
INSPEKTOR_EMAIL = f"e2e.inspektor.{STAMP}@example.com"
DREJTOR_EMAIL = f"e2e.drejtor.{STAMP}@example.com"

failures = 0


def call(method, path, body=None, token=None, base=API):
    """Return (status, json_or_text, headers)."""
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=method)
    request.add_header("Origin", FRONTEND)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw, status, headers = response.read(), response.status, response.headers
    except urllib.error.HTTPError as error:
        raw, status, headers = error.read(), error.code, error.headers
    try:
        payload = json.loads(raw) if raw else None
    except ValueError:
        payload = raw.decode("utf-8", "replace")
    return status, payload, headers


def check(label, condition, detail=""):
    global failures
    mark = "OK  " if condition else "FAIL"
    if not condition:
        failures += 1
    print(f"[{mark}] {label}" + (f"  ({detail})" if detail and not condition else ""))


def wait_for(url, name):
    for _ in range(40):
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except Exception:
            time.sleep(0.5)
    print(f"{name} is not reachable at {url}")
    sys.exit(1)


def main():
    wait_for(API + "/docs", "Backend")
    wait_for(FRONTEND + "/", "Frontend")

    print("\n-- frontend serves the app")
    for route in ["/", "/kerkese", "/kycu", "/inspektor", "/admin/perdoruesit"]:
        status, body, _ = call("GET", route, base=FRONTEND)
        # The title proves it is this app, not another Vite project on the same port.
        ours = "Inspektorati AI" in str(body) and '<div id="root">' in str(body)
        check(f"GET {FRONTEND}{route} -> 200 (Inspektorati AI)", status == 200 and ours, status)

    print("\n-- CORS")
    request = urllib.request.Request(API + "/auth/login", method="OPTIONS")
    request.add_header("Origin", FRONTEND)
    request.add_header("Access-Control-Request-Method", "POST")
    request.add_header("Access-Control-Request-Headers", "content-type,authorization")
    with urllib.request.urlopen(request, timeout=10) as response:
        allowed = response.headers.get("access-control-allow-origin")
    check("preflight allows the frontend origin", allowed == FRONTEND, allowed)

    print("\n-- no self-registration")
    user = {"emri": "E2E", "mbiemri": "Inspektor", "email": INSPEKTOR_EMAIL, "password": PASSWORD, "role": "inspektor"}
    status, _, _ = call("POST", "/auth/register", user)
    check("POST /auth/register does not exist -> 404", status == 404)

    print("\n-- admin creates the inspektor")
    status, body, headers = call("POST", "/auth/login", {"email": ADMIN[0], "password": ADMIN[1]})
    check("seed admin logs in", status == 200, body)
    check("response carries CORS header", headers.get("access-control-allow-origin") == FRONTEND)
    admin_token = body["access_token"]
    status, body, _ = call("POST", "/admin/users", user, token=admin_token)
    check("admin creates an inspektor -> 201", status == 201, body)
    status, _, _ = call("GET", "/auth/sektoret")
    check("sectors list is public -> 200", status == 200)

    print("\n-- inspektor login")
    status, body, _ = call("POST", "/auth/login", {"email": INSPEKTOR_EMAIL, "password": "Gabim!12345"})
    check("wrong password -> 401", status == 401, body)
    status, tokens, _ = call("POST", "/auth/login", {"email": INSPEKTOR_EMAIL, "password": PASSWORD})
    check("correct password -> 200 with both tokens", status == 200 and "refresh_token" in tokens, tokens)
    access, refresh = tokens["access_token"], tokens["refresh_token"]

    print("\n-- protected routes")
    status, body, _ = call("GET", "/auth/me", token=access)
    check("/auth/me -> 200, the same user", status == 200 and body["email"] == INSPEKTOR_EMAIL, body)
    status, _, _ = call("GET", "/inspektor/paneli", token=access)
    check("inspektor -> /inspektor/paneli 200", status == 200)
    status, _, _ = call("GET", "/admin/paneli", token=access)
    check("inspektor -> /admin/paneli 403", status == 403)
    status, _, _ = call("GET", "/inspektor/paneli")
    check("no token -> 401", status == 401)

    print("\n-- refresh")
    status, body, _ = call("POST", "/auth/refresh", {"refresh_token": refresh})
    check("refresh -> 200 with a new access token", status == 200 and body.get("access_token"), body)
    status, _, _ = call("GET", "/auth/me", token=body["access_token"])
    check("new access token works", status == 200)

    print("\n-- logout")
    status, _, _ = call("POST", "/auth/logout", {"refresh_token": refresh})
    check("logout -> 204", status == 204)
    status, _, _ = call("POST", "/auth/refresh", {"refresh_token": refresh})
    check("revoked refresh token -> 401", status == 401)

    print("\n-- admin user management")
    status, _, _ = call("GET", "/admin/paneli", token=admin_token)
    check("admin -> /admin/paneli 200", status == 200)
    status, created, _ = call("POST", "/admin/users", {**user, "email": DREJTOR_EMAIL, "role": "drejtor"}, token=admin_token)
    check("admin creates a drejtor -> 201", status == 201, created)
    status, body, _ = call("PATCH", f"/admin/users/{created['id']}", {"emri": "Ndryshuar"}, token=admin_token)
    check("admin edits the user -> 200", status == 200 and body["emri"] == "Ndryshuar", body)
    status, body, _ = call("GET", "/admin/users", token=admin_token)
    check("admin lists users", status == 200 and any(u["email"] == DREJTOR_EMAIL for u in body))
    status, body, _ = call("POST", f"/admin/users/{created['id']}/deactivate", token=admin_token)
    check("admin deactivates the user -> aktiv=false", status == 200 and body["aktiv"] is False, body)
    status, _, _ = call("POST", "/auth/login", {"email": DREJTOR_EMAIL, "password": PASSWORD})
    check("deactivated user cannot log in -> 403", status == 403)
    status, _, _ = call("GET", "/admin/users", token=access)
    check("inspektor cannot manage users -> 403", status == 403)


def cleanup():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM perdoruesit WHERE email IN (%s, %s)",
        (INSPEKTOR_EMAIL, DREJTOR_EMAIL),
    )
    connection.commit()
    print(f"\ncleanup: deleted {cursor.rowcount} e2e users (their refresh tokens cascade)")
    connection.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup()
    print("\nALL CHECKS PASSED" if failures == 0 else f"\n{failures} CHECK(S) FAILED")
    sys.exit(1 if failures else 0)
