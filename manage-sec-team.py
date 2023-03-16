#!/usr/bin/env python3

"""
This script manages a team in each organization that the user running this owns
within the enterprise.  It is meant to be run after `org-admin-promote.py` to
create/update a team with the "security manager" role.

Inputs:
- GitHub API endpoint
- PAT with `enterprise:admin` scope, read from a file called `token.txt`
- `all_orgs.csv` file from `org-admin-promote.py`
- Team name for the security manager team
- List of security manager team members by handle

Outputs:
- Prints the org names the enterprise admin was removed from to `stdout`
"""

# Imports
from defusedcsv import csv
from src import teams, organizations

# Inputs
api_url = "https://api.github.com"  # for GHEC
# api_url = "https://GHES-HOSTNAME-HERE/api/v3"  # for GHES/GHAE

# github_pat = "GITHUB-PAT-HERE"  # if you want to set that manually
with open("token.txt", "r") as f:
    github_pat = f.read().strip()
    f.close()

# List of organizations (filename)
org_list = "all_orgs.csv"

# Team name for the security manager team
sec_team_name = "security-managers"

# List of security manager team members by handle
sec_team_members = ["teammate1", "teammate2", "teammate3"]

# Read in the org list
with open(org_list, "r") as f:
    orgs = list(csv.DictReader(f))

# Set up the headers
headers = {
    "Authorization": "token {}".format(github_pat),
    "Accept": "application/vnd.github.v3+json",
}


if __name__ == "__main__":
    # For each organization, do
    for org in orgs:
        org_name = org["login"]

        # Get the list of teams
        teams_info = teams.list_teams(api_url, headers, org_name)
        teams_list = [team["name"] for team in teams_info]

        # Create the team if it doesn't exist
        if sec_team_name not in teams_list:
            print("Creating team {}".format(sec_team_name))
            teams.create_team(api_url, headers, org_name, sec_team_name)

        # Update that team to have the "security manager" role
        teams.change_team_role(api_url, headers, org_name, sec_team_name)
        print(
            "Team {} updated as a security manager for {}!".format(
                sec_team_name, org_name
            )
        )

        # Get the list of org members, adding the missing ones to the org
        org_members = organizations.list_org_users(api_url, headers, org_name)
        org_members_list = [member["login"] for member in org_members]
        for username in sec_team_members:
            if username not in org_members_list:
                print("Adding {} to {}".format(username, org_name))
                organizations.add_org_user(api_url, headers, org_name, username)

        # Get the list of team members, adding the missing ones to the team and removing the extra ones
        team_members = teams.list_team_members(
            api_url, headers, org_name, sec_team_name
        )
        team_members_list = [member["login"] for member in team_members]
        for username in team_members_list:
            if username not in sec_team_members:
                print("Removing {} from {}".format(username, sec_team_name))
                teams.remove_team_member(
                    api_url, headers, org_name, sec_team_name, username
                )
        for username in sec_team_members:
            if username not in team_members_list:
                print("Adding {} to {}".format(username, sec_team_name))
                teams.add_team_member(
                    api_url, headers, org_name, sec_team_name, username
                )
