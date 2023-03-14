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
from src import organizations
import os

# Read in config values
if os.environ.get("GITHUB_GRAPHQL_URL") is None:
    api_endpoint = "https://api.github.com/graphql"
else:
    api_endpoint = os.environ.get("GITHUB_GRAPHQL_URL")

with open("token.txt", "r") as f:
    github_pat = f.read().strip()

enterprise_slug = "octodemo"


# Set up the headers
headers = {
    "Authorization": "token {}".format(github_pat),
    "Accept": "application/vnd.github.v3+json",
}

# Do the things!
if __name__ == "__main__":
    # Get the total count, test that function
    total_org_count = organizations.get_total_count(
        api_endpoint, enterprise_slug, headers
    )

    # Get the organization data, make sure it's the same length as the total count
    orgs = organizations.list_orgs(api_endpoint, enterprise_slug, headers)
    assert len(orgs) == total_org_count

    # Print a little data
    print("Total count of organizations returned by the query is: {}".format(len(orgs)))

    # Write the data to a CSV file
    organizations.write_orgs_to_csv(orgs)
