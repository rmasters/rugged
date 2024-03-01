from starlette.applications import Starlette
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from rugged.middleware import RuggedMiddleware


def test_starlette_usage() -> None:
    async def invite(request: Request) -> JSONResponse:
        return JSONResponse(await request.json())

    app = Starlette(
        routes=[Route("/invite", methods=["POST"], endpoint=invite)],
        middleware=[
            Middleware(RuggedMiddleware),
        ],
    )

    client = TestClient(app)

    response = client.post(
        "/invite",
        json={
            "emails[0]": "foo@example.com",
            "emails[1]": "bar@example.com",
            "emails[2]": "baz@example.com",
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
