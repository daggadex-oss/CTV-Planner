import streamlit as st
import pandas as pd
import numpy as np
import io

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(layout="wide")

# =========================
# CUSTOM STYLING (CURATOR THEME)
# =========================
st.markdown("""
<style>

body {
    font-family: 'Montserrat', sans-serif;
}

/* Background */
.stApp {
    background-color: #1A1A1A;
    color: white;
}

/* Headings */
h1 {
    color: #2F5BFF;
    font-weight: 700;
}

h2, h3 {
    color: #FFFFFF;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #2F5BFF, #6C8CFF);
    padding: 15px;
    border-radius: 12px;
    color: white;
}

/* Buttons */
button {
    background-color: #FFC700 !important;
    color: black !important;
    border-radius: 8px !important;
}

/* Dataframe */
.css-1d391kg {
    background-color: #1A1A1A;
}

/* Section blocks */
.block {
    background-color: #262626;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# LOAD DATA
# =========================
df = pd.read_excel("CTV_Planner_Data_Source_v5.xlsx")

# =========================
# HERO SECTION
# =========================
st.title("Curated CTV Planner")

st.markdown("""
**More control. Less waste. Greater transparency.**  

A unified CTV planning environment designed to optimise reach, efficiency, and supply quality.
""")

# =========================
# INPUT PANEL
# =========================
with st.container():
    st.markdown('<div class="block">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        budget = st.number_input("Budget (ZAR)", value=100000)

    with col2:
        objective = st.selectbox(
            "Campaign Objective",
            ["Awareness", "Consideration", "Conversion"]
        )

    with col3:
        target_gender = st.selectbox(
            "Target Gender",
            ["All", "Male", "Female"]
        )

    ages = st.multiselect(
        "Target Age Groups",
        ["18-24", "25-34", "35-44", "45-54", "55+"],
        default=["25-34"]
    )

    selected_publishers = st.multiselect(
        "Publishers",
        df["Publisher"].tolist(),
        default=df["Publisher"].tolist()
    )

    selected_devices = st.multiselect(
        "Devices",
        ["CTV", "Desktop", "Mobile"],
        default=["CTV", "Desktop", "Mobile"]
    )

    generate = st.button("Generate Plan")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# WEIGHTS
# =========================
base_weights = {
    "Awareness": {
        "SABC+": 0.35,
        "VIU": 0.25,
        "Reach Africa": 0.2,
        "eVOD": 0.1,
        "DStv Stream": 0.1
    },
    "Consideration": {
        "Reach Africa": 0.3,
        "eVOD": 0.25,
        "SABC+": 0.2,
        "DStv Stream": 0.15,
        "VIU": 0.1
    },
    "Conversion": {
        "DStv Stream": 0.4,
        "Reach Africa": 0.25,
        "eVOD": 0.2,
        "SABC+": 0.1,
        "VIU": 0.05
    }
}

# =========================
# OUTPUT
# =========================
if generate:

    filtered_df = df[df["Publisher"].isin(selected_publishers)]

    results = []

    for _, row in filtered_df.iterrows():

        age_match = sum([row[age] for age in ages])
        base = base_weights[objective].get(row["Publisher"], 0)
        weight = base * age_match

        # Device factor
        device_factor = 0
        if "CTV" in selected_devices:
            device_factor += row["CTV %"]
        if "Desktop" in selected_devices:
            device_factor += row["Desktop %"]
        if "Mobile" in selected_devices:
            device_factor += row["Mobile %"]

        weight *= device_factor

        # Gender factor
        if target_gender == "Male":
            weight *= row["Male %"]
        elif target_gender == "Female":
            weight *= row["Female %"]

        results.append({
            "Publisher": row["Publisher"],
            "Weight": weight,
            "CPM": row["CPM"],
            "MAU": row["MAU"],
            "Device Factor": device_factor
        })

    results_df = pd.DataFrame(results)

    if results_df["Weight"].sum() == 0:
        st.error("No valid weights.")
        st.stop()

    results_df["Weight"] /= results_df["Weight"].sum()

    results_df["Budget"] = results_df["Weight"] * budget
    results_df["Impressions"] = (results_df["Budget"] / results_df["CPM"]) * 1000

    results_df["Reach"] = np.minimum(
        results_df["MAU"] * results_df["Device Factor"],
        results_df["Impressions"] / 2.5
    )

    results_df["Frequency"] = results_df["Impressions"] / results_df["Reach"]

    output = results_df[[
        "Publisher", "Budget", "CPM", "Impressions", "Reach", "Frequency"
    ]]

    # =========================
    # KPI SECTION
    # =========================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Reach", f"{int(output['Reach'].sum()):,}")

    with col2:
        st.metric("Total Impressions", f"{int(output['Impressions'].sum()):,}")

    with col3:
        st.metric("Avg Frequency", f"{output['Frequency'].mean():.2f}")

    # =========================
    # TABLE + CHART
    # =========================
    col1, col2 = st.columns([2,1])

    with col1:
        st.dataframe(
            output.style.format({
                "Budget": "R{:,.0f}",
                "Impressions": "{:,.0f}",
                "Reach": "{:,.0f}",
                "Frequency": "{:.2f}"
            })
        )

    with col2:
        st.bar_chart(output.set_index("Publisher")["Reach"])

    # =========================
    # EXPORT
    # =========================
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        output.to_excel(writer, index=False, sheet_name='Plan')

    st.download_button(
        "Download Plan",
        buffer.getvalue(),
        "CTV_Plan.xlsx"
    )
