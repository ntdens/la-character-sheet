import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from st_pages import show_pages_from_config, add_page_title, hide_pages
from streamlit_extras.stateful_button import button

add_page_title()

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Username', 'Forgot Password', 'User Management'])

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

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
    st.text('Username: {}'.format(st.session_state["username"]))
    st.text('Name: {}'.format(st.session_state["name"]))
    st.text('Email: {}'.format(config['credentials']['usernames'][st.session_state["username"]]['email']))
    if button("Reset Password", type='primary', key='reset_password'):
        try:
            if authenticator.reset_password(st.session_state["username"]):
                st.success('Password modified successfully')
        except Exception as e:
            st.error(e)
    if button("Update User Details", key='user_details'):
        try:
            if authenticator.update_user_details(st.session_state["username"]):
                st.success('Entries updated successfully')
        except Exception as e:
            st.error(e)

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

with open('./config.yaml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False)