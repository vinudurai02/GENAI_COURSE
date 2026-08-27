import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="BMI Calculator",
    page_icon="⚖️",
    layout="centered"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.block-container {
    max-width: 750px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Header */
.hero {
    text-align: center;
    margin-bottom: 25px;
}

.hero-title {
    font-size: 42px;
    font-weight: 700;
    margin-bottom: 5px;
}

.hero-subtitle {
    font-size: 17px;
    color: #777;
}


/* Result Card */
.result-card {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 20px;
    padding: 30px;
    margin-top: 25px;
    margin-bottom: 25px;
    text-align: center;
}

.result-emoji {
    font-size: 38px;
}

.result-small {
    font-size: 15px;
    color: #777;
    margin-top: 5px;
}

.result-number {
    font-size: 60px;
    font-weight: 700;
    line-height: 1.1;
    margin-top: 8px;
    margin-bottom: 8px;
}

.result-label {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 10px;
}

.result-message {
    font-size: 15px;
    color: #666;
}


/* Details box */
.info-box {
    background-color: #f5f6f8;
    border-radius: 15px;
    padding: 20px;
    margin-top: 20px;
}


/* Button */
div.stButton > button {
    width: 100%;
    height: 3.2rem;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# TITLE
# ============================================================

st.markdown("""
<div class="hero">
<div class="hero-title">⚖️ BMI Calculator</div>
<div class="hero-subtitle">
Calculate your Body Mass Index using your height and weight
</div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# USER INPUT
# ============================================================

st.subheader("Enter your details")

col1, col2 = st.columns(2)


with col1:

    height_cm = st.number_input(
        "Height (cm)",
        min_value=50.0,
        max_value=250.0,
        value=170.0,
        step=1.0
    )


with col2:

    weight_kg = st.number_input(
        "Weight (kg)",
        min_value=10.0,
        max_value=300.0,
        value=70.0,
        step=1.0
    )


# ============================================================
# CALCULATE BUTTON
# ============================================================

calculate = st.button(
    "Calculate BMI",
    use_container_width=True
)


# ============================================================
# BMI CALCULATION
# ============================================================

if calculate:

    # Convert centimetres to metres
    height_m = height_cm / 100


    # BMI Formula
    bmi = weight_kg / (height_m ** 2)


    # ========================================================
    # DETERMINE BMI CATEGORY
    # ========================================================

    if bmi < 18.5:

        category = "Underweight"

        emoji = "🟡"

        message = (
            "Your BMI is below the generally "
            "recommended range."
        )


    elif bmi < 25:

        category = "Normal Weight"

        emoji = "🟢"

        message = (
            "Your BMI falls within the generally "
            "healthy range."
        )


    elif bmi < 30:

        category = "Overweight"

        emoji = "🟠"

        message = (
            "Your BMI is above the generally "
            "recommended range."
        )


    else:

        category = "Obesity"

        emoji = "🔴"

        message = (
            "Your BMI is considerably above the "
            "generally recommended range."
        )


    # ========================================================
    # RESULT CARD
    # ========================================================

    st.markdown(
        f"""
<div class="result-card">
<div class="result-emoji">{emoji}</div>
<div class="result-small">YOUR BMI</div>
<div class="result-number">{bmi:.1f}</div>
<div class="result-label">{category}</div>
<div class="result-message">{message}</div>
</div>
""",
        unsafe_allow_html=True
    )


    # ========================================================
    # BMI SCALE
    # ========================================================

    st.subheader("BMI Scale")


    # Keep progress bar between 0 and 1
    bmi_for_bar = min(bmi, 40)

    progress_value = bmi_for_bar / 40


    st.progress(progress_value)


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.caption("Underweight")

        st.write("< 18.5")


    with col2:

        st.caption("Normal")

        st.write("18.5 – 24.9")


    with col3:

        st.caption("Overweight")

        st.write("25 – 29.9")


    with col4:

        st.caption("Obesity")

        st.write("30+")


    # ========================================================
    # USER DETAILS
    # ========================================================

    st.markdown(
        f"""
<div class="info-box">
<b>Your Details</b><br><br>
Height: <b>{height_cm:.0f} cm</b><br>
Weight: <b>{weight_kg:.1f} kg</b><br>
BMI: <b>{bmi:.1f}</b>
</div>
""",
        unsafe_allow_html=True
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "BMI is a general screening measure and does not "
    "directly measure body fat or overall health."
)