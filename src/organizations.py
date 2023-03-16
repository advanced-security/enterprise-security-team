#!/usr/bin/env python3

"""
Organization queries
"""

# Imports
from defusedcsv import csv
import requests


# Count all organizations in the enterprise
def get_total_count(api_endpoint, enterprise_slug, headers):
    total_count_query = (
        """
        query countEnterpriseOrganizations {
          enterprise(slug: "%s") {
            organizations{
              totalCount
            }
          }
        }
        """
        % enterprise_slug
    )
    response = requests.post(
        api_endpoint, json={"query": total_count_query}, headers=headers
    )
    response.raise_for_status()
    return response.json()["data"]["enterprise"]["organizations"]["totalCount"]


# Make query for all organization names in the enterprise
def make_org_query(enterprise_slug, after_cursor=None):
    return """
    query listEnterpriseOrganizations {
      enterprise(slug: SLUG) {
        organizations(first: 100, after:AFTER) {
          edges{
            node{
              id
              createdAt
              login
              email
              viewerCanAdminister
              viewerIsAMember
              repositories {
                totalCount
                totalDiskUsage
              }
            }
            cursor
          }
          pageInfo {
            endCursor
            hasNextPage
          }
        }
      }
    }
    """.replace(
        "SLUG", '"{}"'.format(enterprise_slug)
    ).replace(
        "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )


# List all organizations in the enterprise by name (that the requestor can see)
def list_orgs(api_endpoint, enterprise_slug, headers):
    orgs = []
    after_cursor = None
    while True:
        response = requests.post(
            api_endpoint,
            json={"query": make_org_query(enterprise_slug, after_cursor)},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()["data"]["enterprise"]["organizations"]
        orgs.extend(data["edges"])
        if data["pageInfo"]["hasNextPage"]:
            after_cursor = data["pageInfo"]["endCursor"]
        else:
            break
    return orgs


# Write the orgs to a csv file
def write_orgs_to_csv(orgs, filename):
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "createdAt",
                "login",
                "email",
                "viewerCanAdminister",
                "viewerIsAMember",
                "repositories.totalCount",
                "repositories.totalDiskUsage",
            ]
        )
        for org in orgs:
            writer.writerow(
                [
                    org["node"]["id"],
                    org["node"]["createdAt"],
                    org["node"]["login"],
                    org["node"]["email"],
                    org["node"]["viewerCanAdminister"],
                    org["node"]["viewerIsAMember"],
                    org["node"]["repositories"]["totalCount"],
                    org["node"]["repositories"]["totalDiskUsage"],
                ]
            )


# List the users in an organization, using REST API with pagination
def list_org_users(api_endpoint, headers, org):
    users = []
    page = 1
    while True:
        response = requests.get(
            api_endpoint + "/orgs/{}/members?page={}".format(org, page),
            headers=headers,
        )
        response.raise_for_status()
        users.extend(response.json())
        if "next" not in response.links:
            break
        page += 1
    return users


# Invite a user to an organization
def add_org_user(api_endpoint, headers, org, username):
    response = requests.put(
        api_endpoint + "/orgs/{}/memberships/{}".format(org, username),
        json={"role": "member"},
        headers=headers,
    )
    response.raise_for_status()
    print(response.status_code)
