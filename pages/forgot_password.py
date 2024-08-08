import streamlit as st
import streamlit_authenticator as stauth
import smtplib
from email.mime.text import MIMEText
import firebase_admin
from firebase_admin import credentials, db
import json
from sheet_helpers import sidebar_about


if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase"], strict=False)
    creds = credentials.Certificate(key_dict)
    defualt_app = firebase_admin.initialize_app(creds, {
        'databaseURL': 'https://la-character-sheets-default-rtdb.firebaseio.com',
        'storageBucket':'la-character-sheets.appspot.com'
    })

with open( "style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>', unsafe_allow_html= True)

config = db.reference("auth").get()

st.sidebar.title("About")
sidebar_about()


#forgot password
try:
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
except Exception as e:
    st.error(e)

