import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Readings Register", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
        [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; height: 0px !important; }
        .stApp { background-color: #1e120b; color: #ffffff; }
        [data-testid="stSidebar"] { background-color: #2c1d16; border-right: 1px solid #422d22; }
        h1 { font-size: 22px !important; margin-top: -30px !important; margin-bottom: 10px !important; }
        h3 { font-size: 16px !important; margin-top: 5px !important; margin-bottom: 2px !important; }
        .vn-blue { color: #00F0FF !important; font-size: 0.9em !important; font-weight: normal !important; }
        div.block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; }
        .blue-divider { border: 0; height: 1px; background: #00F0FF; margin: 5px 0 10px 0 !important; }
    </style>
""", unsafe_allow_html=True)

# --- GLOBALS ---
USER_DIRECTORY = {"Katelyn": "+60193763635", "Thoa": "+601155080892", "Ruth": "+60183668919", "Sarah": "+60168412926", "Tham": "+60169159217", "Tina": "+601121103011", "Hannah": "+60182499896", "hs": "+60122193637"}
all_users = list(USER_DIRECTORY.keys())

# --- DATA FETCHING (Hybrid) ---
@st.cache_data(ttl=600)
def fetch_sheet_records():
    # 1. Try Cloud Secrets first
    try:
        if "gcp_service_account" in st.secrets:
            gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        else:
            # 2. Fallback to Local file
            file_path = '/Users/hoksengho/ReadingApp2.0/credentials.json'
            if not os.path.exists(file_path): return pd.DataFrame(), None
            gc = gspread.service_account(filename=file_path)
            
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1iPxF9ftWROX-_BbBBGKC3rkgRn5QcCIrvcbB3jVoH1g/edit?usp=sharing")
        return pd.DataFrame(sh.get_worksheet(0).get_all_records()), sh.get_worksheet(0)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame(), None

raw_df, target_worksheet = fetch_sheet_records()
if raw_df is None or raw_df.empty:
    raw_df = pd.DataFrame(columns=["Timestamp", "Name", "BibleReference", "ChaptersRead", "GodSpoke", "GodObey", "Phone"])

# --- SIDEBAR ---
st.sidebar.markdown("### 📝 Entry Form <span class='vn-blue'>(Đơn Nhập Liệu)</span>", unsafe_allow_html=True)
selected_name = st.sidebar.selectbox("User", options=all_users + ["Others"], key="user_select")

custom_name, custom_phone = "", ""
if selected_name == "Others":
    custom_name = st.sidebar.text_input("Name (Họ và Tên)").strip()
    custom_phone = st.sidebar.text_input("Phone (Số điện thoại)").strip()

with st.sidebar.form(key="reading_form", clear_on_submit=True):
    input_timestamp = st.text_input("Date & Time", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    reading_ref = st.text_input("Bible Reference")
    chapters = st.number_input("Chapters", min_value=0, step=1, value=0)
    god_spoke = st.text_area("Reflection (God Spoke)")
    god_obey = st.text_area("Obedience (God Obey)")
    submit_button = st.form_submit_button(label="Submit / Gửi")

if submit_button:
    if target_worksheet is None: st.sidebar.error("Database connection failed.")
    elif selected_name == "Others" and (not custom_name or not custom_phone): st.sidebar.error("Missing fields!")
    else:
        name_val = custom_name if selected_name=="Others" else selected_name
        phone_val = custom_phone if selected_name=="Others" else USER_DIRECTORY.get(selected_name, "")
        target_worksheet.append_row([input_timestamp, name_val, reading_ref, int(chapters), god_spoke, god_obey, phone_val])
        st.cache_data.clear()
        st.rerun()

# --- MAIN PAGE ---
st.markdown("<h1>📚 Readings Register <span class='vn-blue'>(Nhật Ký Đọc Kinh Thánh)</span></h1>", unsafe_allow_html=True)

today = datetime.now().date()
c1, c2 = st.columns([1, 1.5])
c1.markdown(f"📅 **Date**: {today.strftime('%d-%m-%Y')}", unsafe_allow_html=True)
filter_mode = c2.radio("Mode", ["Current Month", "Custom Range"], horizontal=True)

st.markdown("<hr class='blue-divider'>", unsafe_allow_html=True)

start = today.replace(day=1) if "Month" in filter_mode else st.date_input("Start", today.replace(day=1))
end = today if "Month" in filter_mode else st.date_input("End", today)

filtered_df = pd.DataFrame()
calc_df = pd.DataFrame()

if not raw_df.empty:
    raw_df["ParsedDate"] = pd.to_datetime(raw_df["Timestamp"], format='mixed', errors='coerce').dt.date
    filtered_df = raw_df[(raw_df["ParsedDate"] >= start) & (raw_df["ParsedDate"] <= end)]

    if not filtered_df.empty:
        days_range = (end - start).days + 1
        calcs = []
        for u in filtered_df["Name"].dropna().unique():
            u_df = filtered_df[filtered_df["Name"] == u]
            sessions = len(u_df)
            calcs.append({
                "Name": u, 
                "Chapters": pd.to_numeric(u_df["ChaptersRead"], errors='coerce').sum(), 
                "Sessions": sessions, 
                "Days Read": u_df["Timestamp"].nunique(), 
                "Missed Days": max(0, days_range - u_df["Timestamp"].nunique()),
                "Reading Rate": f"{int(round((sessions / days_range) * 100, 0))}%"
            })
        calc_df = pd.DataFrame(calcs)

if not calc_df.empty:
    st.markdown("### 📊 Progress Tracking Chart", unsafe_allow_html=True)
    melted = calc_df.melt(id_vars=["Name", "Reading Rate"], value_vars=["Chapters", "Sessions", "Days Read", "Missed Days"], var_name="Metric", value_name="Count")
    fig = px.bar(melted, x="Count", y="Name", color="Metric", orientation='h', barmode="stack", 
                 color_discrete_map={"Chapters": "#A0C4FF", "Sessions": "#B9FBC0", "Days Read": "#FDE2E4", "Missed Days": "#FFCC80"})
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### 📲 WhatsApp Direct Share", unsafe_allow_html=True)
share_user = st.selectbox("Share User", options=all_users)
if not calc_df.empty and share_user in calc_df["Name"].values:
    row = calc_df[calc_df["Name"] == share_user].iloc[0]
    wa_link = f"https://wa.me/{USER_DIRECTORY.get(share_user, '').replace('+', '')}?text=Bible Reading Update: {share_user} - Rate: {row['Reading Rate']}"
    st.markdown(f'<a href="{wa_link}" target="_blank"><button style="width:100%; padding:10px; background:#2c1d16; color:white; border:1px solid #00F0FF;">💬 Launch WhatsApp</button></a>', unsafe_allow_html=True)
else:
    st.info("No data available to share for this user.")

st.markdown("### 📋 Shared Reflection Journal", unsafe_allow_html=True)
if not filtered_df.empty:
    st.dataframe(filtered_df.sort_values(by="Timestamp", ascending=False), use_container_width=True)