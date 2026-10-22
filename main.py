"""CLI demo for PawPal+ — run with: python main.py"""

from datetime import date

from pawpal_system import DailyPlan, Owner, Pet, Scheduler, Task


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a list of tasks as a readable table."""
    print(f"\n{title}")
    print("-" * 66)
    if not tasks:
        print("  (no tasks)")
    for t in tasks:
        status = "✓" if t.completed else " "
        print(
            f"  [{status}] {t.time}-{t.end_time}  {t.pet_name:<6} {t.description:<18} "
            f"{t.priority:<6} {t.frequency}"
        )


def print_plan(plan: DailyPlan) -> None:
    """Print the daily plan with the reason behind each decision."""
    print(f"\nDaily Plan for {plan.day} (budget {plan.available_minutes} min, used {plan.minutes_used} min)")
    print("-" * 66)
    for p in plan.scheduled:
        t = p.task
        print(f"  {t.time}  {t.pet_name:<6} {t.description:<18} {t.duration_minutes:>3} min  <- {p.reason}")
    for p in plan.skipped:
        t = p.task
        print(f"  SKIPPED {t.pet_name:<6} {t.description:<18} <- {p.reason}")
    for warning in plan.conflicts:
        print(f"  ⚠ {warning}")


def main() -> None:
    owner = Owner("Carmen", available_minutes=90)
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of order to show sorting works.
    luna.add_task(Task("Brush fur", "19:00", 15, "low", "weekly"))
    mochi.add_task(Task("Evening walk", "18:30", 40, "medium", "daily"))
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    luna.add_task(Task("Thyroid pill", "08:05", 5, "high", "daily"))  # overlaps Mochi's breakfast
    morning_walk = Task("Morning walk", "07:00", 30, "high", "daily")
    mochi.add_task(morning_walk)
    luna.add_task(Task("Vet checkup", "14:00", 45, "medium", "once"))

    scheduler = Scheduler(owner)
    today = date.today()

    print(f"🐾 PawPal+ for {owner.name}")
    print_tasks("Today's Schedule (sorted by time)", scheduler.get_todays_schedule(today))
    print_tasks("Filter: Luna's tasks only", scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Luna")))

    print("\nConflict check:")
    for warning in scheduler.detect_conflicts():
        print(f"  ⚠ {warning}")

    next_walk = scheduler.mark_task_complete(morning_walk)
    print(f"\nMarked '{morning_walk.description}' complete -> next one auto-created for {next_walk.due_date}")
    pending = scheduler.filter_tasks(scheduler.get_tasks_for_day(today), completed=False)
    print_tasks("Filter: still pending today", scheduler.sort_by_time(pending))

    print_plan(scheduler.build_daily_plan(today))


if __name__ == "__main__":
    main()
