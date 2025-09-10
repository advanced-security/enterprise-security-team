#!/usr/bin/env python3

"""
Promotes the enterprise admin running this script to owner on every organization
in the specified enterprise. Replaces the legacy `ghe-org-admin-promote` tool and
works across GHES / GHEC / data residency / EMU by using GraphQL API.

Inputs:
- GraphQL API endpoint (default: https://api.github.com/graphql)
- PAT with `admin:enterprise` and `admin:org` scope via --token-file or env var GITHUB_TOKEN
- Enterprise slug

Outputs:
- Summary counts printed to stdout
- Newline-delimited list of previously unmanaged org IDs (default: unmanaged_orgs.txt)
- CSV of all organizations (default: all_orgs.csv)
"""

from argparse import ArgumentParser
from typing import List
from urllib.parse import urlparse
from src import enterprises, organizations, util
import logging


LOG = logging.getLogger(__name__)


def add_args(parser: ArgumentParser) -> None:
    """Add arguments to the command line parser."""
    parser.add_argument(
        "enterprise_slug",
        help="Enterprise slug (after /enterprises/ in URL)",
    )
    parser.add_argument(
        "--github-url",
        required=False,
        help="GitHub URL for GHES, EMU or data residency",
    )
    parser.add_argument(
        "--token-file",
        required=False,
        help="Path to file containing a PAT with admin:enterprise and read:org scope (fallback: GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--unmanaged-orgs",
        default="unmanaged_orgs.txt",
        help="Output file for previously unmanaged organization IDs (default: unmanaged_orgs.txt)",
    )
    parser.add_argument(
        "--orgs-csv",
        default="all_orgs.csv",
        help="Output CSV file listing all organizations in the enterprise (default: all_orgs.csv)",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug logging",
    )


def write_unmanaged_orgs(path: str, unmanaged_org_ids: List[str]) -> None:
    """
    Write the list of unmanaged organization IDs to a file.
    """
    with open(path, "w", encoding="utf-8") as f:
        for oid in unmanaged_org_ids:
            print(oid, file=f)


def promote_all(
    api_url: str, headers: dict[str, str], enterprise_slug: str, unmanaged_out: str
) -> List[str] | None:
    """
    Promote the enterprise admin to owner on all unmanaged organizations.
    """
    total_org_count = organizations.get_total_count(api_url, enterprise_slug, headers)
    if total_org_count == 0:
        LOG.warning("⚠️ No organizations found.")
        return []
    orgs = organizations.list_orgs(api_url, enterprise_slug, headers)
    if len(orgs) != total_org_count:
        LOG.error(
            "⨯ Total count of organizations returned by the query is different from the expected count"
        )
        return None
    LOG.info(
        "Total count of organizations returned by the query is: {}".format(
            total_org_count
        )
    )
    enterprise_id = enterprises.get_enterprise_id(api_url, enterprise_slug, headers)
    unmanaged_orgs = [
        org["node"]["id"] for org in orgs if not org["node"]["viewerCanAdminister"]
    ]
    LOG.info(
        "Total count of unmanaged organizations to be promoted on: {}".format(
            len(unmanaged_orgs)
        )
    )
    for i, org_id in enumerate(unmanaged_orgs):
        LOG.info(
            "Promoting to owner on organization: {} [{}/{}]".format(
                org_id, i + 1, len(unmanaged_orgs)
            )
        )
        enterprises.promote_admin(api_url, headers, enterprise_id, org_id, "OWNER")
    write_unmanaged_orgs(unmanaged_out, unmanaged_orgs)
    LOG.info(
        "Total count of newly managed organizations is: {}".format(len(unmanaged_orgs))
    )
    return unmanaged_orgs


def main() -> None:
    """Command line entrypoint."""
    parser = ArgumentParser(description=__doc__)
    add_args(parser)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    api_url = (
        util.graphql_api_url_from_server_url(args.github_url)
        if args.github_url
        else "https://api.github.com/graphql"
    )

    github_pat = util.read_token(args.token_file)
    headers: dict[str, str] = {
        "Authorization": f"token {github_pat}",
    }

    if (
        promote_all(
            api_url,
            headers,
            args.enterprise_slug,
            args.unmanaged_orgs,
        )
        is None
    ):
        LOG.error("⨯ Promotion failed")
        return

    # Refresh and write all orgs CSV after promotions
    orgs = organizations.list_orgs(api_url, args.enterprise_slug, headers)
    organizations.write_orgs_to_csv(orgs, args.orgs_csv)


if __name__ == "__main__":  # pragma: no cover
    main()
