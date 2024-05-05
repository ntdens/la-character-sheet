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

hide_pages(['Register New User', 'Forgot Username'])

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

#login widget
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

#forgot password
try:
    username_of_forgotten_password, email_of_forgotten_password, new_random_password = authenticator.forgot_password()
    if username_of_forgotten_password:
        st.success('New password to be sent securely')
        sender_email = "larpadventerurescharactersheet@gmail.com"  # Enter your address
        receiver_email = email_of_forgotten_password  # Enter receiver address
        password = st.secrets['email_password']
        body = "Your temporary password is {}.".format(new_random_password)
        msg = MIMEText(body)
        msg['Subject'] = 'LARP Character Sheet Forgotten Username'
        msg['From'] = "larpadventerurescharactersheet@gmail.com"
        msg['To'] = email_of_forgotten_password
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
    elif username_of_forgotten_password == False:
        st.error('Username not found')
except Exception as e:
    st.error(e)

with open('./config.yaml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False)