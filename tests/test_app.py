"""Tests for the FastAPI application."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_success(self, client):
        """Test successfully retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data

    def test_get_activities_structure(self, client):
        """Test that activities have correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_participants(self, client):
        """Test that activities contain expected participants."""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignUp:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=newemail@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert "newemail@mergington.edu" in data["message"]

    def test_signup_updates_participants(self, client):
        """Test that signup actually adds participant to activity."""
        email = "test@mergington.edu"
        
        # Sign up
        response = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Programming Class"]["participants"]

    def test_signup_already_signed_up(self, client):
        """Test that signing up twice raises an error."""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == 400
        assert "Already signed up" in response.json()["detail"]

    def test_signup_activity_not_found(self, client):
        """Test that signing up for nonexistent activity returns 404."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_activity_full(self, client):
        """Test that signing up for full activity raises an error."""
        # Basketball Team has max 15 and only 1 participant
        # We need to fill it up to test
        response = client.get("/activities")
        basketball = response.json()["Basketball Team"]
        
        # Fill up the activity
        for i in range(basketball["max_participants"] - len(basketball["participants"])):
            email = f"participant{i}@mergington.edu"
            client.post(f"/activities/Basketball Team/signup?email={email}")
        
        # Try to sign up one more
        response = client.post(
            "/activities/Basketball Team/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"
        
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant."""
        email = "michael@mergington.edu"
        
        # Verify participant is there
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant is removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]

    def test_unregister_not_found_activity(self, client):
        """Test unregistering from nonexistent activity."""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_found_participant(self, client):
        """Test unregistering a participant not in the activity."""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notmember@mergington.edu"
        )
        assert response.status_code == 404
        assert "Student not found" in response.json()["detail"]

    def test_unregister_allows_new_signup(self, client):
        """Test that after unregistering, participant can sign up again."""
        email = "michael@mergington.edu"
        
        # Unregister
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Try to sign up again
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant is back
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering."""
        email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_multiple_signups(self, client):
        """Test multiple participants signing up."""
        activity = "Basketball Team"
        emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        
        initial_count = len(client.get("/activities").json()[activity]["participants"])
        
        # Sign up multiple users
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all signed up
        response = client.get("/activities")
        final_count = len(response.json()[activity]["participants"])
        assert final_count == initial_count + len(emails)
        
        for email in emails:
            assert email in response.json()[activity]["participants"]
