import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from streamlit_extras.stateful_button import button
import firebase_admin
from firebase_admin import credentials, db
import json
from sheet_helpers import APP_PATH, sidebar_about

if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase"], strict=False)
    creds = credentials.Certificate(key_dict)
    defualt_app = firebase_admin.initialize_app(creds, {
        'databaseURL': 'https://la-character-sheets-default-rtdb.firebaseio.com',
        'storageBucket':'la-character-sheets.appspot.com'
    })

with open( "style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)

config = db.reference("auth").get()

st.sidebar.title("About")
sidebar_about()

#authenticate users
if st.session_state["authentication_status"]:
    st.info(f"Check out the [User Guide]({APP_PATH}/User%20Guide?tab=Profile) for more info.", icon=":material/help:")
    doc_ref = db.reference("users/").child(st.session_state['username']).get()
    user_auth = db.reference("auth").child('credentials/usernames/{}'.format(st.session_state['username'])).get()
    user_email = user_auth['email']
    st.write('Username: {}'.format(st.session_state["username"]))
    st.write('Name: {}'.format(st.session_state["name"]))
    st.write('Email: {}'.format(user_email))
    if button("Reset Password", type='primary', key='reset_password'):
        try:
            if st.session_state['auth_data'].reset_password(st.session_state["username"]):
                st.success('Password modified successfully')
                user_auth = db.reference("auth").child('credentials/usernames/{}'.format(st.session_state['username']))
                user_auth.update(config['credentials']['usernames'][st.session_state['username']])
        except Exception as e:
            st.error(e)
    if button("Update User Details", key='user_details'):
        try:
            if st.session_state['auth_data'].update_user_details(st.session_state["username"]):
                user_auth = db.reference("auth").child('credentials/usernames/{}'.format(st.session_state['username']))
                user_auth.update(config['credentials']['usernames'][st.session_state['username']])
        except Exception as e:
            st.error(e)
    st.session_state['auth_data'].logout()

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

with open('./config.yaml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False)