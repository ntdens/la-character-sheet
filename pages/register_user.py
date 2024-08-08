import streamlit as st
import streamlit_authenticator as stauth
import firebase_admin
from firebase_admin import credentials, db
import json
from sheet_helpers import sidebar_about

config = db.reference("auth").get()

if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase"], strict=False)
    creds = credentials.Certificate(key_dict)
    defualt_app = firebase_admin.initialize_app(creds, {
        'databaseURL': 'https://la-character-sheets-default-rtdb.firebaseio.com',
        'storageBucket':'la-character-sheets.appspot.com'
    })

with open( "style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>', unsafe_allow_html= True)

st.sidebar.title("About")
sidebar_about()

#new user registration
try:
    st.info('Use real name for Name field, used to track player across characters')
    email_of_registered_user, username_of_registered_user, name_of_registered_user = st.session_state['auth_data'].register_user(pre_authorization=False)
    if email_of_registered_user:
        user_auth = db.reference("auth").child(f'credentials/usernames/{username_of_registered_user}')
        user_auth.update(config['credentials']['usernames'][username_of_registered_user])
        st.success('User registered successfully')
    
except Exception as e:
    st.error(e)