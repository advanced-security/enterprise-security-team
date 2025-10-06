#!/usr/bin/env python3

"""Token management utilities."""

import os
from urllib.parse import urlparse
import logging


LOG = logging.getLogger(__name__)


def read_token(token_file: str | None) -> str | None:
    """
    Read a PAT from a file, falling back to GITHUB_TOKEN env var.
    """
    token: str | None = None
    if token_file:
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                token = f.read().strip()
        except FileNotFoundError:
            pass

    if not token:
        token = os.getenv("GITHUB_TOKEN")

    if not token or token == "":
        return None

    return token


def read_lines(input_path: str | None) -> list[str] | None:
    """
    Read a file and return a list of lines.
    """
    if not input_path:
        return None

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except (FileNotFoundError, IsADirectoryError) as err:
        LOG.error(f"⨯ File error: {input_path}: {err}")
        raise err


def add_request_headers(headers: dict[str, str]) -> dict[str, str]:
    """
    Add required headers to the request headers.
    """
    headers = {
        **headers,
        "X-GitHub-Api-Version": "2022-11-28",
        "Accept": "application/vnd.github.v3+json",
    }
    return headers


def validate_ca_bundle(ca_bundle_path: str | None) -> str | None:
    """Validate a user-supplied CA certificate / bundle path.

    Returns the path if it exists and is a file. If None was provided, returns None.
    Raises FileNotFoundError if the file does not exist.

    The returned value can be passed directly to the ``verify`` parameter of ``requests``.
    """
    if ca_bundle_path is None:
        return None
    if ca_bundle_path.strip() == "":
        return None
    if not os.path.isfile(ca_bundle_path):
        LOG.error(f"⨯ CA bundle / certificate file not found: {ca_bundle_path}")
        raise FileNotFoundError(ca_bundle_path)
    return ca_bundle_path


def graphql_api_url_from_server_url(server_url: str) -> str:
    """Generate the GraphQL API from the server URL."""
    if server_url is None:
        return "https://api.github.com/graphql"

    parsed_url = urlparse(server_url)

    if parsed_url.scheme == "":
        raise ValueError("Invalid server URL - no scheme")

    if parsed_url.netloc == "":
        raise ValueError("Invalid server URL - no network location")

    if parsed_url.netloc == "github.com":
        return "https://api.github.com/graphql"

    if parsed_url.netloc.endswith(".ghe.com"):
        return f"{parsed_url.scheme}://api.{parsed_url.netloc}/graphql"

    return f"{server_url}/api/graphql"


def rest_api_url_from_server_url(server_url: str) -> str:
    """Generate the REST API from the server URL."""
    if server_url is None:
        return "https://api.github.com"

    parsed_url = urlparse(server_url)

    if parsed_url.scheme == "":
        raise ValueError("Invalid server URL - no scheme")

    if parsed_url.netloc == "":
        raise ValueError("Invalid server URL - no network location")

    if parsed_url.netloc == "github.com":
        return "https://api.github.com"

    if parsed_url.netloc.endswith(".ghe.com"):
        return f"{parsed_url.scheme}://api.{parsed_url.netloc}"

    return f"{server_url}/api/v3"
