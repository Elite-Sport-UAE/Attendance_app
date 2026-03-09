import streamlit as st

st.set_page_config(page_title="ESUAE Attendance", layout="wide")

st.markdown("""
<style>
/* Hide Streamlit chrome */
[data-testid="stSidebar"], header {display:none;}
.block-container {padding:0 !important; max-width:100% !important;}
section.main > div {padding:0 !important;}

/* Force full height on main container */
section.main {
    height:100vh;
    overflow:hidden;
}

/* Column container full height */
[data-testid="stHorizontalBlock"] {
    height:100vh !important;
    gap:0 !important;
}

/* Make columns full height with backgrounds */
[data-testid="column"] {
    height:100vh !important;
    padding:0 !important;
}

/* Left column - dark green */
[data-testid="column"]:first-child {
    background:#0b1a14 !important;
}

/* Right column - dark blue with centering */
[data-testid="column"]:last-child {
    background:#0f172a !important;
}

/* Wrapper inside right column */
[data-testid="column"]:last-child > div {
    height:100vh;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    padding-top:0 !important;
}

/* Content container with top margin */
.login-content {
    width:420px;
    max-width:90%;
    margin-top:80px;
}

/* Button styling */
.stButton > button {
    background:#C6A24A !important;
    color:#ffffff !important;
    font-weight:700 !important;
    border-radius:8px !important;
    padding:10px 32px !important;
    border:none !important;
    width:100% !important;
}

.stButton > button:hover {
    background:#D4AF37 !important;
}

/* Input field labels */
.stTextInput > label {
    color:#cbd5e1 !important;
    font-size:14px !important;
}

/* Spacing */
.stTextInput {
    margin-bottom:12px !important;
}
</style>
""", unsafe_allow_html=True)

# Two columns
left, right = st.columns([1.15, 1], gap="small")

with left:
    st.write("")  # Empty content to render the column

with right:
    st.markdown('<div class="login-content">', unsafe_allow_html=True)
    
    # Logo centered
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image("assets/esuae_logo.png", width=90)
    
    st.markdown("<p style='color:#cbd5e1; font-size:14px; margin:20px 0;'>Secure access required</p>", unsafe_allow_html=True)
    
    # Email field
    email = st.text_input("Email", placeholder="name@elitesportuae.ae")
    
    # Password field
    password = st.text_input("Password", type="password")
    
    # Login button
    login_clicked = st.button("Login")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if login_clicked:
        users = st.secrets.get("auth_users", {})
        if email in users and password == users[email]:
            st.session_state.is_authed = True
            st.session_state.user_email = email
            st.switch_page("pages/1_Attendance.py")
        else:
            st.error("Invalid email or password.")