import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from st_pages import show_pages_from_config, add_page_title, hide_pages
import firebase_admin
from firebase_admin import credentials, db
import json

add_page_title()

show_pages_from_config()

hide_pages(['Forgot Username', 'Forgot Password'])

config = db.reference("auth").get()

if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase"], strict=False)
    creds = credentials.Certificate(key_dict)
    defualt_app = firebase_admin.initialize_app(creds, {
        'databaseURL': 'https://la-character-sheets-default-rtdb.firebaseio.com',
        'storageBucket':'la-character-sheets.appspot.com'
    })

#login widget
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

#new user registration
try:
    st.info('Use Player Name for Name')
    email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(pre_authorization=False)
    if email_of_registered_user:
        user_auth = db.reference("auth").child(f'credentials/usernames/{username_of_registered_user}')
        user_auth.update(config['credentials']['usernames'][username_of_registered_user])
        st.success('User registered successfully')
    
except Exception as e:
    st.error(e)