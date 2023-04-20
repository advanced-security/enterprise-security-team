#!/usr/bin/env python3

"""
This script "replaces" `ghe-org-admin-promote` from GHES to be able to also run 
in GHEC/GHAE.  It promotes the enterprise admin running this script to an 
organization owner of all organizations in the enterprise.

Inputs:
- GitHub API endpoint
- PAT with `enterprise:admin` scope, read from a file called `token.txt`
- Enterprise slug (the string that comes after `/enterprises/` in the URL)

Outputs:
- Total count of orgs to `stdout`
- Total count of orgs that the enterprise owner now owns to `stdout`
- A text file of all (previously) unmanaged orgs to `unmanaged_orgs.txt`
- A CSV of all organizations in the enterprise to `orgs.csv`
"""

# Imports
from src import enterprises, organizations

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
    # Get the total count of organizations
    total_org_count = organizations.get_total_count(
        graphql_endpoint, enterprise_slug, headers
    )

    # Get the organization data, make sure it's the same length as the total count
    orgs = organizations.list_orgs(graphql_endpoint, enterprise_slug, headers)
    assert len(orgs) == total_org_count

    # Print a little data
    print(
        "Total count of organizations returned by the query is: {}".format(
            total_org_count
        )
    )

    # Get the enterprise ID
    enterprise_id = enterprises.get_enterprise_id(
        graphql_endpoint, enterprise_slug, headers
    )

    # Promote enterprise admin running this to an organization owner of all orgs
    unmanaged_orgs = [
        org["node"]["id"] for org in orgs if not org["node"]["viewerCanAdminister"]
    ]
    print(
        "Total count of unmanaged organizations to be promoted on: {}".format(
            len(unmanaged_orgs)
        )
    )
    for i, org_id in enumerate(unmanaged_orgs):
        print(
            "Promoting to owner on organization: {} [{}/{}]".format(
                org_id, i + 1, len(unmanaged_orgs)
            )
        )
        enterprises.promote_admin(
            graphql_endpoint, headers, enterprise_id, org_id, "OWNER"
        )

    with open("unmanaged_orgs.txt", "w") as f:
        for i in unmanaged_orgs:
            f.write(i)
            f.write("\n")
        f.close()

    # Print a little data
    print(
        "Total count of newly managed organizations is: {}".format(len(unmanaged_orgs))
    )

    # Refresh that data
    orgs = organizations.list_orgs(graphql_endpoint, enterprise_slug, headers)

    # Write the orgs to a CSV
    organizations.write_orgs_to_csv(orgs, "all_orgs.csv")
