#!/usr/bin/env python3

"""
This file holds the main function that does all the things.

Inputs:
- GitHub API endpoint (assumes github.com if not specified or run within GHES/GHAE)
- PAT with `enterprise:admin` scope
- Enterprise slug

Outputs:
- CSV file of all organizations in the enterprise
"""

# Imports
from src import enterprises, organizations
import os

# Read in config values
if os.environ.get("GITHUB_GRAPHQL_URL") is None:
    api_endpoint = "https://api.github.com/graphql"
else:
    api_endpoint = os.environ.get("GITHUB_GRAPHQL_URL")

with open("token.txt", "r") as f:
    github_pat = f.read().strip()

enterprise_slug = "GitHub"


# Set up the headers
headers = {
    "Authorization": "token {}".format(github_pat),
    "Accept": "application/vnd.github.v3+json",
}

# Do the things!
if __name__ == "__main__":
    # Get the total count of organizations
    total_org_count = organizations.get_total_count(
        api_endpoint, enterprise_slug, headers
    )

    # Get the organization data, make sure it's the same length as the total count
    orgs = organizations.list_orgs(api_endpoint, enterprise_slug, headers)
    assert len(orgs) == total_org_count

    # Get the enterprise ID
    enterprise_id = enterprises.get_enterprise_id(
        api_endpoint, enterprise_slug, headers
    )
    print(enterprise_id)

    # Promote enterprise admin running this to an organization owner of all orgs
    unmanaged_orgs = []
    for org in orgs:
        if org["node"]["viewerCanAdminister"] is False:
            unmanaged_orgs.append(org["node"]["id"])
            print("Promoting to owner on organization: {}".format(org["node"]["login"]))
            enterprises.promote_admin(
                api_endpoint, headers, enterprise_id, org["node"]["id"]
            )

    # Print a little data
    print("Total count of organizations returned by the query is: {}".format(len(orgs)))
    print(
        "Total count of newly managed organizations is: {}".format(len(unmanaged_orgs))
    )

    # Write the data to a CSV file
    organizations.write_orgs_to_csv(orgs)
