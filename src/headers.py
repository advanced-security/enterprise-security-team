#! /usr/bin/env python3

"""Add headers needed for the GitHub REST API."""


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
