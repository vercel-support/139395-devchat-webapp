from fastapi.testclient import TestClient
from webapp.api.main import app

client = TestClient(app)


def test_create_organization():
    response = client.post("/organizations/", json={"name": "Test Org", "country_code": "US"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Org"
    assert response.json()["country_code"] == "US"


def test_list_users():
    # Create a test organization using the create_organization API
    org_response = client.post("/organizations/", json={"name": "Test Org", "country_code": "US"})
    org_id = org_response.json()["id"]

    response = client.get(f"/organizations/{org_id}/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
