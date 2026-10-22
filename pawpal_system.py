"""PawPal+ logic layer: Owner, Pet, Task and Scheduler classes."""

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care activity."""

    description: str
    time: str  # "HH:MM"
    duration_minutes: int = 15
    priority: str = "medium"  # low / medium / high
    frequency: str = "once"  # once / daily / weekly
    completed: bool = False

    def mark_complete(self) -> None:
        pass


@dataclass
class Pet:
    """A pet and its care tasks."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass


class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(self, name: str):
        self.name = name
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> list[Task]:
        pass


class Scheduler:
    """Organizes tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def get_todays_schedule(self) -> list[Task]:
        pass

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        pass
