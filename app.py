import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# Streamlit reruns this script top-to-bottom on every click, so the Owner lives in
# session_state ("the vault") and is only created the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
owner: Owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

st.subheader("Add a pet")
with st.form("add_pet", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet") and pet_name:
        try:
            owner.add_pet(Pet(pet_name, species))
            st.success(f"Added {pet_name}!")
        except ValueError as e:
            st.error(str(e))

if owner.pets:
    st.subheader("Schedule a task")
    with st.form("add_task", clear_on_submit=True):
        pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])
        title = st.text_input("Task", value="Morning walk")
        time = st.time_input("Time")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        if st.form_submit_button("Add task"):
            owner.get_pet(pet_choice).add_task(
                Task(title, time.strftime("%H:%M"), int(duration), priority)
            )

    st.subheader("Today's schedule")
    tasks = Scheduler(owner).get_todays_schedule()
    if tasks:
        st.table(
            [{"Time": t.time, "Pet": t.pet_name, "Task": t.description,
              "Minutes": t.duration_minutes, "Priority": t.priority} for t in tasks]
        )
    else:
        st.info("No tasks yet.")
else:
    st.info("Add a pet to get started.")
