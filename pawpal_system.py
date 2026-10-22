"""PawPal+ logic layer: Owner, Pet, Task and Scheduler classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
VALID_FREQUENCIES = ("once", "daily", "weekly")


@dataclass
class Task:
    """A single pet care activity (feeding, walk, meds, appointment...)."""

    description: str
    time: str  # "HH:MM", 24-hour clock
    duration_minutes: int = 15
    priority: str = "medium"  # "low" / "medium" / "high"
    frequency: str = "once"  # "once" / "daily" / "weekly"
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    pet_name: str = ""  # filled in by Pet.add_task

    def __post_init__(self) -> None:
        """Validate fields so bad input fails early instead of breaking sorting later."""
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}, got {self.priority!r}")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}, got {self.frequency!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        hours, minutes = self.time.split(":")
        if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
            raise ValueError(f"time must be HH:MM, got {self.time!r}")
        self.time = f"{int(hours):02d}:{int(minutes):02d}"  # normalize "8:00" -> "08:00"

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


@dataclass
class Pet:
    """A pet and the list of care tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        self.tasks.remove(task)

    def task_count(self) -> int:
        """Return how many tasks this pet has."""
        return len(self.tasks)


class Owner:
    """A pet owner who manages one or more pets and has limited time per day."""

    def __init__(self, name: str, available_minutes: int = 120):
        """Create an owner with a daily time budget (in minutes) for pet care."""
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet; pet names must be unique so tasks can be traced back to a pet."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"{self.name} already has a pet named {pet.name}")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Look up a pet by name (case-insensitive), or None if not found."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task from every pet in one combined list."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


class Scheduler:
    """The 'brain': pulls tasks from all of an owner's pets and organizes them."""

    def __init__(self, owner: Owner):
        """Create a scheduler that reads from the given owner."""
        self.owner = owner

    def get_tasks_for_day(self, day: date | None = None) -> list[Task]:
        """Return all tasks (across every pet) that are due on the given day."""
        day = day or date.today()
        return [t for t in self.owner.get_all_tasks() if t.due_date == day]

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by their HH:MM start time."""
        return sorted(tasks, key=lambda t: t.time)

    def get_todays_schedule(self, day: date | None = None) -> list[Task]:
        """Return the day's tasks in chronological order."""
        return self.sort_by_time(self.get_tasks_for_day(day))
