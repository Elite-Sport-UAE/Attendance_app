import streamlit as st
import pandas as pd
import os
import re
from datetime import date, datetime, timezone

if not st.session_state.get("is_authed", False):
    st.warning("Please enter the access code on the Home page.")
    st.stop()


# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------

st.set_page_config(page_title="ESUAE Attendance Register", layout="wide")

# -------------------------------------------------------
# HEADER
# -------------------------------------------------------

header_left, header_right = st.columns([1, 5])

with header_left:
    st.image("assets/esuae_logo.png", width=90)

with header_right:
    st.markdown(
        """
        <div style="padding-top:12px;">
            <div style="font-size:34px; font-weight:700; color:#111827;">
                ESUAE Attendance Register
            </div>
            <div style="font-size:15px; color:#6B7280;">
                Elite Sport UAE • Training Session Management
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("")


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

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Open Athlete List Excel File"):
            os.startfile(lookup_excel_path)

    with col2:
        if st.button("Refresh Lookup Data"):
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

def build_attendance_df(session_id, session_date, selected_sport, coach_name, training_type, location, session_duration, attendance_dict):
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
            "SavedAtUtc": saved_at_utc
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
    session_duration = st.selectbox("Session Duration", options=["60 minutes", "75 minutes", "90 minutes", "120 minutes"], index=2)

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

st.markdown("")

save_col = st.columns([1, 2, 1])[1]

with save_col:
    save_clicked = st.button(
        "Save Attendance",
        disabled=not ready_to_save,
        use_container_width=True
    )

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
            attendance_dict=attendance_to_save
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
