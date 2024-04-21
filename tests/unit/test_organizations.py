"""
Unit tests to test writing regex rules from DDB
"""
import os
import json
import moto
import boto3
import pytest

################################################
#                    Fixture                   #
################################################

@pytest.fixture(autouse=True)
def get_organization_map():
    cwd = os.path.dirname(os.path.realpath(__file__))
    organizations_map_path = os.path.join(cwd, "aws_organizations_details.json")
    with open(organizations_map_path, "r") as fp:
        return json.load(fp)

@pytest.fixture(autouse=True)
def organizations_client(set_aws_creds):
    """
    Fixture to mock AWS Organizations client
    """
    with moto.mock_organizations():
        yield boto3.client("organizations")

@pytest.fixture(autouse=True)
def create_aws_organization(get_organization_map, organizations_client):
    parent_ou_id = organizations_client.create_organization()["Organization"]["Id"]
    create_aws_ous_accounts(get_organization_map, parent_ou_id)

################################################
#                    Helpers                   #
################################################

def create_aws_ous_accounts(aws_organizations_map: dict, root_ou_id: str, parent_ou_id: str = "") -> None:
    """
    Fixture to setup AWS mock organizations by creating:
        1. Creating an AWS organization
        2. Creating AWS organizations units (OUs)
        3. Creating AWS accounts
        4. Moving those AWS accounts under their designated OU
    """
    for organization_resource in aws_organizations_map:

        if organization_resource["type"] == "ORGANIZATIONAL_UNIT":
            # Create OU
            nest_ou_id = organizations_client.create_organizational_unit(
                ParentId = parent_ou_id if parent_ou_id else root_ou_id,
                Name = organization_resource["name"]
            )["OrganizationalUnit"]["Id"]

            # Recursively setup OU
            if organization_resource["children"]:
                create_aws_ous_accounts(
                    organization_resource["children"],
                    root_ou_id,
                    nest_ou_id
                )

        # Create account
        account_id = organizations_client.create_account(
            Email = f"{organization_resource['name']}@testing.com",
            AccountName = organization_resource["name"]
        )["CreateAccountStatus"]["AccountId"]

        # Move account to OU
        organizations_client.move_account(
            AccountId = account_id,
            SourceParentId = root_ou_id,
            DestinationParentId = parent_ou_id
        )


# def test_get_active_aws_accounts_include_all_organiational_units(get_organizations_details) -> None:
#     pass

# def test_get_active_aws_accounts_exclue_specific_organizational_units(get_organizations_details) -> None:
#     pass

# @moto.mock_organizations
# def test_get_active_aws_accounts_filter_suspended(organizations_client, get_organizations_details) -> None:
#     pass