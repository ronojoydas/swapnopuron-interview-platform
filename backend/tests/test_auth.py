
def test_auth_me_rejects_missing_token(client):
    response = client.get("/auth/me")

    assert response.status_code in (401, 403)


def test_login_rejects_invalid_credentials(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent-test-user@example.com",
            "password": "DefinitelyNotARealPassword123!",
        },
    )

    assert response.status_code == 401
