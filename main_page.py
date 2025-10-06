import streamlit as st
import json
from st_pages import add_page_title, get_nav_from_toml, hide_pages
import streamlit_authenticator as stauth
import firebase_admin
from firebase_admin import credentials, db
from email.mime.text import MIMEText
import smtplib

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
authenticator.login()
if 'authentication_status' not in st.session_state or st.session_state["authentication_status"] is False or st.session_state["authentication_status"] is None:
#authenticate login
    tab1, tab2,tab3 = st.tabs(['Register User', 'Forget Username', 'Forget Password'])

    with tab1:
        #new user registration
        st.info('Use real name for Name field, used to track player across characters. Password must have at least 1 uppercase, 1 lowercase, 1 number and 1 special character and be at least 8 characters long. Username cannot contain spaces or special characters')
        email_of_registered_user, username_of_registered_user, name_of_registered_user = st.session_state['auth_data'].register_user()
        if email_of_registered_user:
            user_auth = db.reference("auth").child(f'credentials/usernames/{username_of_registered_user}')
            user_auth.update(config['credentials']['usernames'][username_of_registered_user])
            st.success('User registered successfully')

    with tab2:
        #forgot username
        username_of_forgotten_username, email_of_forgotten_username = st.session_state['auth_data'].forgot_username()
        if username_of_forgotten_username:
            st.success('Username to be sent securely. Be sure to check your spam folder.')
            sender_email = "larpadventerurescharactersheet@gmail.com"  # Enter your address
            receiver_email = email_of_forgotten_username  # Enter receiver address
            password = st.secrets['email_password']
            body = "Your username is {}.".format(username_of_forgotten_username)
            msg = MIMEText(body)
            msg['Subject'] = 'LARP Character Sheet Forgotten Username'
            msg['From'] = "larpadventerurescharactersheet@gmail.com"
            msg['To'] = email_of_forgotten_username
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            user_auth = db.reference("auth").child(f'credentials/usernames/{username_of_forgotten_username}')
            user_auth.update(config['credentials']['usernames'][username_of_forgotten_username])
        elif username_of_forgotten_username == False:
            st.error('Email not found')

    with tab3:
        #forgot password
        username_of_forgotten_password, email_of_forgotten_password, new_random_password = st.session_state['auth_data'].forgot_password()
        if username_of_forgotten_password:
            st.success('New password to be sent securely')
            sender_email = "larpadventerurescharactersheet@gmail.com"  # Enter your address
            receiver_email = email_of_forgotten_password  # Enter receiver address
            password = st.secrets['email_password']
            body = "Your new password is {}.".format(new_random_password)
            msg = MIMEText(body)
            msg['Subject'] = 'LARP Character Sheet Forgotten Username'
            msg['From'] = "larpadventerurescharactersheet@gmail.com"
            msg['To'] = email_of_forgotten_password
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            user_auth = db.reference("auth").child(f'credentials/usernames/{username_of_forgotten_password}')
            user_auth.update(config['credentials']['usernames'][username_of_forgotten_password])
        elif username_of_forgotten_password == False:
            st.error('Username not found')

nav = get_nav_from_toml(".streamlit/pages.toml")
# st.logo('la_logo.png')
pg = st.navigation(nav)
add_page_title(pg)
# hide_pages(['Register New User', 'Forgot Username', 'Forgot Password'])
pg.run()
