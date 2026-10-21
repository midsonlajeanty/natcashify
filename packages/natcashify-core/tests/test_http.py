import pytest
from conftest import LocalServer

from natcashify.core.errors import TransportError
from natcashify.core.http import (
    USER_AGENT,
    AsyncUrllibTransport,
    HttpRequest,
    HttpResponse,
    UrllibTransport,
)
from natcashify.core.testing import FakeTransport

URL = "https://example.test/api"


def test_request_repr_hides_the_body() -> None:
    request = HttpRequest("POST", URL, {}, b'{"password": "s3cr3t"}', 10.0)
    assert "s3cr3t" not in repr(request)


def test_user_agent_names_the_package() -> None:
    assert USER_AGENT.startswith("natcashify/")


def test_urllib_transport_returns_error_statuses(local_server: LocalServer) -> None:
    request = HttpRequest("POST", f"{local_server.base_url}/fail", {}, b"{}", 5.0)
    response = UrllibTransport().send(request)
    assert response.status == 500
    assert response.body == b'{"error": "boom"}'


def test_urllib_transport_does_not_follow_redirects(local_server: LocalServer) -> None:
    request = HttpRequest("POST", f"{local_server.base_url}/redirect", {}, b"{}", 5.0)
    response = UrllibTransport().send(request)
    assert response.status == 302
    assert local_server.hits == ["/redirect"]


def test_urllib_transport_wraps_connection_errors() -> None:
    with pytest.raises(TransportError):
        UrllibTransport().send(HttpRequest("POST", "http://127.0.0.1:9/", {}, b"", 1.0))


def test_urllib_transport_wraps_timeouts(slow_server: LocalServer) -> None:
    request = HttpRequest("POST", f"{slow_server.base_url}/slow", {}, b"{}", 0.2)
    with pytest.raises(TransportError) as info:
        UrllibTransport().send(request)
    assert isinstance(info.value.__cause__, TimeoutError)


def test_urllib_transport_rejects_non_http_urls() -> None:
    with pytest.raises(TransportError):
        UrllibTransport().send(HttpRequest("GET", "file:///etc/passwd", {}, b"", 1.0))


async def test_async_transport_delegates_to_a_thread() -> None:
    inner = FakeTransport(HttpResponse(204, {}, b""))
    request = HttpRequest("POST", URL, {}, b"{}", 5.0)
    response = await AsyncUrllibTransport(inner).send(request)
    assert response.status == 204
    assert inner.requests == [request]


@pytest.mark.parametrize("path", ["/truncated", "/truncated-error"])
def test_urllib_transport_wraps_truncated_responses(local_server: LocalServer, path: str) -> None:
    request = HttpRequest("POST", f"{local_server.base_url}{path}", {}, b"{}", 5.0)
    with pytest.raises(TransportError):
        UrllibTransport().send(request)


def test_urllib_transport_wraps_malformed_urls() -> None:
    with pytest.raises(TransportError):
        UrllibTransport().send(HttpRequest("GET", "http://[bad", {}, b"", 1.0))
