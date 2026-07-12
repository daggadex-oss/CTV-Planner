import streamlit as st
import pandas as pd
import io
import os

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    layout="wide",
    page_title="CTV Planner — CTV OS™",
    page_icon="📺",
)

# =========================
# STYLING — Tactical Telemetry (aligned with CTV OS™)
# =========================
st.markdown("""
<style>
/* === Base === */
:root {
    --bg:        #111111;
    --surface:   #1a1a1a;
    --surface-2: #1e1e1e;
    --border:    rgba(255, 255, 255, 0.08);
    --fg:        #e8e8e8;
    --muted:     #888888;
    --accent:    #ffc700;
    --blue:      #2f5bff;
    --mono:      'JetBrains Mono', 'SF Mono', 'Cascadia Code', ui-monospace, monospace;
    --sans:      'SF Pro Display', system-ui, -apple-system, 'Segoe UI', 'Helvetica Neue', sans-serif;
}

.stApp {
    background-color: var(--bg);
    color: var(--fg);
    font-family: var(--sans);
    -webkit-font-smoothing: antialiased;
}

/* === Typography === */
h1 {
    font-family: var(--sans) !important;
    font-size: clamp(1.6rem, 3vw, 2.4rem) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    color: var(--fg) !important;
    margin-bottom: 0.25rem !important;
}

h2, h3 {
    font-family: var(--sans) !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
    color: var(--fg) !important;
}

p, li, .stMarkdown p {
    color: var(--fg) !important;
    font-family: var(--sans) !important;
}

/* === Metric cards — flat surface, no gradient === */
div[data-testid="stMetric"] {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 18px 20px !important;
}

div[data-testid="stMetricLabel"] > div {
    font-family: var(--sans) !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: var(--muted) !important;
    font-weight: 500 !important;
}

div[data-testid="stMetricValue"] > div {
    font-family: var(--mono) !important;
    font-size: 1.75rem !important;
    font-weight: 500 !important;
    color: var(--fg) !important;
    font-variant-numeric: tabular-nums !important;
}

/* === Buttons === */
.stButton > button {
    background-color: var(--accent) !important;
    color: #111111 !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: var(--sans) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.55rem 1.25rem !important;
    transition: opacity 0.15s ease !important;
}

.stButton > button:hover {
    opacity: 0.9 !important;
}

.stButton > button:active {
    transform: scale(0.98) !important;
}

/* Download button — secondary style */
.stDownloadButton > button {
    background-color: transparent !important;
    color: var(--fg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: var(--sans) !important;
    font-size: 0.85rem !important;
}

.stDownloadButton > button:hover {
    border-color: rgba(255,255,255,0.2) !important;
    background-color: rgba(255,255,255,0.04) !important;
}

/* === Inputs === */
.stNumberInput input,
.stTextInput input {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--fg) !important;
    font-family: var(--mono) !important;
    font-size: 0.875rem !important;
}

.stSelectbox > div > div,
.stMultiSelect > div > div {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--fg) !important;
}

/* === Expander === */
div[data-testid="stExpander"] {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

div[data-testid="stExpander"] summary {
    color: var(--fg) !important;
    font-family: var(--sans) !important;
    font-size: 0.875rem !important;
}

/* === Dataframe === */
.stDataFrame {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

.stDataFrame table {
    font-family: var(--mono) !important;
    font-size: 0.8rem !important;
    font-variant-numeric: tabular-nums !important;
}

/* === Input block container === */
.block {
    background-color: var(--surface);
    border: 1px solid var(--border);
    padding: 24px;
    border-radius: 10px;
    margin-bottom: 20px;
}

/* === Widget labels — uppercase tracking === */
div[data-testid="stWidgetLabel"] > label,
div[data-testid="stWidgetLabel"] p {
    font-family: var(--sans) !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    color: var(--muted) !important;
    font-weight: 500 !important;
}

/* === Multiselect — beat Streamlit emotion cache with higher specificity === */
.stApp [data-testid="stMultiSelect"] [data-baseweb="select"],
.stApp [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
.stApp [data-testid="stMultiSelect"] [data-baseweb="select"] > div > div {
    background-color: #1a1a1a !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
}

/* === Multiselect tag chips === */
.stApp [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background-color: rgba(47, 91, 255, 0.25) !important;
    border: 1px solid rgba(47, 91, 255, 0.5) !important;
    border-radius: 4px !important;
    font-size: 0.75rem !important;
    font-family: var(--sans) !important;
}

.stApp [data-testid="stMultiSelect"] span[data-baseweb="tag"] span {
    color: #e8e8e8 !important;
}

.stApp [data-testid="stMultiSelect"] span[data-baseweb="tag"] svg {
    fill: #888888 !important;
}

/* === Multiselect input text === */
.stApp [data-testid="stMultiSelect"] input {
    color: #e8e8e8 !important;
    background-color: transparent !important;
    caret-color: #e8e8e8 !important;
}

/* === Bar chart container === */
.stVegaLiteChart {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 16px !important;
}

/* === Alert / error messages === */
div[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-family: var(--sans) !important;
    font-size: 0.875rem !important;
}

/* === Horizontal rule === */
hr {
    border-color: var(--border) !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown(
    '<p style="font-family:\'SF Pro Display\',system-ui,sans-serif;font-size:10px;'
    'text-transform:uppercase;letter-spacing:0.18em;color:#888888;margin-bottom:6px;">'
    'CTV OS™ &nbsp;·&nbsp; Media Planning</p>',
    unsafe_allow_html=True,
)
st.title("CTV Planner")
st.markdown(
    '<p style="color:#888888;font-size:0.875rem;margin-top:-8px;margin-bottom:0;">'
    'More control. Less waste. Greater transparency.</p>',
    unsafe_allow_html=True,
)

# =========================
# LOAD DATA (V8)
# =========================
file_path = "CTV_Planner_Data_Source_v8.xlsx"

@st.cache_data
def load_data(path):
    publishers = pd.read_excel(path)
    tiers = pd.read_excel(path, sheet_name="Tier Pricing")
    return publishers, tiers

if not os.path.exists(file_path):
    st.error("Data file not found. Please ensure CTV_Planner_Data_Source_v8.xlsx is in the repo.")
    st.stop()

try:
    df, tier_df = load_data(file_path)
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# =========================
# GUIDE
# =========================
with st.expander("How this planner works"):

    st.markdown("""
### Quick Start
1. Enter your **budget**
2. Select your **campaign objective**
3. Define your **target audience (age + gender)**
4. Choose **devices**
5. Select **curated packages**
6. Click **Generate Plan**

---

### Curated Packages Explained

- **Premium Curated** — High-quality, fully addressable supply with maximum control
- **Core Curated** — Balanced mix of quality and scale for efficient delivery
- **Scaled Pool** — Cost-efficient reach extension via broader supply

---

### How the Plan is Calculated

The planner balances three key factors: **Audience Fit**, **Supply Quality**, and **Inventory Availability**.

---

### How to Read the Output

- **Budget** → Allocation of spend
- **Reach** → Estimated unique users
- **Frequency** → Average exposures
- **Blended CPM** → Overall efficiency

---

### Planning Playbooks

- Premium only → Quality
- Premium + Core → Balanced
- Core + Scaled → Efficient reach
""")

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
            ["Awareness", "Consideration", "Conversion"],
            help="Determines how budget is weighted across supply"
        )

    with col3:
        target_gender = st.selectbox(
            "Target Gender",
            ["All", "Male", "Female"],
            help="Adjusts delivery weighting based on gender composition"
        )

    ages = st.multiselect(
        "Target Age Groups",
        ["18-24", "25-34", "35-44", "45-54", "55+"],
        default=["25-34"],
        help="Prioritises publishers with strong audience alignment"
    )

    selected_devices = st.multiselect(
        "Devices",
        ["CTV", "Desktop", "Mobile"],
        default=["CTV", "Desktop", "Mobile"],
        help="Controls delivery environments"
    )

    selected_tiers = st.multiselect(
        "Curated Packages",
        ["Premium Curated", "Core Curated", "Scaled Pool"],
        default=["Premium Curated"],
        help="Combine tiers to balance quality, scale, and efficiency"
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
        st.error("Select at least one curated package.")
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

            age_match = sum([row[age] for age in ages])
            base = base_weights[objective].get(row["Publisher"], 0.1)
            weight = base * age_match

            device_factor = 0
            if "CTV" in selected_devices:
                device_factor += row["CTV %"]
            if "Desktop" in selected_devices:
                device_factor += row["Desktop %"]
            if "Mobile" in selected_devices:
                device_factor += row["Mobile %"]

            weight *= device_factor

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
        st.error("No valid weights for the selected inputs.")
        st.stop()

    # =========================
    # CALCULATIONS
    # =========================
    results_df["Weight"] /= results_df["Weight"].sum()
    results_df["Budget"] = results_df["Weight"] * budget
    results_df["Impressions"] = (results_df["Budget"] / results_df["CPM"]) * 1000
    reach_cap = results_df["MAU"] * results_df["Device Factor"]
    reach_imp = results_df["Impressions"] / 2.5
    results_df["Reach"] = pd.concat([reach_cap, reach_imp], axis=1).min(axis=1)
    results_df["Frequency"] = results_df["Impressions"] / results_df["Reach"].replace(0, float("nan"))

    # =========================
    # AGGREGATE (NO DUPES)
    # =========================
    aggregated_df = results_df.groupby("Publisher").agg({
        "Budget": "sum",
        "Impressions": "sum",
        "Reach": "sum"
    }).reset_index()

    aggregated_df["Frequency"] = aggregated_df["Impressions"] / aggregated_df["Reach"].replace(0, float("nan"))
    aggregated_df["CPM"] = (aggregated_df["Budget"] / aggregated_df["Impressions"]) * 1000

    output = aggregated_df

    # =========================
    # KPIs
    # =========================
    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Reach", f"{int(output['Reach'].sum()):,}")

    with col2:
        st.metric("Total Impressions", f"{int(output['Impressions'].sum()):,}")

    with col3:
        blended_cpm = (output["Budget"].sum() / output["Impressions"].sum()) * 1000
        st.metric("Blended CPM", f"R{blended_cpm:,.0f}")

    # =========================
    # OUTPUT
    # =========================
    col1, col2 = st.columns([2, 1])

    with col1:
        st.dataframe(
            output.style.format({
                "Budget": "R{:,.0f}",
                "Impressions": "{:,.0f}",
                "Reach": "{:,.0f}",
                "Frequency": "{:.2f}",
                "CPM": "R{:,.0f}"
            }),
            use_container_width=True,
        )

        st.markdown("""
**How to read this plan**

Higher **Reach** = more unique users · Higher **Frequency** = more repeated exposure · Lower **CPM** = more efficient spend

Balance tiers to optimise quality, scale, and efficiency.
""")

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
