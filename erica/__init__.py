import json
import socketserver
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Optional

Handler = Callable[["RequestHandler"], Any]


class Response:
    def __init__(self, req_handler: "RequestHandler") -> None:
        self.req_handler = req_handler
        self.mapping = {
            200: "OK",
            201: "Created",
            204: "No Content",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error",
        }

    def send_headers(self, headers: Dict[str, Any]) -> None:
        for key, value in headers.items():
            self.req_handler.send_header(key, value)
        self.req_handler.end_headers()

    def raw(
        self, data: bytes, status: int, message: str, headers: Dict[str, Any]
    ) -> None:
        """Send a raw response."""
        self.req_handler.send_response(status, message)
        self.send_headers(headers)
        self.req_handler.wfile.write(data)

    def json(
        self,
        data: Dict[str, Any] = {},
        status: int = 200,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a JSON response."""
        if headers is None:
            headers = {}
        headers["Content-type"] = "application/json"
        self.raw(
            json.dumps(data).encode("utf-8"),
            status,
            self.mapping[status],
            headers,
        )

    def text(
        self,
        data: str = "",
        status: int = 200,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a text response."""
        if headers is None:
            headers = {}
        headers["Content-type"] = "text/plain"
        self.raw(
            data.encode("utf-8"),
            status,
            self.mapping[status],
            headers,
        )


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(
        self,
        app: "App",
        request: bytes,
        client_address: tuple[str, int],
        server: socketserver.BaseServer,
    ) -> None:
        self.app = app
        super().__init__(request, client_address, server)

    def do_GET(self) -> Any:
        try:
            return self.app.dispatch(self, "GET")
        except Exception as e:
            self.response.text(str(e), 500)

    def do_POST(self) -> Any:
        try:
            return self.app.dispatch(self, "POST")
        except Exception as e:
            self.response.text(str(e), 500)

    @property
    def response(self) -> Response:
        """Returns a response object for the request."""
        return Response(self)

    @property
    def content_length(self) -> int:
        """Return the content length of the request."""
        return int(self.headers.get("Content-Length", 0))

    @property
    def raw(self) -> bytes:
        """
        Returns the raw request body
        """
        return self.rfile.read(self.content_length)

    @property
    def json(self) -> Any:
        """
        Returns the request body as a JSON object.
        """
        return json.loads(self.raw)

    @property
    def text(self) -> str:
        """
        Returns the request body as a string.
        """
        return self.raw.decode("utf-8")


class Erica:
    def __init__(self) -> None:
        self.handlers: List[Dict[str, Any]] = []

    def register(self, path: str, method: str) -> Callable[[Handler], Handler]:
        """
        Register a handler for a given path and method
        """

        def wrapper(handler: Handler) -> Handler:
            self.handlers.append({"path": path, "handler": handler, "method": method})
            return handler

        return wrapper

    def get(self, path: str) -> Callable[[Handler], Handler]:
        """
        Register a GET handler for a given path
        """

        def wrapper(handler: Handler) -> Handler:
            self.handlers.append({"path": path, "handler": handler, "method": "GET"})
            return handler

        return wrapper

    def post(self, path: str) -> Callable[[Handler], Handler]:
        """
        Register a POST handler for a given path
        """

        def wrapper(handler: Handler) -> Handler:
            self.handlers.append({"path": path, "handler": handler, "method": "POST"})
            return handler

        return wrapper

    def dispatch(self, req_handler: RequestHandler, method: str) -> Any:
        """
        Dispatch a request to the appropriate handler
        """
        for handler in self.handlers:
            if handler["path"] == req_handler.path and handler["method"] == method:
                return handler["handler"](req_handler)
        else:
            return req_handler.response.text("Not Found", status=404)

    def get_handler(self) -> partial[RequestHandler]:
        """
        Return a partial RequestHandler with the app instance
        """
        return partial(RequestHandler, self)

    def run(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """
        Run the app
        """
        http = HTTPServer((host, port), self.get_handler())
        try:
            print(f"Server started at http://{host}:{port}")
            http.serve_forever()
        except KeyboardInterrupt:
            http.server_close()
        finally:
            print("Server stopped")
