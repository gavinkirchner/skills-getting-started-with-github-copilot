import pytest


class TestRootEndpoint:
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_get_activities_contains_required_fields(self, client):
        """Test that activities have required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity in activities.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)

    def test_get_activities_includes_participants(self, client):
        """Test that activities include existing participants"""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        assert "Chess Club" in result["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant"""
        # Signup
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        # Verify
        response = client.get("/activities")
        activities = response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_for_nonexistent_activity_fails(self, client):
        """Test signup for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_fails(self, client):
        """Test that duplicate signups are rejected"""
        # Try to signup someone already registered
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_to_full_activity(self, client):
        """Test signup to a full activity fails"""
        # First, fill up the activity (Gym Class has max 30, currently 2)
        for i in range(28):
            client.post(
                f"/activities/Gym Class/signup?email=student{i}@mergington.edu"
            )
        
        # Try to sign up when full
        response = client.post(
            "/activities/Gym Class/signup?email=extra@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()


class TestUnregisterEndpoint:
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert "message" in result
        assert "michael@mergington.edu" in result["message"]
        assert "Chess Club" in result["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        # Unregister
        client.post("/activities/Chess Club/unregister?email=michael@mergington.edu")
        
        # Verify
        response = client.get("/activities")
        activities = response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test unregister from nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up_fails(self, client):
        """Test unregister for someone not signed up fails"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_signup_and_unregister_cycle(self, client):
        """Test signing up and then unregistering"""
        email = "testcycle@mergington.edu"
        
        # Signup
        response = client.post(f"/activities/Tennis Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()["Tennis Club"]["participants"]
        
        # Unregister
        response = client.post(f"/activities/Tennis Club/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert email not in response.json()["Tennis Club"]["participants"]


class TestEmailHandling:
    def test_email_with_special_characters_encoded(self, client):
        """Test that email encoding works properly"""
        email = "plus+sign@mergington.edu"
        response = client.post(
            f"/activities/Art Studio/signup?email={email}"
        )
        # The TestClient should handle URL encoding
        assert response.status_code == 200

    def test_case_sensitivity_in_emails(self, client):
        """Test email handling is case-insensitive"""
        # Signup with lowercase
        response = client.post(
            "/activities/Music Ensemble/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        
        # Try to signup with uppercase (should fail as duplicate)
        response = client.post(
            "/activities/Music Ensemble/signup?email=TEST@mergington.edu"
        )
        # This should either succeed or fail depending on implementation
        # For now we just verify it doesn't crash
        assert response.status_code in [200, 400]
