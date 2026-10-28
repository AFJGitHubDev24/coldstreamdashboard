import streamlit as st
import boto3
import pandas as pd
import plotly.express as px
from boto3.dynamodb.conditions import Key
import time

st.set_page_config(
    page_title="Cold-Chain Monitoring Dashboard",
    page_icon="❄️",
    layout="wide"
)

# Initialize AWS DynamoDB Resource
@st.cache_resource
def get_dynamodb_resource():
    return boto3.resource('dynamodb', region_name='us-east-1') # Update region if needed

dynamodb = get_dynamodb_resource()
TABLE_NAME = "ColdChainTelemetry123"

def fetch_telemetry_data(device_id="coldchainesp32", limit=300):
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # 1. Attempt Query to get LATEST records first
        try:
            response = table.query(
                KeyConditionExpression=Key('device_id').eq(device_id),
                ScanIndexForward=False,  # Fetch newest items first
                Limit=limit
            )
            items = response.get('Items', [])
        except Exception:
            items = []
            
        # 2. Fallback to Scan if Query is empty or fails
        if not items:
            response = table.scan(Limit=limit)
            items = response.get('Items', [])
            
        if not items:
            return pd.DataFrame()

        # 3. Clean Decimal data types from DynamoDB
        cleaned_items = []
        for item in items:
            row = {}
            for k, v in item.items():
                # Convert Decimal or numeric types to standard Python float/int
                try:
                    row[k] = float(v)
                except (ValueError, TypeError):
                    row[k] = str(v)
            cleaned_items.append(row)

        df = pd.DataFrame(cleaned_items)

        # 4. Handle Timestamps dynamically
        if 'timestamp' in df.columns and not df.empty:
            sample_ts = df['timestamp'].iloc[0]
            # Detect whether epoch is in milliseconds (> 1e11) or seconds
            ts_unit = 'ms' if sample_ts > 1e11 else 's'
            df['datetime'] = pd.to_datetime(df['timestamp'], unit=ts_unit)
            
            # Sort chronologically for proper chart rendering
            df = df.sort_values('datetime', ascending=True)

        return df

    except Exception as e:
        st.error(f"Error querying DynamoDB: {e}")
        return pd.DataFrame()
            
        
# Dashboard UI
st.title("❄️ Cold-Chain Management Dashboard")
st.markdown("Real-time telemetry tracking for cold-chain storage and transit.")

if st.button("🔄 Refresh Data"):
    st.rerun()

df = fetch_telemetry_data()

if not df.empty and 'temperature' in df.columns and 'humidity' in df.columns:
    latest_record = df.iloc[-1]
    latest_temp = latest_record['temperature']
    latest_hum = latest_record['humidity']
    latest_time = latest_record['datetime']

    # Metrics Display
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Temperature (°C)", f"{latest_temp:.1f} °C")
    col2.metric("Current Humidity (%)", f"{latest_hum:.1f} %")
    col3.metric("Last Updated", latest_time.strftime('%H:%M:%S UTC'))

    st.markdown("---")

    # Time-series Charts
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Temperature Over Time")
        fig_temp = px.line(
            df, x='datetime', y='temperature',
            labels={'datetime': 'Time', 'temperature': 'Temperature (°C)'},
            color_discrete_sequence=['#EF553B']
        )
        fig_temp.add_hline(y=8.0, line_dash="dash", line_color="red", annotation_text="Upper Limit (8°C)")
        st.plotly_chart(fig_temp, use_container_width=True)

    with c2:
        st.subheader("Humidity Over Time")
        fig_hum = px.line(
            df, x='datetime', y='humidity',
            labels={'datetime': 'Time', 'humidity': 'Humidity (%)'},
            color_discrete_sequence=['#636EFA']
        )
        st.plotly_chart(fig_hum, use_container_width=True)

    with st.expander("View Raw Telemetry Logs"):
        st.dataframe(df, use_container_width=True)
else:
    st.warning("No telemetry data found in DynamoDB. Ensure the ESP32 is publishing data.")
