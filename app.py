import streamlit as st
import pandas as pd
import numpy as np
import io

# Load data
df = pd.read_excel("CTV_Planner_Data_Source_v5.xlsx")

st.title("CTV Planner")

# =========================
# INPUTS
# =========================

budget = st.number_input("Enter Budget (ZAR)", value=100000)

ages = st.multiselect(
    "Target Age Groups",
    ["18-24", "25-34", "35-44", "45-54", "55+"],
    default=["25-34"]
)

objective = st.selectbox(
    "Campaign Objective",
    ["Awareness", "Consideration", "Conversion"]
)

selected_publishers = st.multiselect(
    "Select Publishers",
    df["Publisher"].tolist(),
    default=df["Publisher"].tolist()
)

selected_devices = st.multiselect(
    "Select Devices",
    ["CTV", "Desktop", "Mobile"],
    default=["CTV", "Desktop", "Mobile"]
)

# ✅ NEW: Gender targeting
target_gender = st.selectbox(
    "Target Gender",
    ["All", "Male", "Female"]
)

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
# GENERATE PLAN
# =========================

if st.button("Generate Plan"):

    filtered_df = df[df["Publisher"].isin(selected_publishers)]

    results = []

    for _, row in filtered_df.iterrows():

        # Audience match (age)
        age_match = sum([row[age] for age in ages])

        base = base_weights[objective].get(row["Publisher"], 0)

        weight = base * age_match

        # =========================
        # DEVICE FACTOR
        # =========================
        device_factor = 0

        if "CTV" in selected_devices:
            device_factor += row["CTV %"]
        if "Desktop" in selected_devices:
            device_factor += row["Desktop %"]
        if "Mobile" in selected_devices:
            device_factor += row["Mobile %"]

        weight = weight * device_factor

        # =========================
        # GENDER FACTOR (soft weighting)
        # =========================
        if target_gender == "Male":
            gender_factor = row["Male %"]
        elif target_gender == "Female":
            gender_factor = row["Female %"]
        else:
            gender_factor = 1  # no bias

        weight = weight * gender_factor

        results.append({
            "Publisher": row["Publisher"],
            "Weight": weight,
            "CPM": row["CPM"],
            "MAU": row["MAU"],
            "Device Factor": device_factor
        })

    results_df = pd.DataFrame(results)

    if results_df["Weight"].sum() == 0:
        st.error("No valid weights. Adjust selections.")
        st.stop()

    # Normalize weights
    results_df["Weight"] = results_df["Weight"] / results_df["Weight"].sum()

    # Budget allocation
    results_df["Budget"] = results_df["Weight"] * budget

    # Impressions
    results_df["Impressions"] = (results_df["Budget"] / results_df["CPM"]) * 1000

    # Reach (device-adjusted)
    results_df["Reach"] = np.minimum(
        results_df["MAU"] * results_df["Device Factor"],
        results_df["Impressions"] / 2.5
    )

    # Frequency
    results_df["Frequency"] = results_df["Impressions"] / results_df["Reach"]

    # Output
    output = results_df[[
        "Publisher", "Budget", "CPM", "Impressions", "Reach", "Frequency"
    ]]

    st.subheader("Plan Output")

    st.dataframe(
        output.style.format({
            "Budget": "R{:,.0f}",
            "Impressions": "{:,.0f}",
            "Reach": "{:,.0f}",
            "Frequency": "{:.2f}"
        })
    )

    # Total reach
    st.subheader("Total Reach")
    st.metric("Estimated Reach", int(output["Reach"].sum()))

    # Chart
    st.bar_chart(output.set_index("Publisher")["Reach"])

    # =========================
    # EXPORT
    # =========================

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        output.to_excel(writer, index=False, sheet_name='Plan')

        inputs_df = pd.DataFrame({
            "Parameter": ["Budget", "Objective", "Ages", "Publishers", "Devices", "Gender"],
            "Value": [
                budget,
                objective,
                ", ".join(ages),
                ", ".join(selected_publishers),
                ", ".join(selected_devices),
                target_gender
            ]
        })

        inputs_df.to_excel(writer, index=False, sheet_name='Inputs')

    st.download_button(
        label="Download Plan (Excel)",
        data=buffer.getvalue(),
        file_name="CTV_Plan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
