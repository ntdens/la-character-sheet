import streamlit as st
import json
from st_pages import add_page_title, get_nav_from_toml, hide_pages
import streamlit_authenticator as stauth
import firebase_admin
from firebase_admin import credentials, db, storage

st.set_page_config(layout="wide")

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
    config['cookie']['expiry_days'],
)
st.session_state['auth_data'] = authenticator
#authenticate login
authenticator.login()


nav = get_nav_from_toml(".streamlit/pages.toml")
st.logo('la_logo.png')
pg = st.navigation(nav)
add_page_title(pg)
# hide_pages(['Register New User', 'Forgot Username', 'Forgot Password'])
pg.run()
