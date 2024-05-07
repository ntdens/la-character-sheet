import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from st_pages import show_pages_from_config, add_page_title, hide_pages
from streamlit_extras.stateful_button import button
import firebase_admin
from firebase_admin import credentials, db
import json

add_page_title()

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Username', 'Forgot Password', 'User Management'])

if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase"], strict=False)
    creds = credentials.Certificate(key_dict)
    defualt_app = firebase_admin.initialize_app(creds, {
        'databaseURL': 'https://la-character-sheets-default-rtdb.firebaseio.com',
        'storageBucket':'la-character-sheets.appspot.com'
    })

config = db.reference("auth").get()

#login widget
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

#authenticate login
authenticator.login()
#authenticate users
if st.session_state["authentication_status"]:
    doc_ref = db.reference("users/").child(st.session_state['username']).get()
    st.text('Username: {}'.format(st.session_state["username"]))
    st.text('Name: {}'.format(st.session_state["name"]))
    if button("Reset Password", type='primary', key='reset_password'):
        try:
            if authenticator.reset_password(st.session_state["username"]):
                st.success('Password modified successfully')
                user_auth = db.reference("auth").child('credentials/usernames/{}'.format(st.session_state['username']))
                user_auth.update(config['credentials']['usernames'][st.session_state['username']])
        except Exception as e:
            st.error(e)
    if button("Update User Details", key='user_details'):
        try:
            if authenticator.update_user_details(st.session_state["username"]):
                doc_ref = db.reference("users/").child(st.session_state['username'])
                doc_ref.update({
                    "name":st.session_state['name'],
                })
                user_auth = db.reference("auth").child('credentials/usernames/{}'.format(st.session_state['username']))
                user_auth.update(config['credentials']['usernames'][st.session_state['username']])
        except Exception as e:
            st.error(e)
    authenticator.logout()

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
    st.page_link("pages/register_user.py", label='Register New User', icon="📝")
    st.page_link("pages/forgot_username.py", label='Forgot Username', icon="👤")
    st.page_link("pages/forgot_password.py", label='Forgot Password', icon="🔑")
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
    st.page_link("pages/register_user.py", label='Register New User', icon="📝")
    st.page_link("pages/forgot_username.py", label='Forgot Username', icon="👤")
    st.page_link("pages/forgot_password.py", label='Forgot Password', icon="🔑")

with open('./config.yaml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False)