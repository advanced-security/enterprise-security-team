#!/usr/bin/env python3

"""
This file holds team-related functions
- check if team exists
- create team if not
- add users to team
- assign team custom role on all org repos
"""

# Imports
import requests


# List teams using REST API with pagination
def list_teams(api_endpoint, headers, org):
    teams = []
    page = 1
    while True:
        response = requests.get(
            api_endpoint + "/orgs/{}/teams?page={}".format(org, page),
            headers=headers,
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
    response = requests.post(
        api_endpoint + "/orgs/{}/teams".format(org),
        json={
            "name": team_slug,
            "description": "Enterprise security manager team",
            "privacy": "closed",
        },
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


# Change that security manager team's role to "security manager"
def change_team_role(api_endpoint, headers, org, team_slug):
    response = requests.put(
        api_endpoint + "/orgs/{}/security-managers/teams/{}".format(org, team_slug),
        headers=headers,
    )
    response.raise_for_status()


# List team members using REST API with pagination
def list_team_members(api_endpoint, headers, org, team_slug):
    members = []
    page = 1
    while True:
        response = requests.get(
            api_endpoint
            + "/orgs/{}/teams/{}/members?page={}".format(org, team_slug, page),
            headers=headers,
        )
        response.raise_for_status()
        members.extend(response.json())
        if "next" not in response.links:
            break
        page += 1
    return members


# Add a user to a team using REST API
def add_team_member(api_endpoint, headers, org, team_slug, username):
    response = requests.put(
        api_endpoint
        + "/orgs/{}/teams/{}/memberships/{}".format(org, team_slug, username),
        headers=headers,
    )
    response.raise_for_status()


# Remove a user from a team using REST API
def remove_team_member(api_endpoint, headers, org, team_slug, username):
    response = requests.delete(
        api_endpoint
        + "/orgs/{}/teams/{}/memberships/{}".format(org, team_slug, username),
        headers=headers,
    )
    response.raise_for_status()
