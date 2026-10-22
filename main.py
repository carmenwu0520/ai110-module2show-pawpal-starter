"""CLI demo for PawPal+ — run with: python main.py"""

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(title: str, tasks: list[Task]) -> None:
    """Print a list of tasks as a readable table."""
    print(f"\n{title}")
    print("-" * 62)
    if not tasks:
        print("  (no tasks)")
    for t in tasks:
        status = "✓" if t.completed else " "
        print(
            f"  [{status}] {t.time}  {t.pet_name:<7} {t.description:<22} "
            f"{t.duration_minutes:>3} min  {t.priority}"
        )


def main() -> None:
    owner = Owner("Carmen", available_minutes=90)
    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", "07:30", 30, "high", "daily"))
    mochi.add_task(Task("Breakfast", "08:00", 10, "high", "daily"))
    luna.add_task(Task("Breakfast", "08:15", 5, "high", "daily"))
    luna.add_task(Task("Brush fur", "19:00", 15, "low", "weekly"))

    scheduler = Scheduler(owner)
    print_schedule("Today's Schedule", scheduler.get_todays_schedule())


if __name__ == "__main__":
    main()
