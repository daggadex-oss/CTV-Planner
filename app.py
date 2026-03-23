import streamlit as st
import pandas as pd
import numpy as np

# Load data
df = pd.read_excel("CTV_Planner_Data_Source_v3.xlsx")

st.title("CTV Planner")

# Inputs
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

# Base weights
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

if st.button("Generate Plan"):

    results = []

    for _, row in df.iterrows():

        # Audience match score
        match = sum([row[age] for age in ages])

        # Base weight
        base = base_weights[objective].get(row["Publisher"], 0)

        weight = base * match

        results.append({
            "Publisher": row["Publisher"],
            "Weight": weight,
            "CPM": row["CPM"],
            "MAU": row["MAU"]
        })

    results_df = pd.DataFrame(results)

    # Normalise weights
    results_df["Weight"] = results_df["Weight"] / results_df["Weight"].sum()

    # Budget allocation
    results_df["Budget"] = results_df["Weight"] * budget

    # Impressions
    results_df["Impressions"] = (results_df["Budget"] / results_df["CPM"]) * 1000

    # Reach (simple model)
    results_df["Reach"] = np.minimum(
        results_df["MAU"],
        results_df["Impressions"] / 2.5
    )

    # Frequency
    results_df["Frequency"] = results_df["Impressions"] / results_df["Reach"]

    # Clean output
    output = results_df[[
        "Publisher", "Budget", "CPM", "Impressions", "Reach", "Frequency"
    
    ]]

    st.subheader("Plan Output")
    st.dataframe(output)
    import io

# Create Excel file in memory
buffer = io.BytesIO()

with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    output.to_excel(writer, index=False, sheet_name='Plan')

    # Inputs sheet
    inputs_df = pd.DataFrame({
        "Parameter": ["Budget", "Objective", "Ages"],
        "Value": [budget, objective, ", ".join(ages)]
    })
    inputs_df.to_excel(writer, index=False, sheet_name='Inputs')

# Download button
st.download_button(
    label="Download Plan (Excel)",
    data=buffer.getvalue(),
    file_name="CTV_Plan.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

    st.subheader("Total Reach")
    st.metric("Estimated Reach", int(output["Reach"].sum()))

    st.bar_chart(output.set_index("Publisher")["Reach"])
