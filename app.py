import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse
from datetime import datetime
import gspread
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Readings Register", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
        [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; height: 0px !important; }
        .stApp { background-color: #1e120b; color: #ffffff; }
        [data-testid="stSidebar"] { background-color: #2c1d16; border-right: 1px solid #422d22; }
        
        /* Typography */
        h1 { font-size: 22px !important; margin-top: -30px !important; margin-bottom: 10px !important; }
        h3 { font-size: 16px !important; margin-top: 5px !important; margin-bottom: 2px !important; }
        .vn-blue { color: #00F0FF !important; font-size: 0.9em !important; font-weight: normal !important; }
        
        /* Compact Elements */
        div.block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; }
        .blue-divider { border: 0; height: 1px; background: #00F0FF; margin: 5px 0 10px 0 !important; }
        input, textarea, div[data-baseweb="select"] { background-color: #120a06 !important; border: 1px solid #6b4c3a !important; }
    </style>
""", unsafe_allow_html=True)

# --- GLOBALS ---
USER_DIRECTORY = {"Katelyn": "+60193763635", "Thoa": "+601155080892", "Ruth": "+60183668919", "Sarah": "+60168412926", "Tham": "+60169159217", "Tina": "+601121103011", "Hannah": "+60182499896", "hs": "+60122193637"}

@st.cache_data(ttl=600)
def fetch_sheet_records():
    file_path = '/Users/hoksengho/ReadingApp2.0/credentials.json'
    if not os.path.exists(file_path): return pd.DataFrame(), None
    try:
        gc = gspread.service_account(filename=file_path)
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1iPxF9ftWROX-_BbBBGKC3rkgRn5QcCIrvcbB3jVoH1g/edit?usp=sharing")
        return pd.DataFrame(sh.get_worksheet(0).get_all_records()), sh.get_worksheet(0)
    except: return pd.DataFrame(), None

raw_df, target_worksheet = fetch_sheet_records()
if raw_df is None or len(raw_df) == 0:
    raw_df = pd.DataFrame(columns=["Timestamp", "Name", "BibleReference", "ChaptersRead", "GodSpoke", "GodObey", "Phone"])

# --- SIDEBAR ---
st.sidebar.markdown("### 📝 Entry Form <span class='vn-blue'>(Đơn Nhập Liệu)</span>", unsafe_allow_html=True)
selected_name = st.sidebar.selectbox("User", options=list(USER_DIRECTORY.keys()) + ["Others"], key="user_select")

custom_name, custom_phone = "", ""
if selected_name == "Others":
    custom_name = st.sidebar.text_input("Name (Họ và Tên)").strip()
    custom_phone = st.sidebar.text_input("Phone (Số điện thoại)").strip()

with st.sidebar.form(key="reading_form", clear_on_submit=True):
    st.markdown("Date & Time <span class='vn-blue'>(Ngày & Giờ)</span>", unsafe_allow_html=True)
    input_timestamp = st.text_input("TS", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), label_visibility="collapsed")
    st.markdown("Bible Reference <span class='vn-blue'>(Sách & Chương)</span>", unsafe_allow_html=True)
    reading_ref = st.text_input("Ref", label_visibility="collapsed")
    st.markdown("Chapters <span class='vn-blue'>(Số chương)</span>", unsafe_allow_html=True)
    chapters = st.number_input("Chaps", min_value=0, step=1, value=0, label_visibility="collapsed")
    st.markdown("Reflection <span class='vn-blue'>(Suy ngẫm)</span>", unsafe_allow_html=True)
    god_spoke = st.text_area("Spoke", height=60, label_visibility="collapsed")
    st.markdown("Obedience <span class='vn-blue'>(Vâng phục)</span>", unsafe_allow_html=True)
    god_obey = st.text_area("Obey", height=60, label_visibility="collapsed")
    submit_button = st.form_submit_button(label="Submit / Gửi")

if submit_button:
    if target_worksheet is None: st.sidebar.error("DB Error")
    elif selected_name == "Others" and (not custom_name or not custom_phone): st.sidebar.error("Missing fields!")
    else:
        target_worksheet.append_row([input_timestamp, (custom_name if selected_name=="Others" else selected_name), reading_ref, int(chapters), god_spoke, god_obey, (custom_phone if selected_name=="Others" else USER_DIRECTORY.get(selected_name, ""))])
        st.cache_data.clear(); st.rerun()

# --- MAIN PAGE ---
st.markdown("<h1>📚 Readings Register <span class='vn-blue'>(Nhật Ký Đọc Kinh Thánh)</span></h1>", unsafe_allow_html=True)

# Compact Header
today = datetime.now().date()
c1, c2 = st.columns([1, 1.5])
c1.markdown(f"📅 **Current Date** <span class='vn-blue'>(Ngày Hiện Tại)</span>: {today.strftime('%d-%m-%Y')}", unsafe_allow_html=True)
c2.markdown("Period Tracking <span class='vn-blue'>(Chọn mốc thời gian)</span>", unsafe_allow_html=True)
filter_mode = st.radio("Mode", ["Current Month <span class='vn-blue'>(Tháng này)</span>", "Custom Range <span class='vn-blue'>(Tùy chọn)</span>"], horizontal=True, label_visibility="collapsed")

st.markdown("<hr class='blue-divider'>", unsafe_allow_html=True)

start = today.replace(day=1) if "Month" in filter_mode else st.date_input("Start / Từ ngày", today.replace(day=1))
end = today if "Month" in filter_mode else st.date_input("End / Đến ngày", today)

raw_df["ParsedDate"] = pd.to_datetime(raw_df["Timestamp"], format='mixed', errors='coerce').dt.date
filtered_df = raw_df[(raw_df["ParsedDate"] >= start) & (raw_df["ParsedDate"] <= end)]

if len(filtered_df) > 0:
    all_users = filtered_df["Name"].dropna().unique()
    calcs = []
    days_range = (end - start).days + 1
    for u in all_users:
        u_df = filtered_df[filtered_df["Name"] == u]
        sessions = len(u_df)
        calcs.append({"Name": u, "Chapters": pd.to_numeric(u_df["ChaptersRead"], errors='coerce').sum(), 
                      "Sessions": sessions, "Days Read": u_df["Timestamp"].nunique(), 
                      "Missed Days": max(0, days_range - u_df["Timestamp"].nunique()),
                      "Reading Rate": f"{int(round((sessions / days_range) * 100, 0))}%"})
    
    calc_df = pd.DataFrame(calcs)
    # Tighter title spacing
    st.markdown("### 📊 Progress Tracking Chart <span class='vn-blue'>(Bảng Tiến Độ)</span>", unsafe_allow_html=True)
    
    melted = calc_df.melt(id_vars=["Name", "Reading Rate"], value_vars=["Chapters", "Sessions", "Days Read", "Missed Days"], var_name="Metric", value_name="Count")
    fig = px.bar(melted, x="Count", y="Name", color="Metric", orientation='h', barmode="stack", 
                 color_discrete_map={"Chapters": "#A0C4FF", "Sessions": "#B9FBC0", "Days Read": "#FDE2E4", "Missed Days": "#FFCC80"})
    
    for _, row in calc_df.iterrows():
        fig.add_annotation(x=row["Chapters"]+row["Sessions"]+row["Days Read"]+row["Missed Days"], y=row["Name"], text=row["Reading Rate"], 
                           showarrow=False, xanchor='left', xshift=10, font=dict(color="#00F0FF", size=24, weight="bold"))
        
    fig.update_layout(paper_bgcolor='#1e120b', plot_bgcolor='#1e120b', font_color="white", margin=dict(t=5, b=0),
                      legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5),
                      xaxis=dict(showline=True, linewidth=1, linecolor='white', gridcolor='#422d22'),
                      yaxis=dict(showline=True, linewidth=1, linecolor='white'))
    st.plotly_chart(fig, use_container_width=True)

# Bottom Sections
st.markdown(f"### 📲 WhatsApp Direct Share <span class='vn-blue' style='font-size:12px;'>(Chia Sẻ Qua WhatsApp)</span>", unsafe_allow_html=True)
share_user = st.selectbox("Share User", options=all_users, label_visibility="collapsed")
if not calc_df.empty:
    row = calc_df[calc_df["Name"] == share_user].iloc[0]
    wa_link = f"https://wa.me/{USER_DIRECTORY.get(share_user, '').replace('+', '')}?text=Bible Reading Update: {share_user} - Rate: {row['Reading Rate']}"
    st.markdown(f'<a href="{wa_link}" target="_blank"><button style="width:100%; padding:10px; background:#2c1d16; color:white; border:1px solid #00F0FF;">💬 Launch WhatsApp</button></a>', unsafe_allow_html=True)

st.markdown(f"### 📋 Shared Reflection Journal <span class='vn-blue' style='font-size:12px;'>(Nhật Ký Suy Ngẫm)</span>", unsafe_allow_html=True)
st.dataframe(filtered_df.sort_values(by="Timestamp", ascending=False), use_container_width=True)