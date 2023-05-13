"""
test_query.py contains tests for the query.py module.
"""
import datetime
import pytest
from webapp.database import Base, engine, create_tables
from webapp.manage import create_organization, create_user, add_user_to_organization
from webapp.query import get_users_of_organization
from webapp.manage import create_access_token, revoke_access_token
from webapp.query import get_valid_tokens_of_organization, get_revoked_token_hashes
from webapp.utils import current_timestamp


@pytest.fixture(scope="function", name="setup_database")
def fixture_setup_database():
    create_tables()
    yield
    # Clean up the database after each test
    Base.metadata.drop_all(engine)


def test_get_users_of_organization_success(setup_database):  # pylint: disable=unused-argument
    org_name = "Test Organization"
    country_code = "USA"
    organization = create_organization(org_name, country_code)

    username1 = "testuser1"
    email1 = "testuser1@example.com"
    user1 = create_user(username1, email1)

    username2 = "testuser2"
    email2 = "testuser2@example.com"
    user2 = create_user(username2, email2)

    add_user_to_organization(user1.id, organization.id)
    add_user_to_organization(user2.id, organization.id)

    users = get_users_of_organization(organization.id)

    assert len(users) == 2
    assert [user1.id, username1, email1] in users
    assert [user2.id, username2, email2] in users


def test_get_users_of_organization_custom_columns(setup_database):  # pylint: disable=W0613
    org_name = "Test Organization"
    country_code = "USA"
    organization = create_organization(org_name, country_code)

    username = "testuser"
    email = "testuser@example.com"
    company = "Test Company"
    location = "Test City"
    social_profile = "https://example.com/testuser"
    user = create_user(username, email, company, location, social_profile)

    add_user_to_organization(user.id, organization.id)

    users = get_users_of_organization(organization.id, columns=['id', 'location', 'company'])

    assert len(users) == 1
    assert [user.id, location, company] in users


def test_get_users_of_organization_invalid_id(setup_database):  # pylint: disable=unused-argument
    users = get_users_of_organization(999)
    assert users == []


def test_get_valid_tokens_of_organization_success(setup_database):  # pylint: disable=W0613
    org_name = "Test Organization"
    country_code = "USA"
    organization = create_organization(org_name, country_code)

    username = "testuser"
    email = "testuser@example.com"
    user = create_user(username, email)

    add_user_to_organization(user.id, organization.id)

    token1 = create_access_token(user.id, organization.id, "token1")
    token2 = create_access_token(user.id, organization.id, "token2")

    valid_tokens = get_valid_tokens_of_organization(organization.id)
    valid_hashes = [token.token_hash for token in valid_tokens]

    assert len(valid_tokens) == 2
    assert token1.token_hash in valid_hashes
    assert token2.token_hash in valid_hashes


def test_get_revoked_tokens_in_time_range_success(setup_database):  # pylint: disable=W0613
    org_name = "Test Organization"
    country_code = "USA"
    organization = create_organization(org_name, country_code)

    username = "testuser"
    email = "testuser@example.com"
    user = create_user(username, email)

    add_user_to_organization(user.id, organization.id)

    token1 = create_access_token(user.id, organization.id, 'token1')
    token2 = create_access_token(user.id, organization.id, 'token2')

    revoke_access_token(token1.id)

    start_time = current_timestamp() - datetime.timedelta(hours=1)
    end_time = current_timestamp() + datetime.timedelta(hours=1)

    revoked_hashes = get_revoked_token_hashes(start_time, end_time)

    assert len(revoked_hashes) == 1
    assert token1.token_hash in revoked_hashes
    assert token2.token_hash not in revoked_hashes


def test_get_revoked_tokens_in_time_range_no_tokens(setup_database):  # pylint: disable=W0613
    start_time = current_timestamp() - datetime.timedelta(hours=1)
    end_time = current_timestamp() + datetime.timedelta(hours=1)

    revoked_tokens = get_revoked_token_hashes(start_time, end_time)

    assert revoked_tokens == []
