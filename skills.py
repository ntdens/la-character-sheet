import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import json
from sheet_helpers import filter_dataframe, APP_PATH, sidebar_about


with open( "style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)

if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase"], strict=False)
    creds = credentials.Certificate(key_dict)
    defualt_app = firebase_admin.initialize_app(creds, {
        'databaseURL': 'https://la-character-sheets-default-rtdb.firebaseio.com',
        'storageBucket':'la-character-sheets.appspot.com'
    })

config = db.reference("auth").get()

st.sidebar.title("About")
sidebar_about()

#authenticate users
if st.session_state["authentication_status"]:
    df = pd.read_excel('Skills_Table.xlsx')
    df['Tier'] = df.Tier.astype(int)
    st.info(f"Check out the [User Guide]({APP_PATH}/User%20Guide?tab=Skills) for more info.", icon=":material/help:")
    try:
        st.dataframe(filter_dataframe(df), hide_index=True, height=950, use_container_width=True)
    except:
        st.warning("You've filtered too far. Try again")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
    # st.page_link(st.Page("pages/register_user.py"), label='Register New User', icon="📝")
    # st.page_link(st.Page("pages/forgot_username.py"), label='Forgot Username', icon="👤")
    # st.page_link(st.Page("pages/forgot_password.py"), label='Forgot Password', icon="🔑")

elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
    # st.page_link(st.Page("pages/register_user.py"), label='Register New User', icon="📝")
    # st.page_link(st.Page("pages/forgot_username.py"), label='Forgot Username', icon="👤")
    # st.page_link(st.Page("pages/forgot_password.py"), label='Forgot Password', icon="🔑")