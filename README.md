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
<h1>Your shopping list</h1>
<form method="post" action="/invite" hx-boost="true" hx-ext="json-enc">
    <label>List name <input type="text" name="title"></label>

    <h2>Items</h2>
    <input type="text" name="items[][item]"> x <input type="number" name="items[][qty]" default="1">
    <input type="text" name="items[][item]"> x <input type="number" name="items[][qty]" default="1">
    <input type="text" name="items[][item]"> x <input type="number" name="items[][qty]" default="1">

    <button onclick="addItemFields()">Add item</button>
    <button type="submit">Save</button>
</form>
```

The request body received by the server could look like this:

```json
{
    "title": "Sofrito time",
    "items[][item]": ["carrots", "celery", "onions"],
    "items[][qty]": [1, 1, 2],
}
```

Using this middleware, the request body is unflattened into:

```python
{
    "title": "Sofrito time",
    "items": [
        {"item": "carrots", "qty": 1},
        {"item": "celery", "qty": 1},
        {"item": "onions", "qty": 2},
    ],
}
```

This makes inputs easier to handle in a FastAPI application using Pydantic:

```python
class ShoppingListItem(BaseModel):
    item: str
    qty: int


class ShoppingList(BaseModel):
    title: str
    items: list[ShoppingListItem]


@app.post("/list")
async def invite_users(shopping_list: ShoppingList):
    find_best_prices(shopping_list.items)
```

A canonical set of supported input names can be found by reading the [unit tests][tests]
for the `unflatten()` function, as [well as the doc-string][docstring] - docs coming soon!

Usage in [starlette][tests-starlette] and [fastapi][tests-fastapi] can be seen
in the respective test files, pending documentation.

[tests]: https://github.com/rmasters/rugged/blob/main/tests/test_unflatteners.py
[tests-starlette]: https://github.com/rmasters/rugged/blob/main/tests/test_middleware_starlette.py
[tests-fastapi]: https://github.com/rmasters/rugged/blob/main/tests/test_middleware_fastapi.py
[docstring]: https://github.com/rmasters/rugged/blob/main/rugged/unflatteners.py

## Contributing & roadmap

-   This middleware is in very early development - things will change. It's being used in a small FastAPI + HTMX microsite. 
-   See the [roadmap](https://github.com/users/rmasters/projects/3) for planned development
-   I am experimenting with Rye to package this project - if you'd like to contribute, the docs are over at [rye-up.com][ryeup]

[ryeup]: https://rye-up.com

## License

This project is released under the terms of the [MIT license](./LICENSE.md).

