import streamlit as st
import pandas as pd
import numpy as np
import io
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(layout="wide")

# =========================
# STYLING
# =========================
st.markdown("""
<style>
.stApp {
    background-color: #1A1A1A;
    color: white;
}

h1 {
    color: #2F5BFF;
}

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #2F5BFF, #6C8CFF);
    padding: 15px;
    border-radius: 12px;
    color: white;
}

button {
    background-color: #FFC700 !important;
    color: black !important;
    border-radius: 8px !important;
}

.block {
    background-color: #262626;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# LOAD DATA (V8)
# =========================
file_path = "CTV_Planner_Data_Source_v8.xlsx"

if not os.path.exists(file_path):
    st.error("Data file not found. Please upload V8 dataset.")
    st.stop()

df = pd.read_excel(file_path)
tier_df = pd.read_excel(file_path, sheet_name="Tier Pricing")

# =========================
# HEADER
# =========================
st.title("Curated CTV Planner")
st.markdown("**More control. Less waste. Greater transparency.**")

# =========================
# INPUTS
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

    selected_devices = st.multiselect(
        "Devices",
        ["CTV", "Desktop", "Mobile"],
        default=["CTV", "Desktop", "Mobile"]
    )

    selected_tiers = st.multiselect(
        "Curated Packages",
        ["Premium Curated", "Core Curated", "Scaled Pool"],
        default=["Premium Curated"]
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
        "DStv Stream": 0.1,
        "Scaled Pool": 0.15
    },
    "Consideration": {
        "Reach Africa": 0.3,
        "eVOD": 0.25,
        "SABC+": 0.2,
        "DStv Stream": 0.15,
        "VIU": 0.1,
        "Scaled Pool": 0.15
    },
    "Conversion": {
        "DStv Stream": 0.4,
        "Reach Africa": 0.25,
        "eVOD": 0.2,
        "SABC+": 0.1,
        "VIU": 0.05,
        "Scaled Pool": 0.15
    }
}

# =========================
# TIER MAPPING
# =========================
tier_mapping = {
    "Premium Curated": "Tier_Premium",
    "Core Curated": "Tier_Core",
    "Scaled Pool": "Tier_Scaled"
}

# =========================
# GENERATE PLAN
# =========================
if generate:

    if len(selected_tiers) == 0:
        st.error("Please select at least one package.")
        st.stop()

    results = []

    for tier in selected_tiers:

        tier_col = tier_mapping[tier]
        tier_publishers = df[df[tier_col] == 1]

        tier_row = tier_df[tier_df["Tier"] == tier]

        if tier_row.empty:
            st.error(f"Tier '{tier}' not found in data.")
            st.stop()

        tier_cpm = tier_row["CPM"].values[0]

        for _, row in tier_publishers.iterrows():

            # AGE MATCH
            age_match = sum([row[age] for age in ages])

            # BASE WEIGHT (safe fallback included)
            base = base_weights[objective].get(row["Publisher"], 0.1)

            weight = base * age_match

            # DEVICE FACTOR
            device_factor = 0
            if "CTV" in selected_devices:
                device_factor += row["CTV %"]
            if "Desktop" in selected_devices:
                device_factor += row["Desktop %"]
            if "Mobile" in selected_devices:
                device_factor += row["Mobile %"]

            weight *= device_factor

            # GENDER FACTOR
            if target_gender == "Male":
                weight *= row["Male %"]
            elif target_gender == "Female":
                weight *= row["Female %"]

            results.append({
                "Publisher": row["Publisher"],
                "Tier": tier,
                "Weight": weight,
                "CPM": tier_cpm,
                "MAU": row["MAU"],
                "Device Factor": device_factor
            })

    results_df = pd.DataFrame(results)

    if results_df["Weight"].sum() == 0:
        st.error("No valid weights.")
        st.stop()

    # =========================
    # NORMALISE + CALCULATE
    # =========================
    results_df["Weight"] /= results_df["Weight"].sum()
    results_df["Budget"] = results_df["Weight"] * budget
    results_df["Impressions"] = (results_df["Budget"] / results_df["CPM"]) * 1000
    results_df["Reach"] = np.minimum(
        results_df["MAU"] * results_df["Device Factor"],
        results_df["Impressions"] / 2.5
    )
    results_df["Frequency"] = results_df["Impressions"] / results_df["Reach"]

    # =========================
    # AGGREGATE (FIX DUPLICATES)
    # =========================
    aggregated_df = results_df.groupby("Publisher").agg({
        "Budget": "sum",
        "Impressions": "sum",
        "Reach": "sum"
    }).reset_index()

    aggregated_df["Frequency"] = aggregated_df["Impressions"] / aggregated_df["Reach"]
    aggregated_df["CPM"] = (aggregated_df["Budget"] / aggregated_df["Impressions"]) * 1000

    output = aggregated_df

    # =========================
    # KPIs
    # =========================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Reach", f"{int(output['Reach'].sum()):,}")

    with col2:
        st.metric("Total Impressions", f"{int(output['Impressions'].sum()):,}")

    with col3:
        blended_cpm = (output["Budget"].sum() / output["Impressions"].sum()) * 1000
        st.metric("Blended CPM", f"R{int(blended_cpm)}")

    # =========================
    # OUTPUT
    # =========================
    col1, col2 = st.columns([2,1])

    with col1:
        st.dataframe(
            output.style.format({
                "Budget": "R{:,.0f}",
                "Impressions": "{:,.0f}",
                "Reach": "{:,.0f}",
                "Frequency": "{:.2f}",
                "CPM": "R{:,.0f}"
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
