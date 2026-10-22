"""Tests for the PawPal+ logic layer. Run with: python -m pytest"""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

TODAY = date(2026, 10, 19)


@pytest.fixture
def setup():
    """An owner with two pets and a scheduler, reused by most tests."""
    owner = Owner("Carmen", available_minutes=60)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna, Scheduler(owner)


# ---------- basics (Phase 2) ----------

def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert pet.task_count() == 0
    pet.add_task(Task("Breakfast", "08:00"))
    assert pet.task_count() == 1
    assert pet.tasks[0].pet_name == "Mochi"


def test_owner_get_all_tasks_combines_every_pet(setup):
    owner, mochi, luna, _ = setup
    mochi.add_task(Task("Walk", "07:00", due_date=TODAY))
    luna.add_task(Task("Pill", "08:00", due_date=TODAY))
    assert {t.pet_name for t in owner.get_all_tasks()} == {"Mochi", "Luna"}


def test_duplicate_pet_name_rejected(setup):
    owner, *_ = setup
    with pytest.raises(ValueError):
        owner.add_pet(Pet("mochi", "dog"))  # case-insensitive duplicate


@pytest.mark.parametrize("kwargs", [
    {"priority": "urgent"},
    {"frequency": "monthly"},
    {"duration_minutes": 0},
])
def test_invalid_task_fields_rejected(kwargs):
    with pytest.raises(ValueError):
        Task("Bad", "08:00", **kwargs)


def test_invalid_time_rejected():
    with pytest.raises(ValueError):
        Task("Bad", "25:00")


# ---------- sorting ----------

def test_sort_by_time_is_chronological(setup):
    _, mochi, luna, scheduler = setup
    mochi.add_task(Task("Dinner", "18:00", due_date=TODAY))
    luna.add_task(Task("Pill", "08:05", due_date=TODAY))
    mochi.add_task(Task("Walk", "07:00", due_date=TODAY))
    times = [t.time for t in scheduler.get_todays_schedule(TODAY)]
    assert times == ["07:00", "08:05", "18:00"]


def test_sort_by_time_handles_unpadded_hours():
    # "9:00" would sort after "10:00" as a plain string; normalizing fixes that.
    tasks = [Task("Late", "10:00"), Task("Early", "9:00")]
    assert [t.description for t in Scheduler(Owner("x")).sort_by_time(tasks)] == ["Early", "Late"]


def test_sort_by_priority_high_first():
    tasks = [Task("a", "07:00", priority="low"), Task("b", "09:00", priority="high"),
             Task("c", "08:00", priority="medium")]
    assert [t.priority for t in Scheduler(Owner("x")).sort_by_priority(tasks)] == ["high", "medium", "low"]


def test_pet_with_no_tasks_gives_empty_schedule(setup):
    *_, scheduler = setup
    assert scheduler.get_todays_schedule(TODAY) == []
    assert scheduler.detect_conflicts([]) == []


# ---------- filtering ----------

def test_filter_by_pet_and_status(setup):
    _, mochi, luna, scheduler = setup
    walk = Task("Walk", "07:00")
    mochi.add_task(walk)
    mochi.add_task(Task("Dinner", "18:00"))
    luna.add_task(Task("Pill", "08:00"))
    walk.mark_complete()

    assert len(scheduler.filter_tasks(pet_name="mochi")) == 2
    assert [t.description for t in scheduler.filter_tasks(pet_name="Mochi", completed=False)] == ["Dinner"]
    assert len(scheduler.filter_tasks(completed=True)) == 1


# ---------- recurring tasks ----------

def test_completing_daily_task_creates_next_day_task(setup):
    _, mochi, _, scheduler = setup
    walk = Task("Walk", "07:00", frequency="daily", due_date=TODAY)
    mochi.add_task(walk)

    next_walk = scheduler.mark_task_complete(walk)

    assert walk.completed is True
    assert next_walk.due_date == TODAY + timedelta(days=1)
    assert next_walk.completed is False
    assert next_walk in mochi.tasks
    assert mochi.task_count() == 2


def test_completing_weekly_task_creates_task_one_week_later(setup):
    _, _, luna, scheduler = setup
    brush = Task("Brush", "19:00", frequency="weekly", due_date=TODAY)
    luna.add_task(brush)
    assert scheduler.mark_task_complete(brush).due_date == TODAY + timedelta(weeks=1)


def test_one_time_task_does_not_repeat(setup):
    _, _, luna, scheduler = setup
    vet = Task("Vet", "14:00", frequency="once")
    luna.add_task(vet)
    assert scheduler.mark_task_complete(vet) is None
    assert luna.task_count() == 1


def test_completing_twice_does_not_duplicate(setup):
    _, mochi, _, scheduler = setup
    walk = Task("Walk", "07:00", frequency="daily")
    mochi.add_task(walk)
    scheduler.mark_task_complete(walk)
    scheduler.mark_task_complete(walk)
    assert mochi.task_count() == 2


# ---------- conflict detection ----------

def test_exact_same_time_is_flagged(setup):
    _, mochi, luna, scheduler = setup
    mochi.add_task(Task("Breakfast", "08:00", 10, due_date=TODAY))
    luna.add_task(Task("Pill", "08:00", 5, due_date=TODAY))
    warnings = scheduler.detect_conflicts(scheduler.get_tasks_for_day(TODAY))
    assert len(warnings) == 1
    # Ties are broken by pet name, so Luna is listed first — check both, not the order.
    assert "Luna" in warnings[0] and "Mochi" in warnings[0]
    assert "same time" in warnings[0]


def test_overlapping_windows_flagged_for_same_pet(setup):
    _, mochi, _, scheduler = setup
    mochi.add_task(Task("Walk", "07:00", 30, due_date=TODAY))
    mochi.add_task(Task("Breakfast", "07:15", 10, due_date=TODAY))
    warnings = scheduler.detect_conflicts(scheduler.get_tasks_for_day(TODAY))
    assert len(warnings) == 1 and "both for Mochi" in warnings[0]


def test_back_to_back_tasks_are_not_a_conflict(setup):
    _, mochi, _, scheduler = setup
    mochi.add_task(Task("Walk", "07:00", 30, due_date=TODAY))
    mochi.add_task(Task("Breakfast", "07:30", 10, due_date=TODAY))
    assert scheduler.detect_conflicts(scheduler.get_tasks_for_day(TODAY)) == []


def test_completed_tasks_are_ignored_for_conflicts(setup):
    _, mochi, luna, scheduler = setup
    done = Task("Breakfast", "08:00", due_date=TODAY)
    mochi.add_task(done)
    luna.add_task(Task("Pill", "08:00", due_date=TODAY))
    done.mark_complete()
    assert scheduler.detect_conflicts(scheduler.get_tasks_for_day(TODAY)) == []


# ---------- daily plan ----------

def test_daily_plan_respects_time_budget_and_priority(setup):
    owner, mochi, luna, scheduler = setup  # budget = 60 min
    mochi.add_task(Task("Long walk", "18:00", 45, "low", due_date=TODAY))
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", due_date=TODAY))
    luna.add_task(Task("Play", "12:00", 30, "medium", due_date=TODAY))

    plan = scheduler.build_daily_plan(TODAY)

    assert [p.task.description for p in plan.scheduled] == ["Breakfast", "Play"]  # clock order
    assert [p.task.description for p in plan.skipped] == ["Long walk"]
    assert plan.minutes_used <= owner.available_minutes
    assert all(p.reason for p in plan.scheduled + plan.skipped)


def test_daily_plan_ignores_other_days_and_completed_tasks(setup):
    _, mochi, _, scheduler = setup
    done = Task("Breakfast", "08:00", due_date=TODAY)
    mochi.add_task(done)
    mochi.add_task(Task("Tomorrow walk", "07:00", due_date=TODAY + timedelta(days=1)))
    done.mark_complete()
    assert scheduler.build_daily_plan(TODAY).scheduled == []
