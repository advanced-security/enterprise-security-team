#!/usr/bin/env python3

"""
This script removes the enterprise admin running this script from all of the 
organizations listed in `unmanaged_orgs.csv`.  It is meant to be run after
`org-admin-promote.py` to remove the enterprise admin from all organizations
that they were promoted to an owner of.

Inputs:
- GitHub API endpoint
- PAT with `enterprise:admin` scope, read from a file called `token.txt`
- Enterprise slug (the string that comes after `/enterprises/` in the URL)
- `unmanaged_orgs.csv` file from `org-admin-promote.py`

Outputs:
- Prints the org names the enterprise admin was removed from to `stdout`
"""

# Imports
from src import enterprises

# Set API endpoint
graphql_endpoint = "https://api.github.com/graphql"  # for GHEC
# graphql_endpoint = "https://GHES-HOSTNAME-HERE/api/graphql" # for GHES/GHAE

# github_pat = "GITHUB-PAT-HERE"  # if you want to set that manually
with open("token.txt", "r") as f:
    github_pat = f.read().strip()
    f.close()

enterprise_slug = "ENTERPRISE-SLUG-HERE"

# Set up the headers
headers = {
    "Authorization": "token {}".format(github_pat),
    "Accept": "application/vnd.github.v3+json",
}

# Do the things!
if __name__ == "__main__":
    # Get the enterprise ID
    enterprise_id = enterprises.get_enterprise_id(
        graphql_endpoint, enterprise_slug, headers
    )

    # Get the list of unmanaged orgs
    with open("unmanaged_orgs.txt", "r") as f:
        unmanaged_orgs = f.read().splitlines()

    # Print the total count of orgs to demote admin from
    print("Total count of orgs to demote admin from: {}".format(len(unmanaged_orgs)))

    # Remove the enterprise admin running this from all of the unmanaged orgs
    for i, org_id in enumerate(unmanaged_orgs):
        print("Removing from organization: {} [{}/{}]".format(org_id, i+1, len(unmanaged_orgs)))
        enterprises.promote_admin(
            graphql_endpoint, headers, enterprise_id, org_id, "UNAFFILIATED"
        )
