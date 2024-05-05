import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
import smtplib
import ssl
from email.mime.text import MIMEText
from st_pages import show_pages_from_config, add_page_title, hide_pages

add_page_title()

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Password'])

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

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
    elif username_of_forgotten_username == False:
        st.error('Email not found')
except Exception as e:
    st.error(e)

with open('./config.yaml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False)