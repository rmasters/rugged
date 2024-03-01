<h1>
  Rugged
  <a href="https://pypi.org/project/rugged"><img src="https://img.shields.io/pypi/v/rugged"></a>
</h1>

An ASGI middleware to unflatten JSON request keys into nested structures.

This behaviour might be familiar [if you've used PHP before][php-form-arrays].

[php-form-arrays]: https://www.php.net/manual/en/faq.html.php#faq.html.arrays

## Example use case

The inspiration for this middleware came from a web app with forms that add
variable numbers of fields dynamically. This web app uses htmx to submit forms
as AJAX requests, and the hx-json-enc extension to send form data as JSON.

For example, with a form like so:

```html
<form method="post" action="/invite" hx-boost="true" hx-ext="json-enc">
    <h1>Invite users</h1>
    <input type="text" name="emails[0]">
    <input type="text" name="emails[1]">
    <input type="text" name="emails[2]">

    <button onclick="addEmailInput()">Add email</button>
    <button type="submit">Send invites</button>
</form>
```

The request body could look like this:

```json
{
    "emails[0]": "foo@example.com",
    "emails[1]": "bar@example.com",
    "emails[2]": "baz@example.com"
}
```

Using the middleware, the request body is unflattened into:

```json
{
    "emails": ["foo@example.com", "bar@example.com", "baz@example.com"]
}
```

This makes inputs easier to handle in a FastAPI application using Pydantic:

```python
class InviteUsers(BaseModel):
    emails: list[str]


@app.post("/invite")
async def invite_users(invite: InviteUsers):
    send_invites(invite.emails)
```

Similarly, this can be nested further:

<table>
<tr>
<td>

```json
{
    "order_id": "1234",
    "product[0][name]": "Product 1",
    "product[0][price]": 100,
    "product[1][name]": "Product 2",
    "product[1][price]": 200,
    "product[2][name]": "Product 3",
    "product[2][price]": 300
}
```

</td>
<td>

```json
{
    "order_id": "1234",
    "product": [
        {"name": "Product 1", "price": 100},
        {"name": "Product 2", "price": 200},
        {"name": "Product 3", "price": 300}
    ]
}
```

</td>
</tr>
</table>

A canonical set of supported inputs can be found by reading the [unit tests][tests]
for the `unflatten()` function.

Usage in [starlette][tests-starlette] and [fastapi][tests-fastapi] can be seen
in the respective test files, pending documentation.

[tests]: https://github.com/rmasters/rugged/blob/main/tests/test_unflatteners.py
[tests-starlette]: https://github.com/rmasters/rugged/blob/main/tests/test_middleware_starlette.py
[tests-fastapi]: https://github.com/rmasters/rugged/blob/main/tests/test_middleware_fastapi.py

## Roadmap / future development ideas

-   Support for un-indexed arrays, e.g. `product[]`
-   Support custom delimiters/formats other than square brackets, e.g. `product.0.name`
-   Support alternative JSON decoders
-   Support for re-flattening dictionaries, if useful
-   Investigate whether this middleware can be used with x-www-form-urlencoded and
    multipart/form-data bodies
-   Some performance optimisation - can we avoid regex?
-   Establish minimum Starlette version required
-   Establish minimum Python version required

## License

This project is licensed under the terms of the [MIT license](./LICENSE.md).

