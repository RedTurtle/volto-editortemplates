from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.restapi.testing import RelativeSession

import json
import pytest


@pytest.fixture()
def api_session(functional, portal):
    """Fixture to provide an API session for interacting with the REST API."""
    session = RelativeSession(portal.absolute_url())
    session.headers.update({"Accept": "application/json"})
    session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
    yield session
    session.close()


@pytest.fixture()
def template_data():
    """Fixture to provide template data."""
    return {
        "id": "test-template",
        "name": "Test Template",
        "config": {
            "blocks": {"block1": {"@type": "title"}},
            "blocks_layout": {"items": ["block1"]},
        },
    }


@pytest.fixture()
def regular_user():
    """Fixture to create a regular user with no specific roles."""
    # Crea un utente regolare senza permessi
    user = api.user.create(
        username="regular_user",
        password="password",
        email="regular_user@example.com",
    )
    return user


class TestBlockTemplateServices:
    endpoint: str = "/@block-template"

    @pytest.fixture(autouse=True)
    def _init(self, portal, api_session, template_data, regular_user):
        self.portal = portal
        self.api_session = api_session
        self.template_data = template_data
        self.regular_user = regular_user

    def test_add_block_template(self):
        """Test the creation of a block template."""
        response = self.api_session.post(
            self.endpoint,
            headers={"Content-Type": "application/json"},
            data=json.dumps(self.template_data),
        )

        assert response.status_code == 204

    def test_add_block_template_unauth(self):
        """Test the creation of a block template."""
        self.api_session.auth = (self.regular_user.getId(), "password")
        response = self.api_session.post(
            self.endpoint,
            headers={"Content-Type": "application/json"},
            data=json.dumps(self.template_data),
        )

        assert response.status_code == 401  # Forbidden

        assert "You are not authorized to access this resource." == response.json().get(
            "message", ""
        )

    def test_update_block_template_unauth(self):
        """Test the creation of a block template."""
        self.api_session.auth = (self.regular_user.getId(), "password")
        response = self.api_session.patch(
            self.endpoint,
            headers={"Content-Type": "application/json"},
            data=json.dumps(self.template_data),
        )

        assert response.status_code == 401  # Forbidden

        assert "You are not authorized to access this resource." == response.json().get(
            "message", ""
        )

    def test_get_block_templates(self):
        """Test retrieval of block templates."""
        # Add a template before testing retrieval
        self.test_add_block_template()

        response = self.api_session.get(self.endpoint)

        assert response.status_code == 200

        data = response.json()
        assert len(data.get("items", [])) > 0
        assert data["items"][0]["name"] == "Test Template"

    def test_search_template_by_name(self):
        """Test searching for a template by name."""
        # Add a template before testing retrieval
        self.test_add_block_template()
        response = self.api_session.get(self.endpoint, params={"name": "Test"})
        assert response.status_code == 200

        results = response.json()
        assert "items" in results
        assert len(results["items"]) > 0

        template_names = [item["name"] for item in results["items"]]
        assert "Test Template" in template_names

    def test_update_block_template(self):
        """Test updating a block template."""
        # Add a template before testing the update
        self.test_add_block_template()
        template_uid = self.get_first_template_uid()

        updated_data = {
            "uid": template_uid,
            "name": "Updated Template Name",
            "config": self.template_data["config"],
        }

        response = self.api_session.patch(
            self.endpoint,
            headers={"Content-Type": "application/json"},
            data=json.dumps(updated_data),
        )
        assert response.status_code == 204

        # Verify the name was updated
        response = self.api_session.get(self.endpoint)
        assert response.status_code == 200
        templates = response.json().get("items", [])
        assert "Updated Template Name" in [t["name"] for t in templates]

    def test_delete_block_template(self, portal):
        """Test deletion of a block template."""
        # Add a template before testing deletion
        self.test_add_block_template()
        template_uid = self.get_first_template_uid()

        response = self.api_session.delete(
            self.endpoint,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"uid": template_uid}),
        )
        assert response.status_code == 204

        # Verify the template was removed
        response = self.api_session.get(self.endpoint)
        assert response.status_code == 200
        templates = response.json().get("items", [])
        assert template_uid not in [t["uid"] for t in templates]

    def test_delete_template_unauth(self):
        """Test that a user without permissions cannot delete a template."""
        # Add a template before testing deletion
        self.test_add_block_template()
        template_uid = self.get_first_template_uid()
        # Simula l'autenticazione dell'utente regolare
        self.api_session.auth = (self.regular_user.getId(), "password")

        response = self.api_session.delete(
            self.endpoint,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"uid": template_uid}),
        )

        assert response.status_code == 401  # Forbidden

        assert "You are not authorized to access this resource." == response.json().get(
            "message", ""
        )

    def get_first_template_uid(self):
        """Helper function to get the UID of the first available template."""
        response = self.api_session.get(self.endpoint)
        templates = response.json().get("items", [])
        return templates[0]["uid"] if templates else None
