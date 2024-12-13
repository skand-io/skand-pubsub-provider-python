# Skand Pubsub Provider Python

This package provides an abstract interface for publishing messages using AWS SNS and the Dapr publish client.

- **AWS SNS** is used when the application runs outside Kubernetes.
- **Dapr publish client** is used when the application runs within Kubernetes.

## Usage

```python
from skand_pubsub_provider import publishers

publisher_type = publishers.determine_default_publisher_type()
sns_client_response = publishers.create_client(publisher_type).publish(
    topic=settings.IMAGE_THUMBNAIL_CREATED_V2_TOPIC_ARN,
    message=payload_json_string,
)
```

## Installation from a Private GitHub Repository

For detailed instructions, refer to the [Poetry documentation on private repositories](https://python-poetry.org/docs/repositories/#private-repository-example).

### Configure Access to GitHub Repositories for Poetry

```shell
poetry config repositories.skand-io-github-org https://github.com/skand-io/
poetry config http-basic.skand-io-github-org <username> <github_token>
```

Note: The GitHub token should have the permission to read the private repository.

### Install the Package

To install a specific version of the package from the private repository:

```shell
poetry add "git+https://github.com/skand-io/skand-pubsub-provider-python.git#<tag_name>"
```

### Debug Installation Before Publishing

To debug the package installation, specify the filesystem path of the package:

```shell
poetry add <relative_path_to_debugging_package>
```
