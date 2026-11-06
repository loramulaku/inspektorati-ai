"""Role-based access: each role reaches only its own protected route."""

import pytest

ROUTES = {
    "inspektor": "/inspektor/paneli",
    "drejtor": "/drejtor/paneli",
    "admin": "/admin/paneli",
}


@pytest.mark.parametrize("role", ROUTES)
def test_each_role_reaches_only_its_own_route(role, client, make_user, login, auth_header):
    user = make_user(role)
    headers = auth_header(login(user.email)["access_token"])

    for route_role, route in ROUTES.items():
        response = client.get(route, headers=headers)
        if route_role == role:
            assert response.status_code == 200
            assert response.json()["role"] == role
        else:
            assert response.status_code == 403
            assert response.json()["detail"] == "Nuk keni leje për këtë veprim"


@pytest.mark.parametrize("route", ROUTES.values())
def test_protected_routes_need_login(route, client):
    assert client.get(route).status_code == 401


def test_deactivated_user_loses_access_with_old_token(client, make_user, login, auth_header, db):
    user = make_user("inspektor")
    headers = auth_header(login(user.email)["access_token"])
    assert client.get("/inspektor/paneli", headers=headers).status_code == 200

    user.aktiv = False
    db.commit()
    assert client.get("/inspektor/paneli", headers=headers).status_code == 401
