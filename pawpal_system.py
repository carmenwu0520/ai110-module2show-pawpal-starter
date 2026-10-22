"""PawPal+ logic layer: Owner, Pet, Task and Scheduler classes."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
RECURRENCE_STEP = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
VALID_FREQUENCIES = ("once", "daily", "weekly")


def to_minutes(hhmm: str) -> int:
    """Convert an 'HH:MM' string into minutes after midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def to_hhmm(total_minutes: int) -> str:
    """Convert minutes after midnight back into an 'HH:MM' string."""
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


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

    @property
    def start_minutes(self) -> int:
        """Start time as minutes after midnight."""
        return to_minutes(self.time)

    @property
    def end_minutes(self) -> int:
        """End time as minutes after midnight (start + duration)."""
        return self.start_minutes + self.duration_minutes

    @property
    def end_time(self) -> str:
        """End time as an 'HH:MM' string."""
        return to_hhmm(self.end_minutes)

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """Return a fresh copy of this task for its next due date, or None if it doesn't repeat."""
        step = RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None
        return replace(self, due_date=self.due_date + step, completed=False)

    def overlaps(self, other: Task) -> bool:
        """True if this task's time window overlaps another task's window."""
        return self.start_minutes < other.end_minutes and other.start_minutes < self.end_minutes


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


@dataclass
class PlannedTask:
    """A task that made it into the daily plan, plus the reason it was chosen."""

    task: Task
    reason: str


@dataclass
class DailyPlan:
    """The result of Scheduler.build_daily_plan: what's in, what's out, and why."""

    day: date
    available_minutes: int
    scheduled: list[PlannedTask] = field(default_factory=list)
    skipped: list[PlannedTask] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    @property
    def minutes_used(self) -> int:
        """Total minutes of all scheduled tasks."""
        return sum(p.task.duration_minutes for p in self.scheduled)


class Scheduler:
    """The 'brain': pulls tasks from all of an owner's pets and organizes them."""

    def __init__(self, owner: Owner):
        """Create a scheduler that reads from the given owner."""
        self.owner = owner

    # ---------- retrieving ----------

    def get_tasks_for_day(self, day: date | None = None) -> list[Task]:
        """Return all tasks (across every pet) that are due on the given day."""
        day = day or date.today()
        return [t for t in self.owner.get_all_tasks() if t.due_date == day]

    def get_todays_schedule(self, day: date | None = None) -> list[Task]:
        """Return the day's tasks in chronological order."""
        return self.sort_by_time(self.get_tasks_for_day(day))

    # ---------- sorting ----------

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by start time (ties broken by priority, then pet name)."""
        return sorted(tasks, key=lambda t: (t.start_minutes, PRIORITY_RANK[t.priority], t.pet_name))

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered high -> low priority (ties broken by start time)."""
        return sorted(tasks, key=lambda t: (PRIORITY_RANK[t.priority], t.start_minutes))

    # ---------- filtering ----------

    def filter_tasks(
        self,
        tasks: list[Task] | None = None,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Filter tasks by pet name and/or completion status; None means 'don't filter on this'."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        result = tasks
        if pet_name is not None:
            result = [t for t in result if t.pet_name.lower() == pet_name.lower()]
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        return result

    # ---------- recurring tasks ----------

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task; for daily/weekly tasks, add and return the next occurrence."""
        if task.completed:
            return None  # completing twice shouldn't create duplicate future tasks
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet = self.owner.get_pet(task.pet_name)
            if pet is not None:
                pet.add_task(next_task)
        return next_task

    # ---------- conflicts ----------

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return a warning message for every pair of tasks whose time windows overlap."""
        if tasks is None:
            tasks = self.get_tasks_for_day()
        ordered = self.sort_by_time([t for t in tasks if not t.completed])
        warnings: list[str] = []
        for i, a in enumerate(ordered):
            for b in ordered[i + 1:]:
                if b.start_minutes >= a.end_minutes:
                    break  # sorted by start, so nothing later can overlap `a`
                if a.due_date == b.due_date and a.overlaps(b):
                    who = f"both for {a.pet_name}" if a.pet_name == b.pet_name else f"{a.pet_name} & {b.pet_name}"
                    relation = "is at the same time as" if a.time == b.time else "overlaps"
                    warnings.append(
                        f"Conflict ({who}): '{a.description}' {a.time}-{a.end_time} "
                        f"{relation} '{b.description}' {b.time}-{b.end_time}"
                    )
        return warnings

    # ---------- daily plan ----------

    def build_daily_plan(self, day: date | None = None) -> DailyPlan:
        """Pick which of today's pending tasks fit in the owner's time budget, highest priority first."""
        day = day or date.today()
        pending = self.filter_tasks(self.get_tasks_for_day(day), completed=False)
        plan = DailyPlan(day=day, available_minutes=self.owner.available_minutes)

        remaining = self.owner.available_minutes
        for task in self.sort_by_priority(pending):
            if task.duration_minutes <= remaining:
                remaining -= task.duration_minutes
                plan.scheduled.append(
                    PlannedTask(task, f"{task.priority} priority, fits in budget ({remaining} min left after)")
                )
            else:
                plan.skipped.append(
                    PlannedTask(task, f"needs {task.duration_minutes} min but only {remaining} min left")
                )

        plan.scheduled.sort(key=lambda p: (p.task.start_minutes, PRIORITY_RANK[p.task.priority], p.task.pet_name))  # clock order
        plan.conflicts = self.detect_conflicts([p.task for p in plan.scheduled])
        return plan
