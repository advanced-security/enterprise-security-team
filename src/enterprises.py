#!/usr/bin/env python3

"""
This file holds enterprise-related functions
"""

import requests
from .headers import add_request_headers


def get_enterprise_id(api_endpoint, enterprise_slug, headers):
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
    )
    response.raise_for_status()
    return response.json()["data"]["enterprise"]["id"]


def make_promote_mutation(enterprise_id, org_id, role):
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


def promote_admin(api_endpoint, headers, enterprise_id, org_id, role):
    """
    Promote an enterprise admin to an organization owner.
    """
    promote_query = make_promote_mutation(enterprise_id, org_id, role)
    response = requests.post(
        api_endpoint,
        json={"query": promote_query},
        headers=add_request_headers(headers),
    )
    response.raise_for_status()
    return response.json()
