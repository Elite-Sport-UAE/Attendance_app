import streamlit as st
import pandas as pd
import os
import re
from datetime import date, datetime, timezone


if not st.session_state.get("is_authed", False):
    st.warning("Please sign in on the Home page.")
    st.stop()

logged_in_email = st.session_state.get("user_email", "")

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------

st.set_page_config(page_title="Attendance Portal", layout="wide")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stSidebarNav"] {display: none !important;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>

/* Compact, consistent buttons */
div.stButton > button,
a.stLinkButton > a {
    height: 34px !important;
    padding: 0 14px !important;
    font-size: 0.85rem !important;
    border-radius: 8px !important;
    width: 160px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Prevent link button container from stretching */
a.stLinkButton {
    width: auto !important;
}

/* Default neutral buttons */
div.stButton > button,
div.stLinkButton > a {
    background: white !important;
    color: #111827 !important;
    border: 1px solid #D1D5DB !important;
}

/* Gold Logout button */
.logout-btn div.stButton > button {
    background-color: #D4AF37 !important;
    color: #ffffff !important;
    border: none !important;
}

.logout-btn div.stButton > button:hover {
    background-color: #c59f2f !important;
    color: #ffffff !important;
}

/* Force button wrapper to align right */
.logout-wrap {
    display: flex;
    justify-content: flex-end;
    width: 100%;
}
            
/* Save Attendance fixed center */
.center-save {
    position: fixed;
    bottom: 80px;        /* distance from bottom */
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
}       

/* Data Management: force Input Data and Refresh Lookup to identical size */
div[data-testid="stExpander"] div.stLinkButton > a,
div[data-testid="stExpander"] div.stButton > button {
    width: 160px !important;
    min-width: 160px !important;
    height: 36px !important;

    padding: 0 16px !important;
    line-height: 36px !important;

    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;

    box-sizing: border-box !important;
    border-radius: 8px !important;
    border: 1px solid #D1D5DB !important;

    font-size: 0.85rem !important;
    font-weight: 500 !important;

    text-decoration: none !important;
}

            
</style>
""", unsafe_allow_html=True)


# HEADERS

header_left, header_mid, header_right = st.columns([1, 12, 2])

with header_left:
    st.image("assets/esuae_logo.png", width=90)

with header_mid:
    st.markdown(
        """
        <div style="padding-top:12px;">
            <div style="font-size:34px; font-weight:700; color:#111827;">
                ESUAE Attendance Portal
            </div>
            <div style="font-size:15px; color:#6B7280;">
                Elite Sport UAE • Training Session Attendance
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with header_right:

    full_email = st.session_state.get("user_email", "User")

    # Extract username before @
    display_name = full_email.split("@")[0] if "@" in full_email else full_email
    display_name = display_name.replace(".", " ").title()

    # Right align using Streamlit columns
    spacer, content = st.columns([1, 4])

    with content:
        st.markdown(
            f"""
            <div style="text-align:right; padding-top:18px; padding-right:20px;">
                <div style="font-size:13px; color:#6B7280;">Logged in</div>
                <div style="font-size:15px; font-weight:600; color:#111827;">
                    {display_name}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        # Button directly under name
        st.markdown("<div style='text-align:right; padding-right:20px;'>", unsafe_allow_html=True)

        if st.button("Logout", key="logout_btn"):
            for k in ["is_authed", "attendance_data", "last_selected_sport", "user_code"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.switch_page("Home.py")

        st.markdown("</div>", unsafe_allow_html=True)


# -------------------------------------------------------
# PATHS
# -------------------------------------------------------

lookup_excel_path = r"C:\Users\AishwarDhawan\General Authority of sports\All Things Data - ESUAE Attendance\Attendance\Athlete list.xlsx"
sessions_dir = r"C:\Users\AishwarDhawan\General Authority of sports\All Things Data - ESUAE Attendance\Attendance\sessions"
os.makedirs(sessions_dir, exist_ok=True)

# -------------------------------------------------------
# DATA MANAGEMENT
# -------------------------------------------------------

with st.expander("Data Management", expanded=False):
    sharepoint_excel_url = "https://teamuaesports.sharepoint.com/:x:/s/AllThingsData/IQAHwcMkC8GaS6_3-8vQ5VfoAXKVAEPAmNp491lt0EjCfh8?e=whmmvE"

    b1, b2, _ = st.columns([1, 1, 8])

    with b1:
        st.link_button("Input Data", sharepoint_excel_url)

    with b2:
        if st.button("Refresh Lookup", key="refresh_lookup_btn"):
            st.cache_data.clear()
            st.rerun()


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------

def safe_filename(text: str) -> str:
    text = str(text).strip()
    text = re.sub(r"[^\w\s\-()]", "", text)  # remove special characters
    text = re.sub(r"\s+", "_", text)         # spaces -> underscore
    return text[:60]                          # keep it short

def build_session_id(session_date, selected_sport, coach_name, training_type, location, session_duration):
    # Unique enough: date + time + key fields
    ts = datetime.now().strftime("%H%M%S")
    return f"{session_date}__{safe_filename(selected_sport)}__{safe_filename(coach_name)}__{safe_filename(training_type)}__{ts}"

def build_attendance_df(session_id, session_date, selected_sport, coach_name, training_type, location, session_duration, attendance_dict, logged_in_email):
    duration_minutes = int(str(session_duration).split()[0])
    saved_at_utc = datetime.now(timezone.utc).isoformat()

    rows = []
    for athlete_name, att in attendance_dict.items():
        is_present = att.get("present", True)
        status = "Present" if is_present else "Absent"

        reason = "" if is_present else (att.get("reason") or "")
        if reason == "Select reason":
            reason = ""

        rows.append({
            "SessionId": session_id,
            "SessionDate": str(session_date),
            "Sport": selected_sport,
            "CoachName": coach_name,
            "TrainingType": training_type,
            "Location": location,
            "DurationMinutes": duration_minutes,
            "AthleteName": athlete_name,
            "Status": status,
            "Reason": reason,
            "SavedAtUtc": saved_at_utc,
            "LoggedInEmail": logged_in_email

        })

    return pd.DataFrame(rows)

# -------------------------------------------------------
# LOAD LOOKUP EXCEL FILE
# -------------------------------------------------------

@st.cache_data
def load_lookup_data(path):
    athlete_df = pd.read_excel(path, sheet_name="athlete_names")
    coach_df = pd.read_excel(path, sheet_name="coach_names")
    sport_df = pd.read_excel(path, sheet_name="sport")
    training_type_df = pd.read_excel(path, sheet_name="training_type")
    location_df = pd.read_excel(path, sheet_name="location")
    reason_df = pd.read_excel(path, sheet_name="reason_absence")

    return athlete_df, coach_df, sport_df, training_type_df, location_df, reason_df


try:
    athlete_df, coach_df, sport_df, training_type_df, location_df, reason_df = load_lookup_data(lookup_excel_path)
    st.toast("Lookup data loaded", icon="✅")
except Exception as e:
    st.error(f"Error loading Excel file: {e}")
    st.stop()


# -------------------------------------------------------
# CLEAN COLUMN NAMES
# -------------------------------------------------------

athlete_df.columns = athlete_df.columns.str.strip()
coach_df.columns = coach_df.columns.str.strip()
sport_df.columns = sport_df.columns.str.strip()
training_type_df.columns = training_type_df.columns.str.strip()
location_df.columns = location_df.columns.str.strip()
reason_df.columns = reason_df.columns.str.strip()

# -------------------------------------------------------
# DROPDOWN LISTS (assumes values in first column)
# -------------------------------------------------------

sports_list = sport_df.iloc[:, 0].dropna().astype(str).sort_values().unique().tolist()
coach_list = coach_df.iloc[:, 0].dropna().astype(str).sort_values().unique().tolist()
training_type_list = training_type_df.iloc[:, 0].dropna().astype(str).sort_values().unique().tolist()
location_list = location_df.iloc[:, 0].dropna().astype(str).sort_values().unique().tolist()
reason_absence_list = reason_df.iloc[:, 0].dropna().astype(str).sort_values().unique().tolist()

# -------------------------------------------------------
# SESSION DETAILS (UI)
# -------------------------------------------------------

st.subheader("Session Details")

left, right = st.columns(2)

with left:
    session_date = st.date_input("Date", value=date.today())
    coach_name = st.selectbox("Coach Name", options=["Select coach"] + coach_list, index=0)
    location = st.selectbox("Location", options=["Select location"] + location_list, index=0)

with right:
    selected_sport = st.selectbox("Sport", options=["Select sport"] + sports_list, index=0)
    training_type = st.selectbox("Training Type", options=["Select type"] + training_type_list, index=0)
    session_duration = st.selectbox("Session Duration", options=["30 minutes", "45 minutes", "60 minutes", "75 minutes", "90 minutes", "120 minutes"], index=2)

# Reset attendance if sport changes
if "last_selected_sport" not in st.session_state:
    st.session_state.last_selected_sport = selected_sport

if selected_sport != st.session_state.last_selected_sport:
    st.session_state.attendance_data = {}
    st.session_state.last_selected_sport = selected_sport

st.divider()

# Ensure session state exists
if "attendance_data" not in st.session_state:
    st.session_state.attendance_data = {}

# -------------------------------------------------------
# ATTENDANCE SECTION
# -------------------------------------------------------

filtered_athletes = []

if selected_sport != "Select sport":

    st.subheader("Mark Attendance")

    # Filter athletes by selected sport
    filtered_athletes = athlete_df[athlete_df["Sport"] == selected_sport]["Athlete Name"].dropna().tolist()

    # Search
    search_query = st.text_input("Search athletes")

    if search_query:
        filtered_athletes = [a for a in filtered_athletes if search_query.lower() in a.lower()]

    present_count = 0

    for athlete in filtered_athletes:

        # Default state
        if athlete not in st.session_state.attendance_data:
            st.session_state.attendance_data[athlete] = {"present": True, "reason": None}

        col1, col2 = st.columns([4, 2])

        with col1:
            present = st.checkbox(
                athlete,
                value=st.session_state.attendance_data[athlete]["present"],
                key=f"{athlete}_present"
            )

        st.session_state.attendance_data[athlete]["present"] = present

        if present:
            present_count += 1
            st.session_state.attendance_data[athlete]["reason"] = None
        else:
            with col2:
                reason = st.selectbox(
                    "Reason for absence",
                    options=["Select reason"] + reason_absence_list,
                    key=f"{athlete}_reason"
                )
            st.session_state.attendance_data[athlete]["reason"] = reason

    st.write(f"{present_count} / {len(filtered_athletes)} athletes present")

st.divider()

# -------------------------------------------------------
# SAVE SESSION (one file per session)
# -------------------------------------------------------

ready_to_save = (
    selected_sport != "Select sport"
    and coach_name != "Select coach"
    and training_type != "Select type"
    and location != "Select location"
    and len(filtered_athletes) > 0
)

st.markdown("<div class='center-save'>", unsafe_allow_html=True)

save_clicked = st.button(
    "Save Attendance",
    disabled=not ready_to_save,
    key="save_attendance_btn"
)

st.markdown("</div>", unsafe_allow_html=True)


if save_clicked:

    # Only save athletes in current filtered view
    attendance_to_save = {
        a: st.session_state.attendance_data[a]
        for a in filtered_athletes
        if a in st.session_state.attendance_data
    }

    try:
        session_id = build_session_id(
            session_date, selected_sport, coach_name, training_type, location, session_duration
        )

        df_session = build_attendance_df(
        session_id=session_id,
        session_date=session_date,
        selected_sport=selected_sport,
        coach_name=coach_name,
        training_type=training_type,
        location=location,
        session_duration=session_duration,
        attendance_dict=attendance_to_save,
        logged_in_email=logged_in_email
    )


        file_name = f"{session_id}__{int(str(session_duration).split()[0])}min.xlsx"
        file_path = os.path.join(sessions_dir, file_name)

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df_session.to_excel(writer, sheet_name="attendance", index=False)

        st.success(f"Saved session file: {file_name}")

        # Reset after save
        st.session_state.attendance_data = {}

    except PermissionError:
        st.error("Permission denied writing session file. Check OneDrive sync or folder permissions.")
    except Exception as e:
        st.error(f"Save failed: {e}")
