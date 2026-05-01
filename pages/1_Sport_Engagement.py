import streamlit as st
import pandas as pd
import re
import requests
from io import BytesIO
from datetime import date, datetime, timezone

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------

st.set_page_config(page_title="Sport Engagement Portal", layout="wide")

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

a.stLinkButton {
    width: auto !important;
}

div.stButton > button,
div.stLinkButton > a {
    background: #43AA8B !important;
    color: white !important;
    border: 1px solid #D1D5DB !important;
}

/* Logout button gold */
.st-key-logout_btn div.stButton > button,
.st-key-logout_btn button {
    background: #C8A44D !important;
    background-color: #C8A44D !important;
    color: white !important;
    border: none !important;
}

.center-save {
    position: fixed;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
}

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
/* Force all widget labels bold */
div[data-testid="stWidgetLabel"] * {
    font-weight: 700 !important;
}

/* Extra fallback for current Streamlit label structure */
label,
label *,
[data-testid="stMarkdownContainer"] p {
    font-weight: 700 !important;
}

</style>
""", unsafe_allow_html=True)

# st.write("Secrets keys:", list(st.secrets.keys()))
# get access token for Microsoft Graph API using client credentials flow
@st.cache_data(ttl=300)
def get_access_token():
    tenant = st.secrets["TENANT_ID"]
    client = st.secrets["CLIENT_ID"]
    secret = st.secrets["CLIENT_SECRET"]

    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    data = {
        "client_id": client,
        "client_secret": secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    r = requests.post(url, data=data)
    r.raise_for_status()
    return r.json()["access_token"]


@st.cache_data(ttl=300)
def get_lookup_workbook_bytes_graph():
    token = get_access_token()
    site_id = get_sharepoint_site_id()
    path = st.secrets["LOOKUP_FILE_PATH"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    file_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:{path}:/content"
    file_resp = requests.get(file_url, headers=headers)
    file_resp.raise_for_status()

    content_type = file_resp.headers.get("Content-Type", "")
    if "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" not in content_type:
        raise ValueError(
            f"Downloaded content is not an Excel file. Content-Type: {content_type}. "
            f"Check LOOKUP_FILE_PATH in secrets.toml."
        )

    return file_resp.content

@st.cache_data(ttl=300)
def get_sharepoint_site_id():
    token = get_access_token()

    site = st.secrets["SHAREPOINT_SITE"]
    site_name = st.secrets["SHAREPOINT_SITE_NAME"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    site_url = f"https://graph.microsoft.com/v1.0/sites/{site}:/sites/{site_name}"
    site_resp = requests.get(site_url, headers=headers)
    site_resp.raise_for_status()

    return site_resp.json()["id"]

def save_session_file_graph(file_name: str, file_bytes: bytes) -> None:
    token = get_access_token()
    site_id = get_sharepoint_site_id()
    folder_path = st.secrets["SESSIONS_FOLDER"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }

    upload_url = (
        f"https://graph.microsoft.com/v1.0/sites/{site_id}"
        f"/drive/root:{folder_path}/{file_name}:/content"
    )

    upload_resp = requests.put(upload_url, headers=headers, data=file_bytes)
    upload_resp.raise_for_status()

# -------------------------------------------------------
# AUTH CHECK
# -------------------------------------------------------
if "is_authed" not in st.session_state:
    st.session_state["is_authed"] = False

if not st.session_state.get("is_authed", False):
    st.switch_page("Home.py")

logged_in_email = st.session_state.get("user_email", "")


# -------------------------------------------------------
# HEADER
# -------------------------------------------------------

header_left, header_mid, header_right = st.columns([1, 12, 2])

with header_left:
    st.image("assets/esuae_logo.png", width=90)

with header_mid:
    st.markdown(
        """
        <div style="padding-top:12px;">
            <div style="font-size:34px; font-weight:700; color:#111827;">
                ESUAE Sport Engagement Portal
            </div>
            <div style="font-size:15px; color:#6B7280;">
                Elite Sport UAE • Training Engagement
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with header_right:
    full_email = st.session_state.get("user_email", "User")
    display_name = full_email.split("@")[0] if "@" in full_email else full_email
    display_name = display_name.replace(".", " ").title()

    st.markdown(
        f"""
        <div style="text-align:right; padding-top:18px; padding-right:30px;">
            <div style="font-size:13px; color:#6B7280;">Logged in</div>
            <div style="font-size:15px; font-weight:600; color:#111827;">
                {display_name}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    logout_spacer, logout_col = st.columns([1, 2])

    with logout_col:
        if st.button("Logout", key="logout_btn"):
            st.session_state.clear()
            st.switch_page("Home.py")

# -------------------------------------------------------

SHAREPOINT_ATHLETE_LIST_URL = "https://teamuaesports.sharepoint.com/:x:/r/sites/AllThingsData/_layouts/15/Doc.aspx?sourcedoc=%7B24C3C107-C10B-4B9A-AFF7-FBCBD0E557E8%7D&file=Athlete%20list.xlsx&action=default&mobileredirect=true"

# # SHAREPOINT LINKS
# -------------------------------------------------------


# lookup_excel_path = r"C:\Users\AishwarDhawan\General Authority of sports\All Things Data - ESUAE Attendance\Attendance\Athlete list.xlsx"
# sessions_dir = r"C:\Users\AishwarDhawan\General Authority of sports\All Things Data - ESUAE Attendance\Attendance\sessions"
# os.makedirs(sessions_dir, exist_ok=True)

# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------

def safe_filename(text: str) -> str:
    text = str(text).strip()
    text = re.sub(r"[^\w\s\-()]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:60]

def build_session_id(session_date, selected_sport, coach_name, training_type):
    ts = datetime.now().strftime("%H%M%S")
    return f"{session_date}__{safe_filename(selected_sport)}__{safe_filename(coach_name)}__{safe_filename(training_type)}__{ts}"

def build_attendance_df(session_id, session_date, selected_sport, coach_name,
                        training_type, location, session_duration,
                        attendance_dict, logged_in_email, athlete_sport_map):

    duration_minutes = int(str(session_duration).split()[0])
    saved_at_utc = datetime.now(timezone.utc).isoformat()

    rows = []
    for athlete_name, att in attendance_dict.items():

        response = att.get("response") or ""

        if response in ["", None, "Select response"]:
            status = ""
        else:
            status = response

        athlete_sport = athlete_sport_map.get(athlete_name, selected_sport)

        rows.append({
            "SessionId": session_id,
            "SessionDate": str(session_date),
            "Sport": selected_sport,
            "AthleteSport": athlete_sport,
            "CoachName": coach_name,
            "TrainingType": training_type,
            "Location": location,
            "DurationMinutes": duration_minutes,
            "AthleteName": athlete_name,
            "Status": status,
            "Reason": "",
            "SavedAtUtc": saved_at_utc,
            "LoggedInEmail": logged_in_email
        })

    return pd.DataFrame(rows)

# -------------------------------------------------------
# LOAD LOOKUP
# -------------------------------------------------------

@st.cache_data(ttl=300)
def load_lookup_data(file_bytes: bytes):
    athlete_df = pd.read_excel(BytesIO(file_bytes), sheet_name="athlete_names", engine="openpyxl")
    coach_df = pd.read_excel(BytesIO(file_bytes), sheet_name="coach_names", engine="openpyxl")
    sport_df = pd.read_excel(BytesIO(file_bytes), sheet_name="sport", engine="openpyxl")
    training_type_df = pd.read_excel(BytesIO(file_bytes), sheet_name="training_type", engine="openpyxl")
    location_df = pd.read_excel(BytesIO(file_bytes), sheet_name="location", engine="openpyxl")
    reason_df = pd.read_excel(BytesIO(file_bytes), sheet_name="reason_absence", engine="openpyxl")
    return athlete_df, coach_df, sport_df, training_type_df, location_df, reason_df

try:
    lookup_file_bytes = get_lookup_workbook_bytes_graph()
    athlete_df, coach_df, sport_df, training_type_df, location_df, reason_df = load_lookup_data(lookup_file_bytes)
except Exception as e:
    st.error(f"Error loading Excel file: {e}")
    st.stop()
# -------------------------------------------------------
# Athlete → Sport mapping (for mixed sport sessions)
# -------------------------------------------------------

athlete_sport_map = (
    athlete_df[["Athlete Name", "Sport"]]
    .dropna(subset=["Athlete Name"])
    .drop_duplicates(subset=["Athlete Name"])
    .set_index("Athlete Name")["Sport"]
    .to_dict()
)

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

st.markdown("### Data Input & Reporting")

st.markdown("<br>", unsafe_allow_html=True)

action_col1, action_col2, action_col3, action_col4 = st.columns([2, 2, 2, 6])

with action_col1:
    st.link_button("Update Athlete List", SHAREPOINT_ATHLETE_LIST_URL)

with action_col2:
    if st.button("Refresh Data"):
        get_access_token.clear()
        get_sharepoint_site_id.clear()
        get_lookup_workbook_bytes_graph.clear()
        load_lookup_data.clear()
        st.rerun()

with action_col3:
    st.link_button(
        "Sport Engagement Report",
        "https://app.powerbi.com/groups/9df28666-ff86-42f8-ad40-3a7acea422af/reports/ab72da67-453f-40c9-814f-18972ae1fcba/5a1942d42da0360e2094?experience=power-bi"
    )

st.markdown("<br>", unsafe_allow_html=True)
# -------------------------------------------------------
# CLEAN COLUMNS
# -------------------------------------------------------

for df in [athlete_df, coach_df, sport_df, training_type_df, location_df, reason_df]:
    df.columns = df.columns.str.strip()

# -------------------------------------------------------
# DROPDOWN LISTS
# -------------------------------------------------------

sports_list = sport_df.iloc[:, 0].dropna().astype(str).sort_values().unique().tolist()
coach_list = coach_df.iloc[:, 0].dropna().astype(str).sort_values().unique().tolist()
training_type_list = training_type_df.iloc[:, 0].dropna().astype(str).sort_values().unique().tolist()
location_list = location_df.iloc[:, 0].dropna().astype(str).sort_values().unique().tolist()
reason_absence_list = reason_df.iloc[:, 0].dropna().astype(str).unique().tolist()

# -------------------------------------------------------
# SESSION DETAILS
# -------------------------------------------------------

st.subheader("Session Details")
st.markdown("<br>", unsafe_allow_html=True)


left, right = st.columns(2)

with left:
    session_date = st.date_input("Date", value=date.today())
    coach_name = st.selectbox("Coach Name", ["Select coach"] + coach_list)
    location = st.selectbox("Location", ["Select location"] + location_list)

with right:
    selected_sport = st.selectbox("Sport", ["Select sport"] + sports_list)
    training_type = st.selectbox("Training Type", ["Select type"] + training_type_list)
    session_duration = st.selectbox("Session Duration",
                                    ["0 minutes","30 minutes", "45 minutes", "60 minutes",
                                     "75 minutes", "90 minutes", "120 minutes"],
                                    index=2)
# ATTENDANCE
# -------------------------------------------------------

if "attendance_data" not in st.session_state:
    st.session_state.attendance_data = {}

if "extra_athletes" not in st.session_state:
    st.session_state.extra_athletes = []

if "last_selected_sport" not in st.session_state:
    st.session_state.last_selected_sport = None

filtered_athletes = []

if selected_sport != "Select sport":

    # Reset extra athletes when sport changes
    if st.session_state.last_selected_sport != selected_sport:
        st.session_state.extra_athletes = []
        st.session_state.last_selected_sport = selected_sport

    st.subheader("Select Athlete Status & Reason for Absence")

    sport_athletes = athlete_df[
        athlete_df["Sport"] == selected_sport
    ]["Athlete Name"].dropna().astype(str).tolist()

    all_athletes_list = sorted(
        athlete_df["Athlete Name"].dropna().astype(str).unique().tolist()
    )

    available_extra_athletes = [
        a for a in all_athletes_list
        if a not in sport_athletes and a not in st.session_state.extra_athletes
    ]

    add_col1, add_col2 = st.columns([4, 2])

    with add_col1:
        extra_athlete = st.selectbox(
            "Add athlete from full list",
            ["Select athlete"] + available_extra_athletes,
            key="extra_athlete_select"
        )

    with add_col2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("Add Athlete", key="add_extra_athlete"):
            if extra_athlete != "Select athlete":
                st.session_state.extra_athletes.append(extra_athlete)
                st.rerun()

    if st.session_state.extra_athletes:
        st.markdown("**Added athletes**")
        for athlete in st.session_state.extra_athletes:
            col_a, col_b = st.columns([5, 1])
            with col_a:
                st.write(athlete)
            with col_b:
                if st.button("Remove", key=f"remove_{athlete}"):
                    st.session_state.extra_athletes.remove(athlete)
                    st.rerun()

    filtered_athletes = sport_athletes.copy()

    for a in st.session_state.extra_athletes:
        if a not in filtered_athletes:
            filtered_athletes.append(a)

    search_query = st.text_input("Search athletes")

    if search_query:
        filtered_athletes = [
            a for a in filtered_athletes
            if search_query.lower() in a.lower()
        ]

    selected_count = 0

    for athlete in filtered_athletes:

        if athlete not in st.session_state.attendance_data:
            st.session_state.attendance_data[athlete] = {"response": None}

        col1, col2 = st.columns([4, 2])

        with col1:
            st.markdown(f"**{athlete}**")

        with col2:
            response_options = ["Select response"] + reason_absence_list
            saved_response = st.session_state.attendance_data[athlete]["response"]

            response = st.selectbox(
                "Attendance Response",
                response_options,
                index=response_options.index(saved_response) if saved_response in response_options else 0,
                key=f"{athlete}_response",
                label_visibility="collapsed"
            )

        st.session_state.attendance_data[athlete]["response"] = (
            None if response == "Select response" else response
        )

        if response != "Select response":
            selected_count += 1

    st.write(f"{selected_count} / {len(filtered_athletes)} athletes updated")

# SAVE
# -------------------------------------------------------
all_answered = all(
    st.session_state.attendance_data[a].get("response") not in [None, "", "Select response"]
    for a in filtered_athletes
)

missing_fields = []

if selected_sport == "Select sport":
    missing_fields.append("Sport")

if coach_name == "Select coach":
    missing_fields.append("Coach")

if training_type == "Select type":
    missing_fields.append("Training Type")

if location == "Select location":
    missing_fields.append("Location")

if len(filtered_athletes) == 0:
    missing_fields.append("Athletes")

if missing_fields:
    st.error(
        "Please complete required fields: "
        + ", ".join(missing_fields)
    )

ready_to_save = (
    selected_sport != "Select sport"
    and coach_name != "Select coach"
    and training_type != "Select type"
    and location != "Select location"
    and len(filtered_athletes) > 0
    and all_answered
)

st.markdown("<div class='center-save'>", unsafe_allow_html=True)

save_clicked = st.button("Save Session")

st.markdown("</div>", unsafe_allow_html=True)

if save_clicked:

    if missing_fields:
        st.error("Please complete required fields: " + ", ".join(missing_fields))

    else:
        attendance_to_save = {
            a: st.session_state.attendance_data[a]
            for a in filtered_athletes
        }

        try:
            session_id = build_session_id(
                session_date, selected_sport, coach_name, training_type
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
                logged_in_email=logged_in_email,
                athlete_sport_map=athlete_sport_map
            )

            file_name = f"{session_id}.xlsx"
            output = BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_session.to_excel(writer, sheet_name="attendance", index=False)

            save_session_file_graph(file_name, output.getvalue())
            st.success(f"Saved session file: {file_name}")
            st.session_state.attendance_data = {}

        except Exception as e:
            st.error(f"Save failed: {e}")
