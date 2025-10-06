#!/usr/bin/env python3

"""
Organization queries
"""

from typing import Any
from defusedcsv import csv
from urllib.parse import quote
import requests
from .util import add_request_headers
import logging

LOG = logging.getLogger(__name__)


def format_errors(errors: list[dict[str, Any]]) -> str:
    """
    Format the errors returned by the API.
    """
    formatted = []
    for error in errors:
        # errors have fields: 'type', 'locations' (a list of a dict with 'line' and 'column' fields), 'message'
        locations = ", ".join(
            f"line {loc['line']}, column {loc['column']}"
            for loc in error.get("locations", [])
        )
        formatted.append(f"Error {error['type']}: {error['message']} (at {locations})")
    return "\n".join(formatted)


# Count all organizations in the enterprise
def get_total_count(
    api_endpoint: str,
    enterprise_slug: str,
    headers: dict[str, str],
    verify: str | bool | None = True,
) -> int:
    """
    Get the total count of organizations in the enterprise.
    """
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
        api_endpoint,
        json={"query": total_count_query},
        headers=add_request_headers(headers),
        verify=verify,
    )
    response.raise_for_status()
    try:
        return response.json()["data"]["enterprise"]["organizations"]["totalCount"]
    except (KeyError, TypeError):
        LOG.error("⨯ Failed to get total count of organizations")
        return 0


# Make query for all organization names in the enterprise
def make_org_query(enterprise_slug: str, after_cursor: str | None = None) -> str:
    """
    Create a GraphQL query to list all organizations in the enterprise.
    """
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


def list_orgs(
    api_endpoint: str,
    enterprise_slug: str,
    headers: dict[str, str],
    verify: str | bool | None = True,
) -> list[dict[str, Any]]:
    """
    List all organizations in the enterprise by name.
    """
    orgs = []
    after_cursor = None
    while True:
        response = requests.post(
            api_endpoint,
            json={"query": make_org_query(enterprise_slug, after_cursor)},
            headers=add_request_headers(headers),
            verify=verify,
        )
        response.raise_for_status()
        data = response.json()
        try:
            org_data = data["data"]["enterprise"]["organizations"]
            orgs.extend(org_data["edges"])
            if org_data["pageInfo"]["hasNextPage"]:
                after_cursor = org_data["pageInfo"]["endCursor"]
            else:
                break
        except (KeyError, TypeError):
            LOG.error("⨯ Failed to get organizations")
            if "errors" in data:
                LOG.error(format_errors(data["errors"]))
            break
    return orgs


def write_orgs_to_csv(orgs: list[dict[str, Any]], filename: str):
    """
    Write the list of organizations to a CSV file.
    """
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


def list_org_users(
    api_endpoint: str,
    headers: dict[str, str],
    org: str,
    verify: str | bool | None = True,
) -> list[dict[str, Any]]:
    """
    List all users in an organization, using REST API with pagination.
    """
    users = []
    page = 1
    while True:
        response = requests.get(
            api_endpoint
            + "/orgs/{}/members?page={}".format(quote(org), quote(str(page))),
            headers=add_request_headers(headers),
            verify=verify,
        )
        response.raise_for_status()
        users.extend(response.json())
        if "next" not in response.links:
            break
        page += 1
    return users


def add_org_user(
    api_endpoint: str,
    headers: dict[str, str],
    org: str,
    username: str,
    verify: str | bool | None = True,
) -> None:
    """
    Invite a user to an organization.
    """
    response = requests.put(
        api_endpoint + "/orgs/{}/memberships/{}".format(quote(org), quote(username)),
        json={"role": "member"},
        headers=add_request_headers(headers),
        verify=verify,
    )
    response.raise_for_status()
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(response.json())


def list_org_roles(
    api_endpoint: str,
    headers: dict[str, str],
    org: str,
    verify: str | bool | None = True,
) -> dict[str, Any]:
    """
    List all roles in an organization.
    """
    response = requests.get(
        api_endpoint + "/orgs/{}/organization-roles".format(quote(org)),
        headers=add_request_headers(headers),
        verify=verify,
    )
    response.raise_for_status()
    return response.json()
