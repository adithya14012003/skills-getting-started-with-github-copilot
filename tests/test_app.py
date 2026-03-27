import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_data():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"], dict)


def test_signup_for_activity_success():
    email = "newstudent@mergington.edu"
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_for_activity_duplicate():
    existing_email = "michael@mergington.edu"
    response = client.post("/activities/Chess Club/signup", params={"email": existing_email})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_for_nonexistent_activity():
    response = client.post("/activities/Nonexistent/signup", params={"email": "a@b.com"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_accelerate_signup_success():
    email = "faststudent@mergington.edu"
    response = client.post("/activities/Tennis Club/accelerate-signup", params={"email": email})
    assert response.status_code == 200
    assert response.json() == {"message": f"Fast signup successful for {email} in Tennis Club"}
    assert email in activities["Tennis Club"]["participants"]


def test_accelerate_signup_full():
    activity = activities["Debate Team"]
    activity["participants"] = [f"s{i}@mergington.edu" for i in range(activity["max_participants"])]

    response = client.post("/activities/Debate Team/accelerate-signup", params={"email": "new@mergington.edu"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_remove_participant_success():
    email = "lucas@mergington.edu"
    response = client.delete("/activities/Tennis Club/participants", params={"email": email})
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Tennis Club"}
    assert email not in activities["Tennis Club"]["participants"]


def test_remove_participant_not_found():
    response = client.delete("/activities/Tennis Club/participants", params={"email": "missing@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_remove_participant_nonexistent_activity():
    response = client.delete("/activities/Nonexistent/participants", params={"email": "a@b.com"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
