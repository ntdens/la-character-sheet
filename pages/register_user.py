import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from st_pages import show_pages_from_config, add_page_title, hide_pages

add_page_title()

show_pages_from_config()

hide_pages(['Forgot Username', 'Forgot Password'])

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

#login widget
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

#new user registration
try:
    email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(pre_authorization=False)
    if email_of_registered_user:
        st.success('User registered successfully')
except Exception as e:
    st.error(e)

with open('./config.yaml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False)