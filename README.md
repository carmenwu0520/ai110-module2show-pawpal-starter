# 🐾 PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner stay on top of pet care across multiple pets. It tracks feedings, walks, medications and appointments, sorts them into a daily timeline, warns about overlapping tasks, rolls recurring tasks forward when you finish them, and builds a daily plan that fits the time you actually have — explaining why each task made the cut (or didn't).

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

## ✨ Features

- **Multi-pet support** — one owner, any number of pets; the scheduler always works across *all* of them through `Owner.get_all_tasks()`.
- **Sorting by time** — the day's tasks are shown as a chronological timeline, even if they were added out of order.
- **Priority sorting** — tasks can also be ranked high → medium → low.
- **Filtering** — by pet and/or by completion status (pending / done).
- **Daily & weekly recurrence** — completing a recurring task automatically creates the next one (tomorrow or next week).
- **Conflict warnings** — any two tasks whose time windows overlap (same pet or different pets) get a readable warning instead of a crash.
- **Budget-aware daily plan** — picks the highest-priority pending tasks that fit in the owner's available minutes and gives a reason for every scheduled and skipped task.
- **Input validation** — bad priorities, frequencies, durations, or times like `25:00` are rejected immediately; `9:00` is normalized to `09:00` so sorting stays correct.

## 🏗️ How it's built (implementation summary)

All logic lives in `pawpal_system.py`; `app.py` (Streamlit) and `main.py` (CLI demo) only call into it.

| Class | Responsibility |
|-------|----------------|
| `Task` (dataclass) | One activity: description, `HH:MM` start time, duration, priority, frequency, due date, completion status, and which pet it belongs to. Knows its own end time, whether it overlaps another task, and how to create its next occurrence. |
| `Pet` (dataclass) | A pet's details plus its list of tasks. `add_task()` tags each task with the pet's name. |
| `Owner` | Holds the pets and the owner's daily time budget. `get_all_tasks()` returns every pet's tasks in one list. |
| `Scheduler` | The "brain". Reads from `Owner.get_all_tasks()` and does the sorting, filtering, recurrence, conflict detection and plan building. |
| `DailyPlan` / `PlannedTask` | The output of `build_daily_plan()`: scheduled tasks, skipped tasks, the reason for each, and any conflicts. |

UML: [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) (final) · [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd) (Phase 1 draft). `diagrams/uml.mmd` is a copy of the final version.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
python main.py          # CLI demo
streamlit run app.py    # web app
python -m pytest        # tests
```

## 🖥️ Sample Output

Output of `python main.py`:

```
🐾 PawPal+ for Carmen

Today's Schedule (sorted by time)
------------------------------------------------------------------
  [ ] 07:00-07:30  Mochi  Morning walk       high   daily
  [ ] 08:00-08:05  Luna   Thyroid pill       high   daily
  [ ] 08:00-08:10  Mochi  Breakfast          high   daily
  [ ] 14:00-14:45  Luna   Vet checkup        medium once
  [ ] 18:30-19:10  Mochi  Evening walk       medium daily
  [ ] 19:00-19:15  Luna   Brush fur          low    weekly

Filter: Luna's tasks only
------------------------------------------------------------------
  [ ] 08:00-08:05  Luna   Thyroid pill       high   daily
  [ ] 14:00-14:45  Luna   Vet checkup        medium once
  [ ] 19:00-19:15  Luna   Brush fur          low    weekly

Conflict check:
  ⚠ Conflict (Luna & Mochi): 'Thyroid pill' 08:00-08:05 is at the same time as 'Breakfast' 08:00-08:10
  ⚠ Conflict (Mochi & Luna): 'Evening walk' 18:30-19:10 overlaps 'Brush fur' 19:00-19:15

Marked 'Morning walk' complete -> next one auto-created for 2026-10-22

Filter: still pending today
------------------------------------------------------------------
  [ ] 08:00-08:05  Luna   Thyroid pill       high   daily
  [ ] 08:00-08:10  Mochi  Breakfast          high   daily
  [ ] 14:00-14:45  Luna   Vet checkup        medium once
  [ ] 18:30-19:10  Mochi  Evening walk       medium daily
  [ ] 19:00-19:15  Luna   Brush fur          low    weekly

Daily Plan for 2026-10-21 (budget 90 min, used 75 min)
------------------------------------------------------------------
  08:00  Luna   Thyroid pill         5 min  <- high priority, fits in budget (75 min left after)
  08:00  Mochi  Breakfast           10 min  <- high priority, fits in budget (80 min left after)
  14:00  Luna   Vet checkup         45 min  <- medium priority, fits in budget (30 min left after)
  19:00  Luna   Brush fur           15 min  <- low priority, fits in budget (15 min left after)
  SKIPPED Mochi  Evening walk       <- needs 40 min but only 30 min left
  ⚠ Conflict (Luna & Mochi): 'Thyroid pill' 08:00-08:05 is at the same time as 'Breakfast' 08:00-08:10
```

## 🧪 Testing PawPal+

```bash
python -m pytest        # or just: pytest
```

The suite (`tests/test_pawpal.py`, 23 tests) covers:

- **Basics** — `mark_complete()` flips status; adding a task raises the pet's task count; `Owner.get_all_tasks()` combines every pet; duplicate pet names and invalid task fields are rejected.
- **Sorting** — tasks come back in chronological order (including the `9:00` vs `10:00` string-sorting trap); priority sort is high → low.
- **Filtering** — by pet (case-insensitive), by status, and both together.
- **Recurrence** — daily → +1 day, weekly → +7 days, one-time tasks don't repeat, and completing the same task twice doesn't create duplicates.
- **Conflicts** — exact same time is flagged; overlapping windows for the same pet are flagged; back-to-back tasks (07:00–07:30 then 07:30) are *not*; completed tasks are ignored.
- **Daily plan** — respects the time budget, prefers higher priority, explains every decision, and ignores completed tasks and tasks due on other days.
- **Edge cases** — a pet with no tasks gives an empty schedule and no conflicts.

Sample test output:

```
collecting ... collected 23 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  4%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED      [  8%]
tests/test_pawpal.py::test_owner_get_all_tasks_combines_every_pet PASSED [ 13%]
tests/test_pawpal.py::test_duplicate_pet_name_rejected PASSED            [ 17%]
tests/test_pawpal.py::test_invalid_task_fields_rejected[kwargs0] PASSED  [ 21%]
tests/test_pawpal.py::test_invalid_task_fields_rejected[kwargs1] PASSED  [ 26%]
tests/test_pawpal.py::test_invalid_task_fields_rejected[kwargs2] PASSED  [ 30%]
tests/test_pawpal.py::test_invalid_time_rejected PASSED                  [ 34%]
tests/test_pawpal.py::test_sort_by_time_is_chronological PASSED          [ 39%]
tests/test_pawpal.py::test_sort_by_time_handles_unpadded_hours PASSED    [ 43%]
tests/test_pawpal.py::test_sort_by_priority_high_first PASSED            [ 47%]
tests/test_pawpal.py::test_pet_with_no_tasks_gives_empty_schedule PASSED [ 52%]
tests/test_pawpal.py::test_filter_by_pet_and_status PASSED               [ 56%]
tests/test_pawpal.py::test_completing_daily_task_creates_next_day_task PASSED [ 60%]
tests/test_pawpal.py::test_completing_weekly_task_creates_task_one_week_later PASSED [ 65%]
tests/test_pawpal.py::test_one_time_task_does_not_repeat PASSED          [ 69%]
tests/test_pawpal.py::test_completing_twice_does_not_duplicate PASSED    [ 73%]
tests/test_pawpal.py::test_exact_same_time_is_flagged PASSED             [ 78%]
tests/test_pawpal.py::test_overlapping_windows_flagged_for_same_pet PASSED [ 82%]
tests/test_pawpal.py::test_back_to_back_tasks_are_not_a_conflict PASSED  [ 86%]
tests/test_pawpal.py::test_completed_tasks_are_ignored_for_conflicts PASSED [ 91%]
tests/test_pawpal.py::test_daily_plan_respects_time_budget_and_priority PASSED [ 95%]
tests/test_pawpal.py::test_daily_plan_ignores_other_days_and_completed_tasks PASSED [100%]

============================== 23 passed in 0.07s ==============================
```

**Confidence level: ⭐⭐⭐⭐ (4/5)** — every core behavior and the main edge cases are tested and pass. Not 5 stars because the UI is tested by hand rather than automatically, and the scheduler doesn't yet handle tasks that cross midnight or let you edit an existing task.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | `sorted()` with a lambda key. Time sort converts `HH:MM` to minutes after midnight (ties broken by priority, then pet name). Priority sort uses a `high=0, medium=1, low=2` rank, ties broken by time. |
| Filtering | `Scheduler.filter_tasks(tasks, pet_name, completed)` | Each argument is optional — `None` means "don't filter on this", so one method covers by-pet, by-status, or both. |
| Conflict handling | `Scheduler.detect_conflicts()`, `Task.overlaps()` | Checks whether `[start, start + duration)` windows overlap, for the same pet or across pets. Returns a list of warning strings instead of raising, so the app keeps running. Tasks are sorted first so the inner loop can stop early. |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.next_occurrence()` | Completing a `daily`/`weekly` task creates a copy with `due_date + timedelta(days=1)` or `timedelta(weeks=1)` and adds it to the same pet. Completing an already-done task does nothing. |
| Daily plan (time budget) | `Scheduler.build_daily_plan()` | Greedy: walk pending tasks highest-priority first, keep each one that still fits in `Owner.available_minutes`, skip the rest with a reason, then show the result in clock order and re-check conflicts. |

## 📸 Demo Walkthrough

1. **Set up the owner.** Run `streamlit run app.py`. In the sidebar, enter the owner's name and use the slider to set how many minutes they have for pet care today (default 120).
2. **Add pets.** In the sidebar "Pets" form, add e.g. *Mochi* (dog) and *Luna* (cat). Each pet appears in the sidebar with its task count. Adding a second pet with the same name shows an error.
3. **Schedule tasks.** In "Schedule a task", pick a pet, enter a task name, start time, date, duration, priority and whether it repeats (once / daily / weekly). Example: Mochi · Morning walk · 07:00 · 30 min · high · daily; Mochi · Breakfast · 08:00 · 10 min · high · daily; Luna · Thyroid pill · 08:00 · 5 min · high · daily.
4. **View the schedule.** The "Schedule" section shows the selected day's tasks sorted by start time, no matter what order they were added in. Use the **Pet** dropdown and **Status** (All / Pending / Done) to filter.
5. **See conflict warnings.** Mochi's breakfast and Luna's pill both start at 08:00, so a yellow warning appears under the table saying they are at the same time. Tasks whose time windows only partly overlap (e.g. 18:30–19:10 and 19:00–19:15) are flagged too. With no conflicts, a green "No time conflicts" message shows instead.
6. **Complete a task.** Pick a pending task in "Mark a task complete" and click **✅ Mark complete**. It gets a ✅ in the table, and for a daily task a success message confirms the next one was auto-scheduled for tomorrow (switch the date picker to tomorrow to see it).
7. **Generate the plan.** Click **Generate plan**. PawPal+ shows how many minutes are used out of the budget, a table of chosen tasks in time order with a "Why" column, a warning for each task that was skipped because time ran out, and any remaining conflicts.

**Sample CLI output** (`python main.py`) showing the same Scheduler behaviors — out-of-order tasks sorted by time, a Luna-only filter, a same-time conflict and an overlap conflict, a daily walk rolling forward to tomorrow, and a 90-minute plan that skips the 40-minute evening walk:

```
🐾 PawPal+ for Carmen

Today's Schedule (sorted by time)
------------------------------------------------------------------
  [ ] 07:00-07:30  Mochi  Morning walk       high   daily
  [ ] 08:00-08:05  Luna   Thyroid pill       high   daily
  [ ] 08:00-08:10  Mochi  Breakfast          high   daily
  [ ] 14:00-14:45  Luna   Vet checkup        medium once
  [ ] 18:30-19:10  Mochi  Evening walk       medium daily
  [ ] 19:00-19:15  Luna   Brush fur          low    weekly

Filter: Luna's tasks only
------------------------------------------------------------------
  [ ] 08:00-08:05  Luna   Thyroid pill       high   daily
  [ ] 14:00-14:45  Luna   Vet checkup        medium once
  [ ] 19:00-19:15  Luna   Brush fur          low    weekly

Conflict check:
  ⚠ Conflict (Luna & Mochi): 'Thyroid pill' 08:00-08:05 is at the same time as 'Breakfast' 08:00-08:10
  ⚠ Conflict (Mochi & Luna): 'Evening walk' 18:30-19:10 overlaps 'Brush fur' 19:00-19:15

Marked 'Morning walk' complete -> next one auto-created for 2026-10-22

Filter: still pending today
------------------------------------------------------------------
  [ ] 08:00-08:05  Luna   Thyroid pill       high   daily
  [ ] 08:00-08:10  Mochi  Breakfast          high   daily
  [ ] 14:00-14:45  Luna   Vet checkup        medium once
  [ ] 18:30-19:10  Mochi  Evening walk       medium daily
  [ ] 19:00-19:15  Luna   Brush fur          low    weekly

Daily Plan for 2026-10-21 (budget 90 min, used 75 min)
------------------------------------------------------------------
  08:00  Luna   Thyroid pill         5 min  <- high priority, fits in budget (75 min left after)
  08:00  Mochi  Breakfast           10 min  <- high priority, fits in budget (80 min left after)
  14:00  Luna   Vet checkup         45 min  <- medium priority, fits in budget (30 min left after)
  19:00  Luna   Brush fur           15 min  <- low priority, fits in budget (15 min left after)
  SKIPPED Mochi  Evening walk       <- needs 40 min but only 30 min left
  ⚠ Conflict (Luna & Mochi): 'Thyroid pill' 08:00-08:05 is at the same time as 'Breakfast' 08:00-08:10
```

**Screenshot or video** *(optional)*: <!-- Add a screenshot of the running app here -->
