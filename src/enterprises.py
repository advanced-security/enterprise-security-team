#!/usr/bin/env python3

"""
This file holds enterprise-related functions
"""

# Imports
import requests


# Get enterprise ID
def get_enterprise_id(api_endpoint, enterprise_slug, headers):
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
        api_endpoint, json={"query": enterprise_query}, headers=headers
    )
    response.raise_for_status()
    return response.json()["data"]["enterprise"]["id"]


# Make promote mutation
def make_promote_mutation(enterprise_id, org_id, role):
    return (
        """
    mutation {
      updateEnterpriseOwnerOrganizationRole(input: { enterpriseId: "ENTERPRISE_ID", organizationId: "ORG_ID", organizationRole: "ORG_ROLE" }) {
        clientMutationId
      }
    }
    """.replace(
            "ENTERPRISE_ID", enterprise_id
        )
        .replace("ORG_ID", org_id)
        .replace("ORG_ROLE", role)
    )


# Promote an enterprise admin to an organization owner
def promote_admin(api_endpoint, headers, enterprise_id, org_id, role):
    promote_query = make_promote_mutation(enterprise_id, org_id, role)
    response = requests.post(
        api_endpoint, json={"query": promote_query}, headers=headers
    )
    response.raise_for_status()
    return response.json()
