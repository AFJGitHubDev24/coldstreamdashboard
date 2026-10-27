import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# Set page config
st.set_page_config(page_title="Cold-Chain Sensor Dashboard", layout="wide")
st.title("🌡️ Cold-Chain Environmental Monitoring Dashboard")
st.markdown("This dashboard displays real-time tracking of temperature, humidity, and gas spoilage levels across cold-chain operations.")

# 1. Sidebar Configuration for Cargo Types & Multi-Range Thresholds
st.sidebar.header("📦 Cold-Chain Management")
cargo_type = st.sidebar.selectbox(
    "Select Cargo Category:",
    ["Perishable Foods", "Pharmaceuticals"]
)

# Regulatory Threshold Profiles (Using Range Boundaries)
if cargo_type == "Perishable Foods":
    TEMP_THRESHOLD = 8.0         # Max 8°C
    
    # Permissible Humidity Range (60% to 85%)
    HUMID_MIN = 60.0             
    HUMID_MAX = 85.0             
    
    # Permissible Gas Spoilage Range (0 to 100 ppm)
    GAS_MIN = 0.0                
    GAS_MAX = 100.0              
else:
    TEMP_THRESHOLD = 8.0         # Max 8°C
    
    # Permissible Humidity Range (35% to 60%)
    HUMID_MIN = 35.0             
    HUMID_MAX = 60.0             
    
    # Permissible Gas Spoilage Range (0 to 50 ppm)
    GAS_MIN = 0.0                
    GAS_MAX = 50.0               

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
### Safe Operating Ranges ({cargo_type})
* **Temp Limit:** Max {TEMP_THRESHOLD}°C
* **Permissible Humidity:** {HUMID_MIN}% – {HUMID_MAX}%
* **Permissible Gas:** {GAS_MIN} – {GAS_MAX} ppm
""")

# 2. Generate Mock Data tuned to the cargo profile
@st.cache_data
def load_mock_data(cargo):
    now = datetime.now()
    timestamps = [now - timedelta(minutes=x) for x in range(60, 0, -1)]
    
    # Data generation ranges intentionally overshoot limits occasionally for demonstration
    if cargo == "Perishable Foods":
        temp_data = np.random.uniform(2.0, 10.0, size=60)
        humid_data = np.random.uniform(55.0, 90.0, size=60)
        gas_data = np.random.uniform(10.0, 120.0, size=60)
    else: # Pharmaceuticals
        temp_data = np.random.uniform(1.0, 9.0, size=60)
        humid_data = np.random.uniform(30.0, 65.0, size=60)
        gas_data = np.random.uniform(5.0, 65.0, size=60)

    data = {
        "Timestamp": timestamps,
        "Temperature (°C)": temp_data,
        "Humidity (%)": humid_data,
        "Gas Spoilage (ppm)": gas_data
    }
    return pd.DataFrame(data)

df = load_mock_data(cargo_type)

# Extract latest readings
latest = df.iloc[-1]
current_temp = latest['Temperature (°C)'].round(1)
current_humid = latest['Humidity (%)'].round(1)
current_gas = latest['Gas Spoilage (ppm)'].round(0)

# 3. Dynamic Range Violation Warnings
st.subheader("⚠️ System Status & Alerts")

alerts = []

# Temperature Check
if current_temp > TEMP_THRESHOLD:
    alerts.append(f"❌ **Temperature Violation:** Current temperature ({current_temp}°C) is above the maximum limit ({TEMP_THRESHOLD}°C)!")

# Humidity Range Check
if current_humid > HUMID_MAX:
    alerts.append(f"❌ **Humidity Out of Range (High):** Current humidity ({current_humid}%) exceeds the upper safe limit ({HUMID_MAX}%). Risk of mold/condensation.")
elif current_humid < HUMID_MIN:
    alerts.append(f"⚠️ **Humidity Out of Range (Low):** Current humidity ({current_humid}%) drops below the minimum limit ({HUMID_MIN}%). Risk of dehydration/static.")

# Gas Spoilage Range Check
if current_gas > GAS_MAX:
    alerts.append(f"🚨 **Gas Spoilage Violation:** Volatile gas levels ({current_gas} ppm) have breached the maximum permissible ceiling ({GAS_MAX} ppm)!")
elif current_gas < GAS_MIN:
    alerts.append(f"⚠️ **Gas Baseline Error:** Current gas reading ({current_gas} ppm) is below the minimum sensor baseline threshold ({GAS_MIN} ppm).")

# Render active alerts
if alerts:
    for alert in alerts:
        st.error(alert)
else:
    st.success(f"✅ **System Normal:** All parameters are safely maintained within the permissible ranges for **{cargo_type}**.")

# 4. Display Current Metrics
st.subheader("Current Readings")
col1, col2, col3 = st.columns(3)

# Calculate Deltas dynamically relative to ranges
temp_delta = f"+{round(current_temp - TEMP_THRESHOLD, 1)} °C over limit" if current_temp > TEMP_THRESHOLD else None

if current_humid > HUMID_MAX:
    humid_delta = f"+{round(current_humid - HUMID_MAX, 1)}% over max"
elif current_humid < HUMID_MIN:
    humid_delta = f"-{round(HUMID_MIN - current_humid, 1)}% below min"
else:
    humid_delta = None

gas_delta = f"+{round(current_gas - GAS_MAX, 0)} ppm over max" if current_gas > GAS_MAX else (f"-{round(GAS_MIN - current_gas, 0)} ppm below min" if current_gas < GAS_MIN else None)

col1.metric(label="Temperature", value=f"{current_temp} °C", delta=temp_delta, delta_color="inverse")
col2.metric(label="Humidity Range Status", value=f"{current_humid} %", delta=humid_delta, delta_color="inverse")
col3.metric(label="Permissible Gas Level", value=f"{current_gas} ppm", delta=gas_delta, delta_color="inverse")

st.markdown("---")

# 5. Historical Analytics Charts with Visual Target Range Boundaries
st.subheader("Historical Analytics")

# Temperature Chart
fig_temp = px.line(df, x="Timestamp", y="Temperature (°C)", title="Temperature Trends", color_discrete_sequence=["#FF4B4B"])
fig_temp.add_hline(y=TEMP_THRESHOLD, line_dash="dash", line_color="red", annotation_text="Max Temperature Limit")
st.plotly_chart(fig_temp, use_container_width=True)

# Humidity Chart (Displays the dynamic safe operational corridor)
fig_hum = px.line(df, x="Timestamp", y="Humidity (%)", title="Humidity Levels & Permissible Range", color_discrete_sequence=["#1C83E1"])
fig_hum.add_hline(y=HUMID_MAX, line_dash="dash", line_color="red", annotation_text=f"Max Safe Limit ({HUMID_MAX}%)")
fig_hum.add_hline(y=HUMID_MIN, line_dash="dash", line_color="orange", annotation_text=f"Min Safe Limit ({HUMID_MIN}%)")
st.plotly_chart(fig_hum, use_container_width=True)

# Gas Spoilage Chart (Displays upper and lower permissible ceilings)
fig_gas = px.area(df, x="Timestamp", y="Gas Spoilage (ppm)", title="Gas Spoilage Levels & Permissible Limit", color_discrete_sequence=["#00D4B2"])
fig_gas.add_hline(y=GAS_MAX, line_dash="dash", line_color="red", annotation_text=f"Max Permissible ({GAS_MAX} ppm)")
fig_gas.add_hline(y=GAS_MIN, line_dash="dash", line_color="gray", annotation_text=f"Min Baseline ({GAS_MIN} ppm)")
st.plotly_chart(fig_gas, use_container_width=True)

# 6. Data Log Expandable View
with st.expander("View Raw Data Log"):
    st.dataframe(df.sort_values(by="Timestamp", ascending=False), use_container_width=True)
