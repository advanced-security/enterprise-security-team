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
from src import enterprises, util
import logging


LOG = logging.getLogger(__name__)


def add_args(parser: ArgumentParser) -> None:
    """Add arguments to the command line parser."""
    parser.add_argument(
        "enterprise_slug",
        help="Enterprise slug (after /enterprises/ in the URL)",
    )
    parser.add_argument(
        "--github-url",
        required=False,
        help="GitHub URL for GHES, EMU or data residency",
    )
    parser.add_argument(
        "--token-file",
        required=False,
        help="File containing a GitHub Personal Access Token with admin:enterprise and read:org scope (or use GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--unmanaged-orgs",
        default="unmanaged_orgs.txt",
        help="Path to newline-delimited list of organization IDs to demote from (default: unmanaged_orgs.txt)",
    )
    parser.add_argument(
        "--progress",
        "-p",
        action="store_true",
        help="Show progress during demotion",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--ca-bundle",
        required=False,
        help="Path to a custom CA certificate or bundle (PEM) for TLS verification (self-signed/internal roots)",
    )


def demote_admin(
    api_url: str,
    headers: dict[str, str],
    enterprise_id: str,
    org_ids: Iterable[str],
    progress: bool = False,
    verify: str | bool | None = True,
) -> None:
    """Demote the enterprise admin from each organization ID provided."""
    org_ids_list = list(org_ids)
    LOG.info("Total count of orgs to demote admin from: {}".format(len(org_ids_list)))
    for i, org_id in enumerate(org_ids_list):
        if progress:
            LOG.info(
                "Removing from organization: {} [{}/{}]".format(
                    org_id, i + 1, len(org_ids_list)
                )
            )
        enterprises.promote_admin(
            api_url, headers, enterprise_id, org_id, "UNAFFILIATED", verify=verify
        )


def main() -> None:
    """Command line entrypoint."""
    parser = ArgumentParser(description=__doc__)
    add_args(parser)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    github_pat = util.read_token(args.token_file)

    api_url = util.graphql_api_url_from_server_url(args.github_url)

    if not github_pat:
        LOG.error("⨯ GitHub Personal Access Token not found")
        return

    headers: dict[str, str] = {
        "Authorization": f"token {github_pat}",
    }

    # Optional custom CA bundle / cert file
    verify: str | bool | None = True
    try:
        verify = util.validate_ca_bundle(args.ca_bundle)
    except FileNotFoundError:
        return

    enterprise_id = enterprises.get_enterprise_id(
        api_url, args.enterprise_slug, headers, verify=verify
    )

    unmanaged_orgs = util.read_lines(args.unmanaged_orgs)

    if not unmanaged_orgs:
        LOG.error("⨯ No unmanaged organizations found to demote admin from")
        return

    demote_admin(
        api_url, headers, enterprise_id, unmanaged_orgs, args.progress, verify=verify
    )


if __name__ == "__main__":  # pragma: no cover
    main()
