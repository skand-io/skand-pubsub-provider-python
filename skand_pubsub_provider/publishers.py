from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dapr.clients.grpc._response import DaprResponse

from abc import ABC, abstractmethod
from enum import Enum

import boto3
from dapr.clients import DaprClient as DaprClientLib

from . import settings


class PublisherType(Enum):
    """Enum for publisher types."""

    AWS_SNS = "aws_sns"
    DAPR = "dapr"


class PublisherClient(ABC):
    """Abstract base class for publisher clients."""

    @abstractmethod
    def publish(self, topic: str, message: str) -> None:
        """Publish a message to a specific topic."""


class AWSSNSClient(PublisherClient):
    """AWS SNS client."""

    SERVICE_NAME = "sns"

    client: boto3.client

    def __init__(self, *_args: str, **_kwargs: str) -> None:
        """Initialize the AWS SNS client."""
        endpoint = (
            f"http://{settings.LOCALSTACK_HOSTNAME}:4566"
            if settings.LOCALSTACK_HOSTNAME
            else None
        )
        if endpoint:
            self.client = boto3.session.Session().client(
                self.SERVICE_NAME, endpoint_url=endpoint
            )
        else:
            self.client = boto3.client(self.SERVICE_NAME)

    def publish(self, topic: str, message: str) -> dict[str, str]:
        """Publish a message to an SNS topic."""
        return self.client.publish(TopicArn=topic, Message=message)


class DaprClient(PublisherClient):
    """Dapr client."""

    def __init__(self, pubsub_name: str = "", *_args: str, **_kwargs: str) -> None:
        """Initialize the Dapr client."""
        self.pubsub_name = pubsub_name

    def publish(self, topic: str, message: str) -> DaprResponse:
        """Publish a message to a Dapr pub/sub topic."""
        with DaprClientLib() as client:
            return client.publish_event(
                pubsub_name=self.pubsub_name,
                topic_name=topic,
                data=message,
                data_content_type="application/json",
            )


def _is_running_in_kubernetes() -> bool:
    """Check if the application is running in a Kubernetes environment."""
    return settings.KUBERNETES_SERVICE_HOST and settings.KUBERNETES_SERVICE_PORT


def determine_default_publisher_type() -> PublisherType:
    """Determine the default publisher type based on the computing environment."""
    if _is_running_in_kubernetes():
        return PublisherType.DAPR
    return PublisherType.AWS_SNS


def create_client(
    publisher_type: PublisherType | None = None, *args: str, **kwargs: str
) -> PublisherClient:
    """Create a publisher client based on type."""
    if publisher_type == PublisherType.DAPR:
        return DaprClient(*args, **kwargs)
    if publisher_type == PublisherType.AWS_SNS:
        return AWSSNSClient(*args, **kwargs)
    error_message = f"Unsupported publisher type: {publisher_type}"
    raise ValueError(error_message)
