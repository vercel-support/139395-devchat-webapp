"""
test_management.py contains tests for the functions in management.py.
"""
import pytest
from webapp.model import Organization, organization_user, Role
from webapp.controller import create_organization
from webapp.model import User
from webapp.controller import create_user, add_user_to_organization, assign_role_to_user
from webapp.model import AccessKey
from webapp.controller import create_access_key, revoke_access_key
from webapp.utils import verify_access_key


def test_create_organization_success(database):
    name = "Test-Organization"
    country_code = "USA"
    organization = create_organization(database, name, country_code)

    assert organization.name == name
    assert organization.country_code == country_code
    assert organization.balance == 0
    assert organization.currency == "USD"

    db_organization = database.query(Organization).filter_by(id=organization.id).first()

    assert db_organization is not None
    assert db_organization.name == name
    assert db_organization.country_code == country_code
    assert db_organization.balance == 0
    assert db_organization.currency == "USD"


def test_create_organization_duplicate_name(database):
    name = "Duplicate-Organization"
    country_code = "US"
    create_organization(database, name, country_code)

    with pytest.raises(Exception):
        create_organization(database, name, country_code)


def test_create_user_success(database):
    username = "testuser"
    email = "testuser@example.com"
    company = "Test Company"
    location = "Test City"
    social_profile = "https://example.com/testuser"

    user = create_user(database, username, email, company, location, social_profile)

    assert user.username == username
    assert user.email == email
    assert user.company == company
    assert user.location == location
    assert user.social_profile == social_profile

    db_user = database.query(User).filter_by(id=user.id).first()

    assert db_user is not None
    assert db_user.username == username
    assert db_user.email == email
    assert db_user.company == company
    assert db_user.location == location
    assert db_user.social_profile == social_profile


def test_create_user_duplicate_username(database):
    username = "duplicateuser"
    email = "duplicateuser@example.com"

    create_user(database, username, email)

    with pytest.raises(Exception):
        create_user(database, username, "anotheremail@example.com")


def test_create_user_invalid_email(database):
    with pytest.raises(ValueError) as error:
        create_user(database, "testuser", "invalid_email")
        assert str(error) == "Invalid email provided."


def test_add_user_to_organization_success(database):
    org_name = "Test-Organization"
    country_code = "USA"
    organization = create_organization(database, org_name, country_code)

    username = "testuser"
    email = "testuser@example.com"
    user = create_user(database, username, email)

    result = add_user_to_organization(database, user.id, organization.id)

    assert result is True

    db_organization = database.query(Organization).filter_by(id=organization.id).first()
    assert db_organization is not None
    users = db_organization.users

    assert len(users) == 1
    assert users[0].id == user.id


def test_add_user_to_organization_invalid_ids(database):
    with pytest.raises(ValueError) as error:
        add_user_to_organization(database, 999, 999)
        assert str(error) == "User or organization does not exist."


def test_add_user_to_organization_with_role(database):
    org_name = "Test-Organization"
    country_code = "USA"
    organization = create_organization(database, org_name, country_code)

    username = "testuser"
    email = "testuser@example.com"
    user = create_user(database, username, email)

    result = add_user_to_organization(database, user.id, organization.id, role=Role.OWNER)

    assert result is True

    db_organization = database.query(Organization).filter_by(id=organization.id).first()
    assert db_organization is not None
    users = db_organization.users

    assert len(users) == 1
    assert users[0].id == user.id

    user_organization = (
        database.query(organization_user)
        .filter(organization_user.c.user_id == user.id)
        .filter(organization_user.c.organization_id == organization.id)
        .first()
    )

    assert user_organization is not None
    assert user_organization.role == Role.OWNER


def test_assign_role_to_user(database):
    org_name = "Test-Organization"
    country_code = "USA"
    organization = create_organization(database, org_name, country_code)

    username = "testuser"
    email = "testuser@example.com"
    user = create_user(database, username, email)

    add_user_to_organization(database, user.id, organization.id)

    result = assign_role_to_user(database, user.id, organization.id, role=Role.OWNER)

    assert result is True

    user_organization = (
        database.query(organization_user)
        .filter(organization_user.c.user_id == user.id)
        .filter(organization_user.c.organization_id == organization.id)
        .first()
    )

    assert user_organization is not None
    assert user_organization.role == Role.OWNER


def test_create_key_success(database):
    org_name = "Test-Organization"
    country_code = "USA"
    organization = create_organization(database, org_name, country_code)

    username = "testuser"
    email = "testuser@example.com"
    user = create_user(database, username, email)

    add_user_to_organization(database, user.id, organization.id)

    key_name = "Test Key"
    key, value = create_access_key(database, user.id, organization.id, key_name)

    assert key.user_id == user.id
    assert key.organization_id == organization.id
    assert key.name == key_name
    assert key.revoke_time is None

    db_key = database.query(AccessKey).filter_by(id=key.id).first()

    assert db_key is not None
    assert db_key.user_id == user.id
    assert db_key.organization_id == organization.id
    assert db_key.name == key_name
    assert db_key.revoke_time is None

    # Verify the generated access key
    org_id_from_key = verify_access_key(value)
    assert org_id_from_key == organization.id


def test_revoke_key_success(database):
    org_name = "Test-Organization"
    country_code = "USA"
    organization = create_organization(database, org_name, country_code)

    username = "testuser"
    email = "testuser@example.com"
    user = create_user(database, username, email)

    add_user_to_organization(database, user.id, organization.id)

    key_name = "Test Key"
    key, _ = create_access_key(database, user.id, organization.id, key_name)

    result = revoke_access_key(database, key.id)

    assert result is True

    db_key = database.query(AccessKey).filter_by(id=key.id).first()

    assert db_key is not None
    assert db_key.revoke_time is not None


def test_revoke_key_invalid_id(database):
    with pytest.raises(ValueError) as error:
        revoke_access_key(database, 999)
        assert str(error) == "Key does not exist."
