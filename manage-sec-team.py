#!/usr/bin/env python3

"""
Manages a team in each organization that the user running this owns
within the enterprise.  It is meant to be run after `org-admin-promote.py` to
create/update a team with the "security manager" role.

Inputs:
- GitHub API endpoint (defaults to https://api.github.com)
- PAT with `admin:enterprise` and `admin:org` scope, read from a named file (or GITHUB_TOKEN if that is not provided)
- `all_orgs.csv` file from `org-admin-promote.py`
- Team name for the security manager team
- List of security manager team members by handle

Outputs:
- Prints the members that were added to and removed from the security managers team
"""

from argparse import ArgumentParser
from typing import Any
from defusedcsv import csv
from src import teams, organizations, util
import logging


LOG = logging.getLogger(__name__)


def add_args(parser) -> None:
    """Add arguments to the command line parser."""
    parser.add_argument(
        "--github-url",
        required=False,
        help="GitHub URL for GHES, EMU or data residency",
    )
    parser.add_argument(
        "--token-file",
        required=False,
        help="GitHub Personal Access Token file (or use GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--org-list",
        default="all_orgs.csv",
        help="CSV file of organizations (default: all_orgs.csv)",
    )
    parser.add_argument(
        "--sec-team-name",
        default="security-managers",
        help="Security team name (default: security-managers)",
    )
    parser.add_argument("--sec-team-members", nargs="*", help="Security team members")
    parser.add_argument(
        "--sec-team-members-file", required=False, help="Security team members file"
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy API endpoints to manage the security managers",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Show progress information",
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
        help="Path to a custom CA certificate or bundle (PEM) to trust for TLS (self-signed/internal CAs)",
    )


def make_security_managers_team(
    org_name: str,
    sec_team_name: str,
    api_url: str,
    headers: dict[str, str],
    legacy=False,
    progress=False,
    verify: str | bool | None = True,
) -> None:
    """Create or update the security managers team in the specified organization."""
    security_manager_role_id: str | None = None

    if not legacy:
        org_roles: dict[str, Any] = organizations.list_org_roles(
            api_url, headers, org_name, verify=verify
        )

        # Check if the "security manager" role exists
        if "roles" not in org_roles:
            LOG.error("⨯ Malformed response from GitHub API")
            return

        security_manager_role_id_list = [
            role["id"]
            for role in org_roles["roles"]
            if role["name"] == "security_manager"
        ]
        if not security_manager_role_id_list:
            LOG.error(
                "⨯ Organization {} does not have a security manager role".format(
                    org_name
                )
            )
            return
        security_manager_role_id = security_manager_role_id_list[0]

    # Get the list of teams
    teams_info = teams.list_teams(api_url, headers, org_name, verify=verify)
    teams_list = [team["name"] for team in teams_info]

    # Create the team if it doesn't exist
    if sec_team_name not in teams_list:
        if progress:
            LOG.info("Creating team {}".format(sec_team_name))
        try:
            teams.create_team(api_url, headers, org_name, sec_team_name, verify=verify)
        except Exception as e:
            LOG.error("⨯ Failed to create team {}: {}".format(sec_team_name, e))

    # Update that team to have the "security manager" role
    try:
        # only update it if the team does not already have the role
        if not teams.has_team_role(
            api_url,
            headers,
            org_name,
            sec_team_name,
            security_manager_role_id,
            legacy=legacy,
            verify=verify,
        ):
            teams.change_team_role(
                api_url,
                headers,
                org_name,
                sec_team_name,
                security_manager_role_id,
                legacy=legacy,
                verify=verify,
            )
            if progress:
                LOG.info(
                    "✓ Team {} updated as a security manager for {}".format(
                        sec_team_name, org_name
                    )
                )
        else:
            LOG.debug(
                "✓ Team {} already has the security manager role for {}".format(
                    sec_team_name, org_name
                )
            )
    except Exception as e:
        LOG.error("⨯ Failed to update team {}: {}".format(sec_team_name, e))
        if LOG.getEffectiveLevel() == logging.DEBUG:
            raise e


def add_security_managers_to_team(
    org_name: str,
    sec_team_name: str,
    sec_team_members: list[str],
    api_url: str,
    headers: dict[str, str],
    progress: bool = False,
    verify: str | bool | None = True,
) -> None:
    """Add security managers to the specified team in the organization."""
    # Get the list of org members, adding the missing ones to the org
    org_members = organizations.list_org_users(
        api_url, headers, org_name, verify=verify
    )
    org_members_list = [member["login"] for member in org_members]
    for username in sec_team_members:
        if username not in org_members_list:
            if progress:
                LOG.info("Adding {} to {}".format(username, org_name))
            try:
                organizations.add_org_user(
                    api_url, headers, org_name, username, verify=verify
                )
            except Exception as e:
                LOG.error(
                    "⨯ Failed to add user {} to org {}: {}".format(
                        username, org_name, e
                    )
                )
                return

    # Get the list of team members, adding the missing ones to the team and removing the extra ones
    team_members = teams.list_team_members(
        api_url, headers, org_name, sec_team_name, verify=verify
    )
    team_members_list = [member["login"] for member in team_members]
    for username in team_members_list:
        if username not in sec_team_members:
            if progress:
                LOG.info("Removing {} from {}".format(username, sec_team_name))
            try:
                teams.remove_team_member(
                    api_url, headers, org_name, sec_team_name, username, verify=verify
                )
            except Exception as e:
                LOG.error(
                    "⨯ Failed to remove user {} from team {}: {}".format(
                        username, sec_team_name, e
                    )
                )
                return
    for username in sec_team_members:
        if username not in team_members_list:
            if progress:
                LOG.info("Adding {} to {}".format(username, sec_team_name))
            try:
                teams.add_team_member(
                    api_url, headers, org_name, sec_team_name, username, verify=verify
                )
            except Exception as e:
                LOG.error(
                    "⨯ Failed to add user {} to team {}: {}".format(
                        username, sec_team_name, e
                    )
                )
                return
        else:
            LOG.debug(
                "✓ User {} is already a member of {}".format(username, sec_team_name)
            )


def main() -> None:
    """Command line entrypoint."""
    parser = ArgumentParser(description=__doc__)
    add_args(parser)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    # Read in the org list
    with open(args.org_list, "r") as f:
        orgs = list(csv.DictReader(f))

    github_pat = util.read_token(args.token_file)

    if not github_pat:
        LOG.error("⨯ GitHub Personal Access Token not found")
        return

    if args.sec_team_members and args.sec_team_members_file:
        LOG.error("⨯ Please use either --sec-team-members or --sec-team-members-file")
        return

    sec_team_members = []
    if args.sec_team_members_file:
        sec_team_members = util.read_lines(args.sec_team_members_file)

        if not sec_team_members:
            LOG.error("⨯ No security team members found in file")
            return

    elif args.sec_team_members:
        sec_team_members = args.sec_team_members
    else:
        LOG.error(
            "⨯ Please provide either --sec-team-members or --sec-team-members-file"
        )
        return

    api_url = util.rest_api_url_from_server_url(args.github_url)

    # Optional custom CA bundle / cert file
    verify: str | bool | None = True
    try:
        verify = util.validate_ca_bundle(args.ca_bundle)
    except FileNotFoundError:
        return

    # Set up the headers
    headers = {
        "Authorization": "token {}".format(github_pat),
    }

    # For each organization, do
    for org in orgs:
        org_name = org["login"]

        make_security_managers_team(
            org_name,
            args.sec_team_name,
            api_url,
            headers,
            legacy=args.legacy,
            progress=args.progress,
            verify=verify,
        )
        add_security_managers_to_team(
            org_name,
            args.sec_team_name,
            sec_team_members,
            api_url,
            headers,
            progress=args.progress,
            verify=verify,
        )


if __name__ == "__main__":
    main()
