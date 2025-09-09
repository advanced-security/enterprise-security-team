#!/usr/bin/env python3

"""Token management utilities."""

import os


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
