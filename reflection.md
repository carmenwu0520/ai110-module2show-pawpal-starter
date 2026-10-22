# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The three core actions I wanted a user to be able to do were:

1. **Add a pet** (name, species, age) under their owner profile.
2. **Schedule a care task** for a specific pet — what it is, when it starts, how long it takes, how important it is, and whether it repeats.
3. **See today's tasks** across all their pets as one ordered schedule, and get a plan that fits the time they have.

My first UML draft (`diagrams/uml_draft.mmd`) had four classes:

- **Task** — one activity: description, `HH:MM` time, duration, priority, frequency, and a `completed` flag, with `mark_complete()`.
- **Pet** — the pet's details plus a list of its tasks, with `add_task()`.
- **Owner** — the person, holding a list of pets, with `add_pet()` and `get_all_tasks()`.
- **Scheduler** — the "brain" that takes an Owner and produces today's schedule (`get_todays_schedule()`, `sort_by_time()`).

Relationships: Owner *has many* Pets, Pet *has many* Tasks, and Scheduler *reads from* Owner. I used dataclasses for Task and Pet since they're mostly data.

**b. Design changes**

Yes, the design grew a lot between the draft and the final version (`diagrams/uml_final.mmd`):

- **Task got a `pet_name` and a `due_date`.** Once the Scheduler pulled every task into one combined list through `Owner.get_all_tasks()`, a task no longer "knew" which pet it belonged to, so the schedule couldn't say whose walk it was. `Pet.add_task()` now tags each task with the pet's name. `due_date` was needed for recurring tasks — "daily" doesn't mean anything without a date to add one day to.
- **Owner got `available_minutes`.** The scenario says the plan should consider the owner's time, so the owner needed a daily time budget.
- **Two small result classes, `DailyPlan` and `PlannedTask`, were added.** `build_daily_plan()` needs to return more than a list: what got scheduled, what got skipped, *why* for each one, and any conflicts. Returning a dataclass is clearer than returning a tuple of lists.
- **Task validates itself in `__post_init__`.** I made `"9:00"` normalize to `"09:00"`, because as plain strings `"9:00"` sorts *after* `"10:00"`, which would silently break sorting.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:

- **Date** — only tasks due on the selected day.
- **Completion status** — finished tasks aren't planned again or counted as conflicts.
- **Priority** (high / medium / low) — decides what gets in first when time is short.
- **Owner's available time** — the total minutes of planned tasks can't go over `available_minutes`.
- **Start time and duration** — used for ordering the day and for detecting overlaps.

I decided **priority + time budget** mattered most, because the scenario is a *busy* owner — the realistic problem isn't "what order do I do things in," it's "I can't do everything today, so what do I drop?" A missed thyroid pill matters a lot more than a skipped brushing session. Start time matters for *displaying* the plan and for catching conflicts, but it doesn't decide what gets dropped.

**b. Tradeoffs**

**The daily plan uses a greedy algorithm**: it goes through pending tasks from highest to lowest priority and keeps each one that still fits in the remaining minutes. That means it doesn't always use the time budget perfectly. In the CLI demo with 90 minutes, the 40-minute medium-priority evening walk gets skipped (only 30 minutes left), but the 15-minute low-priority brushing still fits, so a lower-priority task ends up in the plan while a higher-priority one doesn't. An optimal "knapsack" approach could squeeze more value out of the budget.

I think that's reasonable here because the greedy rule is **easy for an owner to understand and predict** ("important stuff first, until you run out of time"), each decision comes with a one-line reason, and with only a handful of pet tasks a day the difference from an optimal solution is small. An "optimal" plan that the owner can't explain to themselves is less useful than a slightly imperfect one they trust.

A second tradeoff: **conflict detection checks overlapping time windows, not just identical start times**, but it treats *any* two overlapping tasks as a conflict — even for different pets, where one person might actually manage both (e.g., feeding two pets at once). I chose to warn rather than block, so the owner gets the heads-up and decides.

---

## 3. AI Collaboration

<!-- Carmen: this section is graded on "specific, honest details". It describes what actually
happened in this project. Read through the code yourself, then rewrite this section in your
own words and add your own judgment calls before submitting. Delete this comment when done. -->

**a. How you used AI**

I used Claude in agent mode for most of the build, going phase by phase: first the Phase 1 UML draft and the class skeleton, then the core classes with a CLI demo, then the Streamlit wiring, then the algorithms, then the tests, and finally the UML/README/reflection. Each phase ended with its own commit, which made it easy to review one phase at a time and see exactly what changed.

The most effective features were:

- **Agent mode for multi-file changes** — e.g., recurring tasks needed changes in `Task` (`next_occurrence()`), in `Scheduler` (`mark_task_complete()`), in `main.py` and in the tests at the same time.
- **Running the code as part of each step** — the agent ran `python main.py`, `python -m pytest`, and a scripted Streamlit test (`streamlit.testing.v1.AppTest`) that clicked through adding pets, adding tasks, marking one complete, and generating a plan, so problems showed up right away instead of at the end.
- **Asking for edge cases** — the test plan included cases I wouldn't have thought of first, like the `"9:00"` vs `"10:00"` string-sorting trap, back-to-back tasks that touch but don't overlap, and completing the same task twice.

Most helpful prompts were specific and tied to a file, e.g. "how should the Scheduler retrieve all tasks from the Owner's pets?" and "what are the most important edge cases for a pet scheduler with sorting and recurring tasks?"

**b. Judgment and verification**

- **A failing test, and deciding where the bug was.** The first version of the conflict test expected the warning to say "Mochi & Luna", but it said "Luna & Mochi" and failed. The question was whether the bug was in `pawpal_system.py` or the test. `sort_by_time()` intentionally breaks ties by pet name, so Luna (alphabetically first) is listed first — the *logic* was right and the *test* was too strict about wording. The fix was to check that both names appear, not their order, rather than changing the scheduler to make the test pass.
- **Keeping the CLI readable.** An earlier `main.py` printed filter results in whatever order the tasks were stored, which looked unsorted and confusing. The filter output is now passed through `sort_by_time()` first.
- **Keeping the design simple.** Conflict detection returns a list of warning strings rather than raising exceptions or auto-moving tasks, so the program never crashes and the owner stays in control.

Verification was always: run `python main.py` and read the output, run `python -m pytest`, and click through the app.

**Separate phases / sessions.** Treating each phase as its own focused step (with its own commit) kept the algorithm work separate from the core classes and the testing work separate from both, which made it much easier to tell what each change was responsible for.

**Being the "lead architect."** The AI can produce a lot of working code quickly, so the human's job shifts to deciding *what* the system should do and checking that it does it — choosing which constraints matter (priority and time budget), choosing tradeoffs (greedy plan, warn-don't-block conflicts), and treating test failures as questions ("is the test wrong or the code?") instead of just making the red go away.

---

## 4. Testing and Verification

**a. What you tested**

23 tests in `tests/test_pawpal.py`, grouped by feature:

- **Basics:** `mark_complete()` changes status; adding a task increases the pet's task count and tags the pet name; `Owner.get_all_tasks()` returns tasks from every pet; duplicate pet names and invalid priority/frequency/duration/time are rejected.
- **Sorting:** tasks come back in chronological order; `"9:00"` sorts before `"10:00"`; priority sort is high → medium → low.
- **Filtering:** by pet (case-insensitive), by status, and by both.
- **Recurrence:** daily → next day, weekly → +7 days, one-time tasks don't repeat, completing twice doesn't create duplicates.
- **Conflicts:** same start time flagged; overlapping windows for the same pet flagged; back-to-back tasks not flagged; completed tasks ignored.
- **Daily plan:** stays within the time budget, picks higher priority first, gives a reason for every decision, ignores completed tasks and other days.
- **Edge case:** a pet with no tasks → empty schedule, no conflicts.

These matter because sorting, recurrence, conflicts and the plan are exactly the "smart" parts of the app. If one of them is quietly wrong (like a medication task not repeating), the owner would trust a schedule that's missing something important.

**b. Confidence**

**4 / 5.** All 23 tests pass, and the CLI demo and a scripted run of the Streamlit app behave as expected. I'm not at 5 because the UI isn't covered by the automated suite, and some real-world cases aren't handled yet.

Edge cases I'd test next:

- Tasks that cross midnight (e.g., 23:30 for 60 minutes).
- A weekly task completed late — right now the next one is based on the original due date, not the day it was actually done.
- Two pets with similar names, or renaming a pet after tasks were added.
- The time budget set to zero, or a single task longer than the whole budget.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the **daily plan with explanations**. It actually answers the scenario's question — "what should I do today, and why?" — instead of just listing tasks. Every scheduled task says why it was chosen, and every skipped task says exactly how many minutes it needed versus what was left.

**b. What you would improve**

- Let the user **edit and delete tasks** in the UI (right now you can only add and complete).
- **Save data** to a JSON file so pets and tasks survive closing the app.
- Make the plan smarter: try to **fit skipped tasks into open gaps** or suggest a new time for one side of a conflict, instead of only warning.
- Base recurrence on the day a task was actually completed, and support "every N days" for things like flea medication.

**c. Key takeaway**

Designing the classes *before* coding mattered more than I expected — almost every later change (tagging tasks with `pet_name`, adding `due_date`) came from a relationship I hadn't thought through in the UML. And with AI writing a lot of the code, the most important skill is verification: deciding what "correct" means, writing tests that check it, and reading failures carefully instead of just making them pass.
