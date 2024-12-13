import os

# for testing
LOCALSTACK_HOSTNAME = os.getenv("LOCALSTACK_HOSTNAME")

# k8s (An application deploys to K8S, which injects environment variables there.)
KUBERNETES_SERVICE_HOST = os.getenv("KUBERNETES_SERVICE_HOST")
KUBERNETES_SERVICE_PORT = os.getenv("KUBERNETES_SERVICE_PORT")
