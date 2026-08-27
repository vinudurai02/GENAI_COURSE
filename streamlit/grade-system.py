import streamlit as st


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Student Grade Calculator",
    page_icon="🎓",
    layout="centered"
)


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🎓 Student Grade Calculator")

st.write(
    "Enter your mark below to calculate your grade."
)


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------

mark = st.number_input(
    "Enter your mark",
    min_value=0,
    max_value=100,
    value=75,
    step=1
)


# --------------------------------------------------
# CALCULATE BUTTON
# --------------------------------------------------

if st.button(
    "Calculate Grade",
    use_container_width=True
):


    # --------------------------------------------------
    # GRADE CALCULATION
    # --------------------------------------------------

    if mark >= 90:

        grade = "A"

    elif mark >= 80:

        grade = "B"

    elif mark >= 70:

        grade = "C"

    elif mark >= 60:

        grade = "D"

    else:

        grade = "E"


    # --------------------------------------------------
    # DISPLAY RESULT
    # --------------------------------------------------

    st.subheader("Your Result")

    st.metric(
        label="Grade",
        value=grade
    )

    st.success(
        f"You entered {mark}. Your grade is {grade}."
    )


# --------------------------------------------------
# GRADING SCALE
# --------------------------------------------------

st.divider()

st.subheader("Grading Scale")

st.write("""
- **90 – 100:** Grade A
- **80 – 89:** Grade B
- **70 – 79:** Grade C
- **60 – 69:** Grade D
- **Below 60:** Grade E
""")