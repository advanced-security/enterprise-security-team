#!/usr/bin/env python3

"""
Removes (demotes) the enterprise admin running this script from each organization
listed in a file (default: unmanaged_orgs.txt). It is meant to be run after
`org-admin-promote.py` to undo temporary organization ownership grants.

Inputs:
- GraphQL API endpoint (defaults to https://api.github.com/graphql)
- PAT with `admin:enterprise` and `admin:org` scope, provided via --token-file or $GITHUB_TOKEN
- Enterprise slug (the segment after /enterprises/ in the URL)
- A newline-delimited file of organization IDs (default: unmanaged_orgs.txt)

Outputs:
- Prints progress lines for each organization demotion
"""

from argparse import ArgumentParser
from typing import Iterable, List
from src import enterprises, github_token
import logging

LOG = logging.getLogger(__name__)


def add_args(parser: ArgumentParser) -> None:
    """Add arguments to the command line parser."""
    parser.add_argument(
        "--api-url",
        default="https://api.github.com/graphql",
        help="GitHub GraphQL API endpoint (https://github-hostname-here/api/graphql for GHES, EMU or data residency)",
    )
    parser.add_argument(
        "--token-file",
        required=False,
        help="File containing a GitHub Personal Access Token with admin:enterprise and read:org scope (or use GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--enterprise-slug",
        required=True,
        help="Enterprise slug (after /enterprises/ in the URL)",
    )
    parser.add_argument(
        "--unmanaged-orgs",
        default="unmanaged_orgs.txt",
        help="Path to newline-delimited list of organization IDs to demote from",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug logging",
    )


def read_unmanaged_org_ids(path: str) -> List[str]:
    """Return a list of non-empty lines from the unmanaged orgs file."""
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def demote_admin(
    api_url: str, headers: dict[str, str], enterprise_id: str, org_ids: Iterable[str]
) -> None:
    """Demote the enterprise admin from each organization ID provided."""
    org_ids_list = list(org_ids)
    LOG.info("Total count of orgs to demote admin from: {}".format(len(org_ids_list)))
    for i, org_id in enumerate(org_ids_list):
        LOG.info(
            "Removing from organization: {} [{}/{}]".format(
                org_id, i + 1, len(org_ids_list)
            )
        )
        enterprises.promote_admin(
            api_url, headers, enterprise_id, org_id, "UNAFFILIATED"
        )


def main() -> None:
    """Command line entrypoint."""
    parser = ArgumentParser(description=__doc__)
    add_args(parser)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    github_pat = github_token.read_token(args.token_file)

    if not github_pat:
        LOG.error("⨯ GitHub Personal Access Token not found")
        return

    headers: dict[str, str] = {
        "Authorization": f"token {github_pat}",
    }

    enterprise_id = enterprises.get_enterprise_id(
        args.api_url, args.enterprise_slug, headers
    )

    unmanaged_orgs = read_unmanaged_org_ids(args.unmanaged_orgs)
    demote_admin(args.api_url, headers, enterprise_id, unmanaged_orgs)


if __name__ == "__main__":  # pragma: no cover
    main()
