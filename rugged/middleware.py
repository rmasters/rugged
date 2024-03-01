import json

from starlette.types import ASGIApp, Receive, Scope, Send, Message
from starlette.datastructures import MutableHeaders

from .unflatteners import unflatten


class RuggedMiddleware:
    should_unflatten: bool
    receive: Receive
    send: Send

    def __init__(self, app: ASGIApp):
        self.app = app

        self.should_unflatten = False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        headers = MutableHeaders(scope=scope)

        self.should_unflatten = "application/json" in headers.get("content-type", "")

        self.receive = receive
        await self.app(scope, self.receive_json, send)

    async def receive_json(self) -> Message:
        message = await self.receive()

        if not self.should_unflatten:
            return message

        body = message["body"]
        more_body = message.get("more_body", False)
        if more_body:
            message = await self.receive()
            if message["body"] != b"":
                raise NotImplementedError(
                    "Streaming the request body not supported yet."
                )

        data = json.loads(body)
        unflattened = unflatten(data)

        message["body"] = json.dumps(unflattened).encode()
        return message
