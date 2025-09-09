#!/usr/bin/env python3

"""
This file holds team-related functions
- check if team exists
- create team if not
- add users to team
- assign team custom role on all org repos
"""

import requests
from urllib.parse import quote
from .headers import add_request_headers


# List teams using REST API with pagination
def list_teams(api_endpoint, headers, org):
    """
    List all teams in an organization.
    """
    teams = []
    page = 1
    while True:
        response = requests.get(
            api_endpoint
            + "/orgs/{}/teams?page={}".format(quote(org), quote(str(page))),
            headers=add_request_headers(headers),
        )
        response.raise_for_status()
        teams.extend(response.json())
        if "next" not in response.links:
            break
        page += 1
    return teams


# Create "closed" security manager team using REST API
# Closed teams are visible to users, allowing an understanding of who's responsible
def create_team(api_endpoint, headers, org, team_slug):
    """
    Create a new team in an organization.
    """
    response = requests.post(
        api_endpoint + "/orgs/{}/teams".format(quote(org)),
        json={
            "name": team_slug,
            "description": "Enterprise security manager team",
            "privacy": "closed",
        },
        headers=add_request_headers(headers),
    )
    response.raise_for_status()
    return response.json()


# Change that security manager team's role to "security manager"
def change_team_role(
    api_endpoint, headers, org, team_slug, security_manager_role_id=None, legacy=False
):
    """
    Change the role of a team in an organization to "security manager"
    """
    if legacy:
        response = requests.put(
            api_endpoint
            + "/orgs/{}/security-managers/teams/{}".format(
                quote(org), quote(team_slug)
            ),
            headers=add_request_headers(headers),
        )
        response.raise_for_status()
    else:
        # /orgs/{org}/organization-roles/teams/{team_slug}/{role_id}
        response = requests.put(
            api_endpoint
            + "/orgs/{}/organization-roles/teams/{}/{}".format(
                quote(org), quote(team_slug), security_manager_role_id
            ),
            headers=add_request_headers(headers),
        )
        response.raise_for_status()


def has_team_role(api_endpoint, headers, org, team_slug, role_id, legacy=False):
    """
    Check if a team has a specific role in an organization.
    """
    if legacy:
        # http(s)://HOSTNAME/api/v3/orgs/ORG/security-managers
        response = requests.get(
            api_endpoint + "/orgs/{}/security-managers".format(quote(org)),
            headers=add_request_headers(headers),
        )
        response.raise_for_status()
        roles = response.json()
        return any(role["slug"] == team_slug for role in roles)
    else:
        # Use paginated retrieval for teams assigned a specific organization role.
        # Endpoint pattern: GET /orgs/{org}/organization-roles/{role_id}/teams?page=N
        page = 1
        while True:
            response = requests.get(
                api_endpoint
                + "/orgs/{}/organization-roles/{}/teams?page={}".format(
                    quote(org), quote(str(role_id)), quote(str(page))
                ),
                headers=add_request_headers(headers),
            )
            response.raise_for_status()
            teams_page = response.json()
            if any(team.get("slug") == team_slug for team in teams_page):
                return True
            if "next" not in response.links:
                break
            page += 1
        return False


# List team members using REST API with pagination
def list_team_members(api_endpoint, headers, org, team_slug):
    """
    List all members of a team in an organization.
    """
    members = []
    page = 1
    while True:
        response = requests.get(
            api_endpoint
            + "/orgs/{}/teams/{}/members?page={}".format(
                quote(org), quote(team_slug), quote(str(page))
            ),
            headers=add_request_headers(headers),
        )
        response.raise_for_status()
        members.extend(response.json())
        if "next" not in response.links:
            break
        page += 1
    return members


# Add a user to a team using REST API
def add_team_member(api_endpoint, headers, org, team_slug, username):
    """
    Add a user to a team in an organization.
    """
    response = requests.put(
        api_endpoint
        + "/orgs/{}/teams/{}/memberships/{}".format(
            quote(org), quote(team_slug), quote(username)
        ),
        headers=add_request_headers(headers),
    )
    response.raise_for_status()


# Remove a user from a team using REST API
def remove_team_member(api_endpoint, headers, org, team_slug, username):
    """
    Remove a user from a team in an organization.
    """
    response = requests.delete(
        api_endpoint
        + "/orgs/{}/teams/{}/memberships/{}".format(
            quote(org), quote(team_slug), quote(username)
        ),
        headers=add_request_headers(headers),
    )
    response.raise_for_status()
