from datetime import datetime
from decimal import Decimal

import pytest

from src.models import GoalContributionModel, SavingsGoalModel


def goal_payload(**overrides):
    payload = {
        "name": "Emergency Fund",
        "target_amount": "5000.00",
        "icon": "shield",
        "color": "#123456",
        "scope": "personal",
    }
    payload.update(overrides)
    return payload


def contribution_payload(**overrides):
    payload = {
        "amount": "125.50",
        "occurred_at": "2026-09-17T19:00:00",
    }
    payload.update(overrides)
    return payload


def add_goal(db, user, name="Goal", scope="personal"):
    goal = SavingsGoalModel(
        user_id=user.user_id,
        name=name,
        target_amount=Decimal("1000.00"),
        icon=None,
        color=None,
        scope=scope,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def add_contribution(db, user, goal, amount="50.00"):
    contribution = GoalContributionModel(
        user_id=user.user_id,
        goal_id=goal.savings_goal_id,
        amount=Decimal(amount),
        occurred_at=datetime(2026, 9, 17, 18, 0),
    )
    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    return contribution


def test_create_goal(authenticated_client, user, db):
    response = authenticated_client.post(
        "/api/goals",
        json=goal_payload(name="  New Laptop  ", icon="  ", color=" #fff "),
    )

    assert response.status_code == 201
    payload = response.get_json()["goal"]
    assert payload["name"] == "New Laptop"
    assert payload["target_amount"] == 5000.0
    assert payload["icon"] is None
    assert payload["color"] == "#fff"

    db.expire_all()
    saved = db.get(SavingsGoalModel, payload["goal_id"])
    assert saved.user_id == user.user_id


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (None, "Missing request body"),
        ({"name": "", "scope": "personal", "target_amount": 1}, "Goal name is required"),
        ({"name": "x", "scope": "private", "target_amount": 1}, "Scope must be 'personal' or 'shared'"),
        ({"name": "x", "scope": "personal", "target_amount": "wat"}, "Invalid target amount"),
        ({"name": "x", "scope": "personal", "target_amount": 0}, "Target amount must be greater than 0"),
    ],
)
def test_create_goal_validates_input(authenticated_client, payload, message):
    response = authenticated_client.post("/api/goals", json=payload)

    assert response.status_code == 400
    assert response.get_json()["message"] == message


def test_goal_list_includes_own_goals_and_shared_goals_only(
    authenticated_client,
    user,
    second_user,
    db,
):
    own = add_goal(db, user, name="Mine")
    shared = add_goal(db, second_user, name="Family", scope="shared")
    add_goal(db, second_user, name="Bob Private")

    response = authenticated_client.get("/api/goals")

    assert response.status_code == 200
    ids = {goal["goal_id"] for goal in response.get_json()["goals"]}
    assert ids == {own.savings_goal_id, shared.savings_goal_id}


def test_shared_goal_is_readable_but_not_editable_by_non_owner(
    authenticated_client,
    second_user,
    db,
):
    goal = add_goal(db, second_user, scope="shared")

    get_response = authenticated_client.get(f"/api/goals/{goal.savings_goal_id}")
    assert get_response.status_code == 200

    update_response = authenticated_client.put(
        f"/api/goals/{goal.savings_goal_id}",
        json=goal_payload(scope="shared"),
    )
    assert update_response.status_code == 403
    assert update_response.get_json()["message"] == "Only the goal owner can update this goal"

    delete_response = authenticated_client.delete(f"/api/goals/{goal.savings_goal_id}")
    assert delete_response.status_code == 403
    assert delete_response.get_json()["message"] == "Only the goal owner can delete this goal"


def test_other_users_personal_goal_is_hidden(authenticated_client, second_user, db):
    goal = add_goal(db, second_user, scope="personal")

    assert authenticated_client.get(f"/api/goals/{goal.savings_goal_id}").status_code == 404


def test_owner_can_update_and_delete_goal(authenticated_client, user, db):
    goal = add_goal(db, user)
    goal_id = goal.savings_goal_id

    update = authenticated_client.put(
        f"/api/goals/{goal_id}",
        json=goal_payload(name="Updated", target_amount="2500", scope="shared"),
    )
    assert update.status_code == 200
    assert update.get_json()["goal"]["name"] == "Updated"
    assert update.get_json()["goal"]["scope"] == "shared"

    delete = authenticated_client.delete(f"/api/goals/{goal_id}")
    assert delete.status_code == 200

    db.expire_all()
    assert db.get(SavingsGoalModel, goal_id) is None


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (None, "Missing request body"),
        ({"amount": "bad"}, "Invalid amount"),
        ({"amount": 0}, "Amount must be greater than 0"),
        ({"amount": 5, "occurred_at": "bad"}, "Invalid occurred_at datetime"),
    ],
)
def test_contribution_validates_input(
    authenticated_client,
    user,
    db,
    payload,
    message,
):
    goal = add_goal(db, user)

    response = authenticated_client.post(
        f"/api/goals/{goal.savings_goal_id}/contributions",
        json=payload,
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == message


def test_user_can_contribute_to_another_users_shared_goal(
    authenticated_client,
    user,
    second_user,
    db,
):
    goal = add_goal(db, second_user, scope="shared")

    response = authenticated_client.post(
        f"/api/goals/{goal.savings_goal_id}/contributions",
        json=contribution_payload(),
    )

    assert response.status_code == 201
    payload = response.get_json()["contribution"]
    assert payload["user_id"] == user.user_id
    assert payload["amount"] == 125.5


def test_user_cannot_contribute_to_another_users_personal_goal(
    authenticated_client,
    second_user,
    db,
):
    goal = add_goal(db, second_user, scope="personal")

    response = authenticated_client.post(
        f"/api/goals/{goal.savings_goal_id}/contributions",
        json=contribution_payload(),
    )

    assert response.status_code == 404
    assert response.get_json()["message"] == "Goal not found"


def test_shared_goal_contributions_are_visible_to_authenticated_users(
    authenticated_client,
    user,
    second_user,
    db,
):
    goal = add_goal(db, second_user, scope="shared")
    contribution = add_contribution(db, second_user, goal)
    own_contribution = add_contribution(db, user, goal, amount="75.00")

    response = authenticated_client.get(
        f"/api/goals/{goal.savings_goal_id}/contributions"
    )

    assert response.status_code == 200
    ids = {item["contribution_id"] for item in response.get_json()["contributions"]}
    assert ids == {contribution.contribution_id, own_contribution.contribution_id}


def test_only_contribution_creator_can_delete_it(
    authenticated_client,
    second_authenticated_client,
    user,
    second_user,
    db,
):
    goal = add_goal(db, second_user, scope="shared")
    contribution = add_contribution(db, user, goal)

    contribution_id = contribution.contribution_id

    url = (
        f"/api/goals/{goal.savings_goal_id}"
        f"/contributions/{contribution_id}"
    )

    other_response = second_authenticated_client.delete(url)
    assert other_response.status_code == 404
    assert other_response.get_json()["message"] == "Contribution not found"

    owner_response = authenticated_client.delete(url)
    assert owner_response.status_code == 200

    db.expire_all()

    assert db.get(GoalContributionModel, contribution_id) is None
