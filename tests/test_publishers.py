from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

import pytest
from dapr.clients.exceptions import DaprGrpcError
from dapr.conf import settings as dapr_settings
from google.rpc import code_pb2, status_pb2

from skand_pubsub_provider import publishers, settings

from .daprutils.fake_dapr_server import FakeDaprSidecar


@pytest.fixture
def dapr_server() -> Generator[FakeDaprSidecar, Any, None]:
    """Fixture to start a fake Dapr server."""
    server = FakeDaprSidecar()
    server.start()

    dapr_settings.DAPR_HTTP_PORT = server.http_port
    dapr_settings.DAPR_HTTP_ENDPOINT = f"http://127.0.0.1:{server.http_port}"

    yield server
    server.stop()


def test_dapr_client_publish(dapr_server: FakeDaprSidecar) -> None:
    pubsub_name, topic, message = "pubsub", "example", "test_data"

    dapr_client = publishers.DaprClient(pubsub_name=pubsub_name)
    resp = dapr_client.publish(topic=topic, message=message)

    assert resp.headers["hdata"] == [message]
    assert resp.headers["htopic"] == [topic]
    assert resp.headers["data_content_type"] == ["application/json"]

    # Set up the mock server to raise an exception
    dapr_server.raise_exception_on_next_call(
        status_pb2.Status(
            code=code_pb2.INVALID_ARGUMENT, message="my invalid argument message"
        )
    )

    # Use `pytest.raises` to check for exceptions
    with pytest.raises(DaprGrpcError):
        dapr_client.publish(topic=topic, message=message)


@pytest.mark.parametrize(
    ("publisher_type", "expected"),
    [
        (publishers.PublisherType.AWS_SNS, publishers.AWSSNSClient),
        (publishers.PublisherType.DAPR, publishers.DaprClient),
    ],
)
def test_create_client_with_parameters_in_happy_cases(
    publisher_type: str, expected: publishers.PublisherClient
) -> None:
    client = publishers.create_client(publisher_type)
    assert isinstance(client, expected)


@pytest.mark.parametrize(
    "publisher_type",
    [
        None,
        "UNKOWN_PUBLISHER_TYPE",
    ],
)
def test_create_client_with_parameters_in_failed_cases(
    publisher_type: str | None,
) -> None:
    with pytest.raises(ValueError):
        publishers.create_client(publisher_type)


@pytest.mark.parametrize(
    ("kubenernetes_service_host", "kubenernetes_service_port", "expected_client"),
    [
        ("10.152.183.1", "443", publishers.DaprClient),
        ("10.152.183.1", None, publishers.AWSSNSClient),
        (None, "443", publishers.AWSSNSClient),
        (None, None, publishers.AWSSNSClient),
    ],
)
def test_create_client_with_settings(
    kubenernetes_service_host: str | None,
    kubenernetes_service_port: str | None,
    expected_client: publishers.PublisherClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "KUBERNETES_SERVICE_HOST", kubenernetes_service_host)
    monkeypatch.setattr(settings, "KUBERNETES_SERVICE_PORT", kubenernetes_service_port)

    publisher_type = publishers.determine_default_publisher_type()
    client = publishers.create_client(publisher_type=publisher_type)
    assert isinstance(client, expected_client)
