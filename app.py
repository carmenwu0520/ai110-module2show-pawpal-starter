from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan your pets' day: add tasks, catch scheduling conflicts, and get a plan that fits your time.")

# Streamlit reruns this script top-to-bottom on every click, so the Owner lives in
# session_state ("the vault") and is only created the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=120)
owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)


def task_rows(tasks: list[Task]) -> list[dict]:
    """Turn Task objects into rows Streamlit can show as a table."""
    return [
        {
            "Done": "✅" if t.completed else "",
            "Time": f"{t.time}–{t.end_time}",
            "Pet": t.pet_name,
            "Task": t.description,
            "Min": t.duration_minutes,
            "Priority": t.priority,
            "Repeats": t.frequency,
        }
        for t in tasks
    ]


# ---------------- Sidebar: owner + pets ----------------
with st.sidebar:
    st.header("👤 Owner")
    owner.name = st.text_input("Name", value=owner.name)
    owner.available_minutes = st.slider(
        "Time available for pet care today (min)", 15, 480, owner.available_minutes, step=15
    )

    st.header("🐶 Pets")
    with st.form("add_pet", clear_on_submit=True):
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "other"])
        age = st.number_input("Age", min_value=0, max_value=40, value=1)
        if st.form_submit_button("Add pet"):
            if not pet_name.strip():
                st.error("Give your pet a name first.")
            else:
                try:
                    owner.add_pet(Pet(pet_name.strip(), species, int(age)))
                    st.success(f"Added {pet_name}!")
                except ValueError as e:
                    st.error(str(e))
    for pet in owner.pets:
        st.write(f"• **{pet.name}** ({pet.species}, {pet.age}y) — {pet.task_count()} tasks")

if not owner.pets:
    st.info("👈 Add a pet in the sidebar to get started.")
    st.stop()

# ---------------- Add a task ----------------
st.subheader("➕ Schedule a task")
with st.form("add_task", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])
        title = st.text_input("Task", value="Morning walk")
        task_time = st.time_input("Start time", value=time(8, 0), step=300)
        due = st.date_input("Date", value=date.today())
    with c2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["high", "medium", "low"])
        frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
    if st.form_submit_button("Add task"):
        new_task = Task(title, task_time.strftime("%H:%M"), int(duration), priority, frequency, due)
        owner.get_pet(pet_choice).add_task(new_task)
        st.success(f"Added '{title}' for {pet_choice} at {new_task.time}.")

st.divider()

# ---------------- Schedule view: sort + filter + conflicts ----------------
st.subheader("📅 Schedule")
day = st.date_input("Show tasks for", value=date.today(), key="view_day")
f1, f2 = st.columns(2)
with f1:
    pet_filter = st.selectbox("Pet", ["All pets"] + [p.name for p in owner.pets])
with f2:
    status_filter = st.radio("Status", ["All", "Pending", "Done"], horizontal=True)

day_tasks = scheduler.get_tasks_for_day(day)
shown = scheduler.filter_tasks(
    day_tasks,
    pet_name=None if pet_filter == "All pets" else pet_filter,
    completed={"All": None, "Pending": False, "Done": True}[status_filter],
)
shown = scheduler.sort_by_time(shown)

if shown:
    st.table(task_rows(shown))
else:
    st.info("No tasks match for this day.")

conflicts = scheduler.detect_conflicts(day_tasks)
if conflicts:
    for warning in conflicts:
        st.warning(f"⚠️ {warning} — consider moving one of these so you aren't in two places at once.")
elif day_tasks:
    st.success("No time conflicts on this day. 🎉")

# Mark a task complete (recurring tasks roll forward automatically)
pending = scheduler.sort_by_time(scheduler.filter_tasks(day_tasks, completed=False))
if pending:
    labels = [f"{t.time} · {t.pet_name} · {t.description}" for t in pending]
    pick = st.selectbox("Mark a task complete", range(len(pending)), format_func=lambda i: labels[i])
    if st.button("✅ Mark complete"):
        next_task = scheduler.mark_task_complete(pending[pick])
        if next_task:
            st.session_state.flash = f"Done! Next '{next_task.description}' auto-scheduled for {next_task.due_date}."
        else:
            st.session_state.flash = "Done!"
        st.rerun()
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

st.divider()

# ---------------- Daily plan ----------------
st.subheader("🧠 Build today's plan")
st.caption(
    f"Picks pending tasks for {day} highest-priority first until your "
    f"{owner.available_minutes}-minute budget runs out, then explains each decision."
)
if st.button("Generate plan", type="primary"):
    plan = scheduler.build_daily_plan(day)
    if not plan.scheduled and not plan.skipped:
        st.info("Nothing pending for this day.")
    else:
        st.success(
            f"Planned {len(plan.scheduled)} task(s), {plan.minutes_used} of "
            f"{plan.available_minutes} min used."
        )
        st.table(
            [
                {"Time": f"{p.task.time}–{p.task.end_time}", "Pet": p.task.pet_name,
                 "Task": p.task.description, "Why": p.reason}
                for p in plan.scheduled
            ]
        )
        for p in plan.skipped:
            st.warning(f"Skipped **{p.task.description}** ({p.task.pet_name}): {p.reason}.")
        for warning in plan.conflicts:
            st.warning(f"⚠️ {warning}")
