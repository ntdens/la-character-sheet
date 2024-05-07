import streamlit as st
import streamlit_authenticator as stauth
import smtplib
from email.mime.text import MIMEText
from st_pages import show_pages_from_config, add_page_title, hide_pages
import firebase_admin
from firebase_admin import credentials, db
import json

add_page_title()

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Password'])

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

#forgot username
try:
    username_of_forgotten_username, email_of_forgotten_username = authenticator.forgot_username()
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
except Exception as e:
    st.error(e)
