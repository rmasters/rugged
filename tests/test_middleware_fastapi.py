from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from rugged.middleware import RuggedMiddleware


def test_fastapi_usage() -> None:
    app = FastAPI()
    app.add_middleware(RuggedMiddleware)

    class InviteEmails(BaseModel):
        emails: list[str]

    @app.post("/invite", response_model=InviteEmails)
    async def invite(invite: InviteEmails) -> dict[str, list[str]]:
        return {"emails": invite.emails}

    client = TestClient(app)

    response = client.post(
        "/invite",
        json={
            "emails[]": ["foo@example.com", "bar@example.com", "baz@example.com"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "emails": [
            "foo@example.com",
            "bar@example.com",
            "baz@example.com",
        ],
    }
