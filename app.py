import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse
from datetime import datetime
import json
import gspread
import calendar  

# --- STYLING & COMPACTING CONFIGURATION ---
st.set_page_config(page_title="Readings Register", layout="wide")

# Injecting comprehensive CSS styling targeting user inputs and layout headers
st.markdown("""
    <style>
        /* Remove Top White Header Bar & Decoration lines */
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
            height: 0px !important;
        }
        .stApp [data-testid="stDecoration"] {
            display: none !important;
        }
        
        /* Base Background Theme Adjustments */
        .stApp {
            background-color: #1e120b;
            color: #ffffff;
        }
        
        /* Sidebar layout styling */
        [data-testid="stSidebar"] {
            background-color: #2c1d16;
            border-right: 1px solid #422d22;
        }
        
        /* Darker, High-Contrast Data Entry Inputs */
        div[data-baseweb="select"] > div, 
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div,
        input, textarea {
            background-color: #120a06 !important;
            color: #ffffff !important;
            border: 1px solid #6b4c3a !important;
        }
        
        /* High contrast for label headers sitting over inputs */
        label, p, span, .stWidgetLabel {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Mobile-Friendly Prompt Banner styling for the Sidebar Arrow indicator */
        .mobile-sidebar-hint {
            background-color: #120a06;
            border: 2px dashed #00F0FF;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 14px;
            text-align: right;
            color: #ffffff;
        }
        
        /* GLOBAL STYLING: Forces all Markdown translation labels, headers, and italic groups to render Luminous Blue */
        .vn-blue, em, h2 span, h3 span, p span {
            color: #00F0FF !important;
            font-weight: normal !important;
            font-style: normal !important;
        }
        
        /* Dark Theme Style for Submit Entry Button */
        button[kind="primaryFormSubmit"], .stFormSubmitButton > button {
            background-color: #120a06 !important;
            color: #ffffff !important;
            border: 1px solid #8c644d !important;
            font-weight: bold !important;
            transition: all 0.2s ease;
        }
        button[kind="primaryFormSubmit"]:hover, .stFormSubmitButton > button:hover {
            background-color: #2c1d16 !important;
            border-color: #ffffff !important;
        }
        
        /* Compact typography layout controls */
        h1, h2, h3, h4 {
            margin-top: 2px !important;
            margin-bottom: 4px !important;
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            color: #ffffff !important;
            font-weight: bold !important;
        }
        div.block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 1rem !important;
        }
        
        /* Custom Luminous Blue Horizontal Rule Partition */
        .blue-divider {
            border: 0;
            height: 1px;
            background: #00F0FF;
            margin-top: 15px;
            margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# BILINGUAL TRANSLATION MATRIX 
# =====================================================================
T_TITLE_ENG = "Readings Register"
T_TITLE_VIE = "(Nhật Ký Đọc Kinh Thánh)"

T_DATE_HDR  = "Current Date"
T_DATE_VIE  = "(Ngày Hiện Tại)"

T_PERIOD_HDR = "Period Tracking /"
T_PERIOD_VIE = "Chọn mốc thời gian"

T_TRACK_HDR = "Progress Tracking"
T_TRACK_VIE = "(Bảng Tiến Độ Đọc Kinh Thánh)"

# Content Plain IDs mapping definitions
T_USER_SEL = "User"
T_USER_VIE = "(Người đọc):"
T_CUST_NAME = "Name"
T_CUST_VIE = "(Họ và Tên):"
T_CUST_PHONE = "WhatsApp (with +)"
T_CUST_PVIE = "(Số điện thoại):"
T_DATETIME = "Date & Time"
T_DATETIME_VIE = "(Ngày & Giờ):"
T_BIBLEREF = "Bible Reference"
T_BIBLEREF_VIE = "(Sách & Chương đã đọc):"
T_CHAPTERS = "Chapters"
T_CHAPTERS_VIE = "(Số chương):"
T_GODSPOKE = "God's Message"
T_GODSPOKE_VIE = "(Suy ngẫm / Ghi chú):"
T_GODOBEY = "Obedience Step"
T_GODOBEY_VIE = "(Lời hứa / Vâng phục):"

T_SUBMIT = "Submit Entry / Gửi Nhật Ký"
T_MISSING = "Missing fields! / Vui lòng điền đầy đủ các thông tin!"
T_SAVED = "Saved! / Đã lưu thành công!"

T_CURR_MONTH  = "Current Month"
T_CURR_MONTH_VIE = "Tháng này"
T_CUST_RANGE  = "Custom Range"
T_CUST_RANGE_VIE = "Tùy chọn"
T_START       = "Start"
T_START_VIE   = "(Từ ngày):"
T_END         = "End"
T_END_VIE     = "(Đến ngày):"

T_SENDER_ID   = "Sender Identity"
T_SENDER_VIE  = "(Tên người gửi):"
T_WA_LAUNCH   = "💬 Launch WhatsApp & Pre-fill Template Text / Mở WhatsApp & Gửi Tin Nhắn"

MAP_METRIC = {
    "Chapters": "Chapters / Số Chương",
    "Sessions": "Sessions / Số Lần Đọc",
    "Days Read": "Days Read / Số Ngày Đọc",
    "Missed Days": "Missed Days / Số Ngày Chưa Đọc",
    "Reading Rate": "Reading Rate / % Số Ngày Đọc"
}

# --- GLOBAL DICTIONARY DATA ---
USER_DIRECTORY = {
    "Katelyn": "+60193763635",
    "Thoa": "+601155080892",
    "Ruth": "+60183668919",
    "Sarah": "+60168412926",
    "Tham": "+60169159217",
    "Tina": "+601121103011",
    "Hannah": "+60182499896",
    "hs": "+60122193637"
}

# Mobile Sidebar Open Hint Box Instruction Banner
st.markdown("""
    <div class="mobile-sidebar-hint">
        📱 <b>Mobile Users:</b> Tap the double arrow <b>( >> )</b> button in the top-left corner to open the Entry Form! <br>
        <span class="vn-blue">Thành viên dùng điện thoại: Nhấn dấu mũi tên <b>( >> )</b> ở góc trên cùng bên trái để mở Đơn Nhập Liệu!</span>
    </div>
""", unsafe_allow_html=True)

st.markdown(f"<h1>📚 {T_TITLE_ENG} <span style='font-size: 22px; color: #d4af37; font-weight: normal;'>{T_TITLE_VIE}</span></h1>", unsafe_allow_html=True)

# =====================================================================
# DATA STORAGE LAYER: SERVICE ACCOUNT JSON CONNECTION MANAGER
# =====================================================================
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1iPxF9ftWROX-_BbBBGKC3rkgRn5QcCIrvcbB3jVoH1g/edit?usp=sharing"
CREDENTIALS_FILE = "sheets-ai-automation-3a77cb6b83b6.json"

@st.cache_data(ttl=0)
def fetch_sheet_records():
    try:
        if "creds_json" in st.secrets:
            # Parse the direct JSON string structure
            creds = json.loads(st.secrets["creds_json"])
            
            if "private_key" in creds:
                pk = str(creds["private_key"])
                # Clean out string escape artifacts securely
                pk = pk.replace("\\n", "\n")
                creds["private_key"] = pk
        else:
            with open(CREDENTIALS_FILE, "r") as f:
                creds = json.load(f)
        
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open_by_url(GOOGLE_SHEET_URL)
        worksheet = sh.get_worksheet(0)
        records = worksheet.get_all_records()
        return pd.DataFrame(records), worksheet
    except Exception as e:
        st.error(f"Google Cloud connection failed: {e}")
        return pd.DataFrame(), None

raw_df, target_worksheet = fetch_sheet_records()

if raw_df is None or len(raw_df) == 0:
    raw_df = pd.DataFrame(columns=["Timestamp", "Name", "BibleReference", "ChaptersRead", "GodSpoke", "GodObey", "Phone"])

# --- SIDEBAR ENTRY FORM (HTML FIXED & DISCRETE ISOLATION) ---
st.sidebar.markdown(f"### 📝 Entry Form <br><span class='vn-blue' style='font-size:16px;'>Đơn Nhập Liệu</span>", unsafe_allow_html=True)

st.sidebar.markdown(f"{T_USER_SEL} <span class='vn-blue'>{T_USER_VIE}</span>", unsafe_allow_html=True)
selected_name = st.sidebar.selectbox("User Selection Box", options=list(USER_DIRECTORY.keys()) + ["Others"], label_visibility="collapsed")

custom_name = ""
custom_phone = ""
if selected_name == "Others":
    st.sidebar.markdown(f"{T_CUST_NAME} <span class='vn-blue'>{T_CUST_VIE}</span>", unsafe_allow_html=True)
    custom_name = st.sidebar.text_input("Custom Name Form Box", label_visibility="collapsed").strip()
    
    st.sidebar.markdown(f"{T_CUST_PHONE} <span class='vn-blue'>{T_CUST_PVIE}</span>", unsafe_allow_html=True)
    custom_phone = st.sidebar.text_input("Custom Phone Form Box", label_visibility="collapsed").strip()

with st.sidebar.form(key="reading_form", clear_on_submit=True):
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"{T_DATETIME} <span class='vn-blue'>{T_DATETIME_VIE}</span>", unsafe_allow_html=True)
    input_timestamp = st.text_input("Timestamp Entry Field", value=current_time_str, label_visibility="collapsed")
    
    st.markdown(f"{T_BIBLEREF} <span class='vn-blue'>{T_BIBLEREF_VIE}</span>", unsafe_allow_html=True)
    reading_ref = st.text_input("Bible Reference Entry Field", label_visibility="collapsed")
    
    st.markdown(f"{T_CHAPTERS} <span class='vn-blue'>{T_CHAPTERS_VIE}</span>", unsafe_allow_html=True)
    chapters = st.number_input("Chapters Entry Field", min_value=0, step=1, value=0, label_visibility="collapsed")
    
    st.markdown(f"{T_GODSPOKE} <span class='vn-blue'>{T_GODSPOKE_VIE}</span>", unsafe_allow_html=True)
    god_spoke = st.text_area("Reflection Notes Field", height=65, label_visibility="collapsed")
    
    st.markdown(f"{T_GODOBEY} <span class='vn-blue'>{T_GODOBEY_VIE}</span>", unsafe_allow_html=True)
    god_obey = st.text_area("Obedience Target Field", height=65, label_visibility="collapsed")
    
    submit_button = st.form_submit_button(label=T_SUBMIT)

if "last_active_user" not in st.session_state:
    st.session_state["last_active_user"] = list(USER_DIRECTORY.keys())[0]

if submit_button:
    final_name = custom_name if selected_name == "Others" else selected_name
    final_phone = custom_phone if selected_name == "Others" else USER_DIRECTORY.get(selected_name, "")
    
    if selected_name == "Others" and (not custom_name or not custom_phone):
        st.sidebar.error(T_MISSING)
    else:
        if target_worksheet is not None:
            try:
                row_to_append = [input_timestamp, final_name, reading_ref, int(chapters), god_spoke, god_obey, final_phone]
                target_worksheet.append_row(row_to_append)
                st.session_state["last_active_user"] = final_name
                st.sidebar.success(T_SAVED)
                st.cache_data.clear()
                st.rerun()
            except Exception as write_err:
                st.sidebar.error(f"Write error: {write_err}")
        else:
            st.sidebar.error("Database connection was unavailable.")

# --- MAIN CONTROLS & GRAPH ---
has_data = len(raw_df) > 0

if has_data:
    time_col = "Timestamp" if "Timestamp" in raw_df.columns else "Date"
    ref_col = "BibleReference" if "BibleReference" in raw_df.columns else "ReadingReference"
    
    raw_df["ParsedDate"] = pd.to_datetime(raw_df[time_col], format='mixed', errors='coerce').dt.date
    raw_df = raw_df.dropna(subset=["ParsedDate"])
    
    today = datetime.now().date()
    st.markdown(f"""
        <div style='margin-top: 5px; margin-bottom: 5px;'>
            <span style='font-size: 16px; font-weight: bold; color: #ffffff;'>📅 {T_DATE_HDR}</span>
            <span class='vn-blue' style='font-size: 13px;'>{T_DATE_VIE} : </span>
            <span style='font-size: 24px; font-weight: bold; color: #00F0FF; margin-left: 5px;'>{today.strftime('%d-%m-%Y')}</span>
        </div>
    """, unsafe_allow_html=True)
    
    hdr_col, opt_col = st.columns([2, 3])
    with hdr_col:
        st.markdown(f"<div style='padding-top:6px;'><span style='font-size: 16px; font-weight: bold; color: #ffffff;'>⏱️ {T_PERIOD_HDR}</span> <span class='vn-blue' style='font-size: 13px;'>{T_PERIOD_VIE}</span></div>", unsafe_allow_html=True)
    with opt_col:
        filter_mode = st.radio("Period Tracking Options Mode", options=[f"{T_CURR_MONTH} / {T_CURR_MONTH_VIE}", f"{T_CUST_RANGE} / {T_CUST_RANGE_VIE}"], horizontal=True, label_visibility="collapsed")
        
    if f"{T_CUST_RANGE} / {T_CUST_RANGE_VIE}" in filter_mode:
        col1, col2 = st.columns(2)
        with col1: 
            st.markdown(f"{T_START} <span class='vn-blue' style='font-size:12px;'>{T_START_VIE}</span>", unsafe_allow_html=True)
            start_filter = st.date_input("Start Custom Date Entry", today.replace(day=1), label_visibility="collapsed")
        with col2: 
            st.markdown(f"{T_END} <span class='vn-blue' style='font-size:12px;'>{T_END_VIE}</span>", unsafe_allow_html=True)
            end_filter = st.date_input("End Custom Date Entry", today, label_visibility="collapsed")
    else:
        start_filter = today.replace(day=1)
        end_filter = today
            
    st.markdown("<hr class='blue-divider'>", unsafe_allow_html=True)
    filtered_df = raw_df[(raw_df["ParsedDate"] >= start_filter) & (raw_df["ParsedDate"] <= end_filter)]
    
    if len(filtered_df) > 0:
        total_days_in_period = (end_filter - start_filter).days + 1
        all_users = filtered_df["Name"].dropna().unique()
        calculated_records = []
        
        for user in all_users:
            user_df = filtered_df[filtered_df["Name"] == user]
            ch_count = pd.to_numeric(user_df["ChaptersRead"], errors='coerce').sum()
            sess_count = len(user_df)
            days_read_count = user_df["ParsedDate"].nunique()
            missed_days_count = max(0, total_days_in_period - days_read_count)
            
            pct_val = int(round((sess_count / total_days_in_period) * 100, 0)) if total_days_in_period > 0 else 0
            pct_text = f"{pct_val}%"
            
            calculated_records.append({
                "Name": user, "Chapters": ch_count, "Sessions": sess_count, "Days Read": days_read_count, "Missed Days": missed_days_count, "Reading Rate": 0, "PctText": pct_text  
            })
            
        calc_df = pd.DataFrame(calculated_records)
        st.markdown(f"<h2>📊 <span style='font-size: 24px; color:#ffffff;'>{T_TRACK_HDR}</span> <span class='vn-blue' style='font-size: 24px;'>{T_TRACK_VIE}</span></h2>", unsafe_allow_html=True)
        
        melted_df = calc_df.melt(id_vars=["Name", "PctText"], value_vars=["Chapters", "Sessions", "Days Read", "Missed Days", "Reading Rate"], var_name="Metric", value_name="Count")
        melted_df["Metric Display"] = melted_df["Metric"].map(MAP_METRIC)
        
        fig = px.bar(
            melted_df, y="Name", x="Count", color="Metric Display", orientation='h', barmode="stack", text="Count",
            color_discrete_map={
                MAP_METRIC["Chapters"]: "#A0C4FF", MAP_METRIC["Sessions"]: "#B9FBC0", MAP_METRIC["Days Read"]: "#FDE2E4", MAP_METRIC["Missed Days"]: "#FFD6A5", MAP_METRIC["Reading Rate"]: "#00F0FF" 
            }
        )
        
        for idx, row in calc_df.iterrows():
            total_bar_length = row["Chapters"] + row["Sessions"] + row["Days Read"] + row["Missed Days"]
            fig.add_annotation(
                x=total_bar_length, y=row["Name"], text=row["PctText"], showarrow=False, xshift=22, font=dict(color="#00F0FF", size=24, weight="bold")
            )
        
        fig.update_layout(
            margin=dict(l=10, r=60, t=10, b=10), paper_bgcolor='#1e120b', plot_bgcolor='#1e120b', font=dict(color="#ffffff", size=13), 
            xaxis=dict(
                title=dict(text="Count / Số Lượng", font=dict(color="#ffffff", size=14)), tickfont=dict(color="#ffffff", size=12), gridcolor="#422d22",
                showline=True, linewidth=1, linecolor='#00F0FF'
            ),
            yaxis=dict(
                title=dict(text="Users / Người Đọc", font=dict(color="#ffffff", size=14)), tickfont=dict(color="#ffffff", size=13),
                showline=True, linewidth=1, linecolor='#00F0FF'
            ),
            legend=dict(
                orientation="h", y=-0.28, x=0.5, xanchor="center", title=dict(text="Metrics / Tiêu Chí:", font=dict(color="#ffffff", size=12)), font=dict(color="#ffffff", size=12) 
            )
        )
        
        fig.update_layout(legend_title_text="Metrics / Tiêu Chí | <span style='color:#00F0FF;'>■</span> Reading Rate / % Số Ngày Đọc")
        fig.update_traces(textposition="inside", insidetextanchor="middle", textfont=dict(color="#120a06", size=12, weight="bold"))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        
        # --- WHATSAPP UTILITY EXPORT SUITE ---
        st.markdown(f"### 📲 WhatsApp Direct Share <br><span class='vn-blue' style='font-size:16px;'>Chia Sẻ Trực Tiếp Qua WhatsApp</span>", unsafe_allow_html=True)
        
        st.markdown(f"{T_SENDER_ID} <span class='vn-blue'>{T_SENDER_VIE}</span>", unsafe_allow_html=True)
        default_index = list(all_users).index(st.session_state["last_active_user"]) if st.session_state["last_active_user"] in all_users else 0
        share_user = st.selectbox("Identity Selection Box Link", options=all_users, index=default_index, label_visibility="collapsed")
        
        user_stats = calc_df[calc_df["Name"] == share_user]
        if not user_stats.empty:
            row = user_stats.iloc[0]
            summary_text = f"📖 *Bible Reading Update ({start_filter} to {end_filter})*\n👤 Member: {share_user}\n📊 Chapters: {row['Chapters']} | Sessions: {row['Sessions']}\n✨ Days Read: {row['Days Read']} | Missed: {row['Missed Days']}"
            user_log_match = raw_df[raw_df["Name"] == share_user].dropna(subset=["Phone"])
            phone_num = str(user_log_match.iloc[-1]["Phone"]).strip() if not user_log_match.empty and str(user_log_match.iloc[-1]["Phone"]).strip() != "" else USER_DIRECTORY.get(share_user, "")
            phone_num = phone_num.replace(" ", "").replace("-", "")
            whatsapp_url = f"https://wa.me/{phone_num}?text={urllib.parse.quote(summary_text)}"
            
            st.markdown(f"""
            <table style="width:100%; border-collapse: collapse; background-color: #2c1d16; border: 1px solid #422d22; font-size:13px; margin-bottom:10px;">
                <tr style="background-color: #422d22; color: #ffffff; font-weight: bold;">
                    <th style="padding: 6px; border: 1px solid #422d22; width: 45%;">Step 1: Save Chart (Bước 1: Lưu Biểu Đồ)</th>
                    <th style="padding: 6px; border: 1px solid #422d22; width: 55%;">Step 2: Upload to WhatsApp (Bước 2: Gửi Qua WhatsApp)</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #422d22; color: #f5f0eb; vertical-align: top;">
                        Hover over graph menu bar. Click the 📷 <b>Camera Icon</b> to instantly download chart image file inside your system <b>Downloads</b> folder.
                    </td>
                    <td style="padding: 8px; border: 1px solid #422d22; color: #f5f0eb; vertical-align: top;">
                        Press green link block below. In your active WhatsApp dialogue popup, click the <b>Paperclip (+) attachment icon</b>, choose saved chart file, then hit Send.
                    </td>
                </tr>
            </table>
            """, unsafe_allow_html=True)
            if phone_num:
                st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="padding:10px; background-color:#7c5c43; color:white; border:none; border-radius:4px; cursor:pointer; font-weight:bold; font-size:14px; width:100%;">{T_WA_LAUNCH}</button></a>', unsafe_allow_html=True)
        
        # --- REFLECTION JOURNALS ---
        st.markdown(f"### 📋 Shared Reflection Journal <br><span class='vn-blue' style='font-size:16px;'>Nhật Ký Suy Ngẫm Chung</span>", unsafe_allow_html=True)
        display_df = filtered_df.copy()[[time_col, "Name", ref_col, "ChaptersRead", "GodSpoke", "GodObey"]]
        display_df.columns = ["Timestamp", "Name", "Bible Reference", "Chapters", "God's Message", "Obedience Step"]
        st.dataframe(display_df.sort_values(by="Timestamp", ascending=False), use_container_width=True, hide_index=True)
