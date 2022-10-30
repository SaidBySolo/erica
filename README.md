# erica

> flask-like zero denpendency web server.

## Sample

```py
from erica import Erica, RequestHandler

app = Erica()


@app.get("/")
def hello(request: RequestHandler) -> None:
    request.response.json({"message": "Hello, World!"})


@app.post("/")
def q(request: RequestHandler) -> None:
    request.response.text(f"you posted {request.text}")


app.run()
```
