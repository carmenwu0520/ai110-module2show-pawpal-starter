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

**a. How you used AI**

Honestly, I leaned on AI a lot for this one. I was working overtime at my job during election season, so I used Claude in agent mode and had it go through the project phase by phase, the same order as the assignment: UML draft and skeleton, core classes plus the CLI demo, connecting Streamlit, the scheduling algorithms, tests, and then the final UML, README and reflection. Every phase ended with its own commit, so I can look back at the history and see exactly what changed at each step instead of one giant dump of code.

The features that helped the most:

- **Agent mode editing several files at once.** Recurring tasks was a good example. It needed `Task.next_occurrence()`, `Scheduler.mark_task_complete()`, a change in `main.py`, and new tests all at the same time. Doing that by hand would have been easy to mess up.
- **Running things right away.** After each phase it ran `python main.py` and `python -m pytest`, and it even used Streamlit's testing tool (`AppTest`) to "click" through the app: add pets, add tasks, mark one done, generate a plan. So problems showed up immediately and not at the very end.
- **Edge cases I wouldn't have thought of.** The `"9:00"` vs `"10:00"` thing surprised me. As plain strings `"9:00"` sorts *after* `"10:00"`, which would quietly break the schedule. Same with back-to-back tasks (07:00–07:30 and then 07:30) not counting as a conflict.

**b. Judgment and verification**

A few moments where the AI's first version was not accepted as-is:

- **The failing conflict test.** One test expected the warning to say "Mochi & Luna", but the code printed "Luna & Mochi", so it failed. The real question was whether the bug was in the code or in the test. The scheduler breaks ties by pet name on purpose, so Luna comes first. The logic was fine and the test was just too picky about the order. The fix was to check that both names show up, instead of changing the scheduler just to make the test go green. I liked this one because it's an easy trap: when a test fails, the lazy fix is to bend the code to the test.
- **A made-up commit email.** When the agent first committed, it put in a school-style email address for me that it had basically guessed. That isn't my email. It got caught and all the commits were re-done with the correct author info. Small thing, but it showed me I need to check what an agent does *around* the code too, not only the code.
- **Almost-fake test output.** While copying the pytest output into the README, the agent first changed the "platform" line to make it look like it ran on a Mac. It caught that itself and pasted the real output instead. Evidence in a README should be the real thing, even if it looks less pretty.
- **GitHub access.** To push to my fork I had to give the Claude GitHub app permission. I only gave it access to this one repo, not all my repositories.

How I verified: read the `main.py` output to see if the schedule made sense, ran `python -m pytest`, and looked at the app.

**Separate phases / sessions.** I didn't open a brand-new chat for every phase, but splitting the work by phase with a commit after each one did the same job. The algorithm changes stayed separate from the core classes, and the tests had their own commit, so it was easy to tell which change did what.

**Being the "lead architect."** My takeaway is that the AI can write a lot of working code really fast, so the hard part moves to me. I have to decide what the app should actually do, check that it really does it, and catch the things the AI does confidently but wrong (like the email). I'm still learning to do this, honestly. Next time I want to read the code more closely *while* it's being built, not only at the end.

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
