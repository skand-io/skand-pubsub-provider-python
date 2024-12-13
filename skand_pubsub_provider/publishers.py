from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from . import settings

import boto3
from dapr.clients import DaprClient as DaprClientLib

class PublisherType(Enum):
    AWS_SNS = "aws_sns"
    DAPR = "dapr"


class PublisherClient(ABC):
    @abstractmethod
    def publish(self, topic: str, message: str):
        """Publish a message to a specific topic."""
        pass


class AWSSNSClient(PublisherClient):
    def __init__(self, *args, **kwargs):
        endpoint = f"http://{settings.LOCALSTACK_HOSTNAME}:4566" if settings.LOCALSTACK_HOSTNAME else None
        if endpoint:
            self.client = boto3.session.Session().client("sns", endpoint_url=endpoint)
        else:
            self.client = boto3.client("sns")

    def publish(self, topic: str, message: str):
        """Publish a message to an SNS topic."""
        response = self.client.publish(TopicArn=topic, Message=message)
        return response


class DaprClient(PublisherClient):
    def __init__(self, pubsub_name: str="", *args, **kwargs):
        self.pubsub_name = pubsub_name

    def publish(self, topic: str, message: str):
        """Publish a message to a Dapr pub/sub topic."""
        with DaprClientLib() as client:
            response = client.publish_event(
                pubsub_name=self.pubsub_name,
                topic_name=topic,
                data=message,
                data_content_type="application/json",
            )
            return response


def _is_running_in_kubernetes() -> bool:
    """Check if the application is running in a Kubernetes environment."""
    return settings.KUBERNETES_SERVICE_HOST and \
        settings.KUBERNETES_SERVICE_PORT


def determine_default_publisher_type() -> PublisherType:
    """Determine the default publisher type based on the computing environment."""
    if _is_running_in_kubernetes():
        return PublisherType.DAPR
    return PublisherType.AWS_SNS


def create_client(publisher_type: Optional[PublisherType] = None, *args, **kwargs) -> PublisherClient:
    """Factory function to create a publisher client based on type."""
    if publisher_type == PublisherType.DAPR:
        return DaprClient(*args, **kwargs)
    if publisher_type == PublisherType.AWS_SNS:
        return AWSSNSClient(*args, **kwargs)
    raise ValueError(f"Unsupported publisher type: {publisher_type}")
