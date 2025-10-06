#!/usr/bin/env python3

"""
This file holds enterprise-related functions
"""

from typing import Any
import requests
from .util import add_request_headers


def get_enterprise_id(
    api_endpoint: str,
    enterprise_slug: str,
    headers: dict[str, str],
    verify: str | bool | None = True,
) -> str:
    """
    Get the ID of an enterprise by its slug.
    """
    enterprise_query = """
    query {
      enterprise(slug: "ENTERPRISE_SLUG") {
        id
      }
    }
    """.replace(
        "ENTERPRISE_SLUG", enterprise_slug
    )
    response = requests.post(
        api_endpoint,
        json={"query": enterprise_query},
        headers=add_request_headers(headers),
        verify=verify,
    )
    response.raise_for_status()
    return response.json()["data"]["enterprise"]["id"]


def make_promote_mutation(enterprise_id: str, org_id: str, role: str) -> str:
    """
    Create a GraphQL mutation to promote the Enterprise owner to owner in an organization.
    """
    return (
        """
    mutation {
      updateEnterpriseOwnerOrganizationRole(input: { enterpriseId: "ENTERPRISE_ID", organizationId: "ORG_ID", organizationRole: ORG_ROLE }) {
        clientMutationId
      }
    }
    """.replace(
            "ENTERPRISE_ID", enterprise_id
        )
        .replace("ORG_ID", org_id)
        .replace("ORG_ROLE", role)
    )


def promote_admin(
    api_endpoint: str,
    headers: dict[str, str],
    enterprise_id: str,
    org_id: str,
    role: str,
    verify: str | bool | None = True,
) -> dict[str, Any]:
    """
    Promote an enterprise admin to an organization owner.
    """
    promote_query = make_promote_mutation(enterprise_id, org_id, role)
    response = requests.post(
        api_endpoint,
        json={"query": promote_query},
        headers=add_request_headers(headers),
        verify=verify,
    )
    response.raise_for_status()
    return response.json()
