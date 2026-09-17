from src.services.goal_contribution_service import (
    create_contribution,
    delete_contribution,
    get_contribution_for_user,
    get_contributions_for_goal,
)
from src.services.goal_service import (
    create_goal,
    delete_goal,
    get_goal_for_user,
    get_shared_goals,
    update_goal,
)


def make_goal(db, user, money, scope="personal", name="Emergency Fund"):
    return create_goal(
        db,
        user.user_id,
        name,
        money(2500),
        "fas fa-piggy-bank",
        "#abcdef",
        scope,
    )


def test_personal_goal_is_only_visible_to_owner(db, user_factory, money):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    goal = make_goal(db, alice, money)

    assert get_goal_for_user(db, alice.user_id, goal.savings_goal_id) is not None
    assert get_goal_for_user(db, bob.user_id, goal.savings_goal_id) is None


def test_shared_goal_is_visible_to_other_user(db, user_factory, money):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    goal = make_goal(db, alice, money, scope="shared")

    assert get_goal_for_user(db, bob.user_id, goal.savings_goal_id) is not None
    assert goal in get_shared_goals(db)


def test_update_goal(db, user_factory, money):
    user = user_factory()
    goal = make_goal(db, user, money)

    updated = update_goal(
        db, goal, "Vacation", money(5000), "fas fa-plane", "#123456", "shared"
    )

    assert updated.name == "Vacation"
    assert updated.target_amount == money(5000)
    assert updated.scope == "shared"


def test_user_can_contribute_to_shared_goal(
    db, user_factory, sample_datetime, money
):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    goal = make_goal(db, alice, money, scope="shared")

    contribution = create_contribution(
        db, bob.user_id, goal.savings_goal_id, money(400), sample_datetime
    )

    assert contribution is not None
    assert contribution.user_id == bob.user_id
    assert contribution.amount == money(400)


def test_user_cannot_contribute_to_other_users_personal_goal(
    db, user_factory, sample_datetime, money
):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    goal = make_goal(db, alice, money, scope="personal")

    contribution = create_contribution(
        db, bob.user_id, goal.savings_goal_id, money(400), sample_datetime
    )

    assert contribution is None


def test_contribution_can_only_be_fetched_by_creator(
    db, user_factory, sample_datetime, money
):
    alice = user_factory("Alice", "alice-key")
    bob = user_factory("Bob", "bob-key")
    goal = make_goal(db, alice, money, scope="shared")
    contribution = create_contribution(
        db, bob.user_id, goal.savings_goal_id, money(400), sample_datetime
    )

    assert get_contribution_for_user(
        db, bob.user_id, goal.savings_goal_id, contribution.contribution_id
    ) is not None
    assert get_contribution_for_user(
        db, alice.user_id, goal.savings_goal_id, contribution.contribution_id
    ) is None


def test_delete_contribution(db, user_factory, sample_datetime, money):
    user = user_factory()
    goal = make_goal(db, user, money)
    contribution = create_contribution(
        db, user.user_id, goal.savings_goal_id, money(100), sample_datetime
    )

    delete_contribution(db, contribution)

    assert get_contributions_for_goal(db, user.user_id, goal.savings_goal_id) == []


def test_deleting_goal_deletes_contributions(
    db, user_factory, sample_datetime, money
):
    user = user_factory()
    goal = make_goal(db, user, money)
    goal_id = goal.savings_goal_id
    create_contribution(db, user.user_id, goal_id, money(100), sample_datetime)

    delete_goal(db, goal)

    assert get_goal_for_user(db, user.user_id, goal_id) is None
    from src.models import GoalContributionModel
    assert db.query(GoalContributionModel).filter_by(goal_id=goal_id).count() == 0
