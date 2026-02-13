import streamlit as st

st.set_page_config(page_title="ESUAE Attendance", layout="wide")

header_left, header_right = st.columns([1, 5])
with header_left:
    st.image("assets/esuae_logo.png", width=90)
with header_right:
    st.markdown(
        """
        <div style="padding-top:12px;">
            <div style="font-size:34px; font-weight:700; color:#111827;">
                ESUAE Attendance
            </div>
            <div style="font-size:15px; color:#6B7280;">
                Secure access required
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("")

if "is_authed" not in st.session_state:
    st.session_state.is_authed = False

st.subheader("Enter Access Code")

access_code = st.text_input("Access code", type="password", placeholder="Enter your access code")
login_clicked = st.button("Continue", use_container_width=True)

if login_clicked:
    valid_codes = st.secrets.get("auth", {}).get("access_codes", [])
    if access_code in valid_codes:
        st.session_state.is_authed = True
        st.success("Access granted. Use the left menu to open Attendance.")
    else:
        st.error("Invalid access code. Please try again.")

st.info("If you do not have an access code, contact the ESUAE Performance team.")
