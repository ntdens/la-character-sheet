import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from st_pages import show_pages_from_config, add_page_title, hide_pages
import firebase_admin
from firebase_admin import credentials, db
import json

add_page_title(layout='wide')

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Username', 'Forgot Password', 'User Management'])

with open( "style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    df['Spell'] = df.Spell.astype(str)
    df = df.fillna('None')
    modification_container = st.container()

    with modification_container:
        for column in df.columns:
            left, right = st.columns((1, 20))
            if is_numeric_dtype(df[column]):
                _min = df[column].min()
                _max = df[column].max()
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=1,
                )
                df = df[df[column].between(*user_num_input)]
            # Treat columns with < 10 unique values as categorical
            elif isinstance(df[column], pd.CategoricalDtype) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df

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

#authenticate login
authenticator.login()

#authenticate users
if st.session_state["authentication_status"]:
    df = pd.read_excel('Skills_Table.xlsx')
    df['Tier'] = df.Tier.astype(int)
    st.info('Double click a cell to read full contents')
    st.dataframe(filter_dataframe(df), hide_index=True, height=950, use_container_width=True)

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
    st.page_link("pages/register_user.py", label='Register New User', icon="📝")
    st.page_link("pages/forgot_username.py", label='Forgot Username', icon="👤")
    st.page_link("pages/forgot_password.py", label='Forgot Password', icon="🔑")
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
    st.page_link("pages/register_user.py", label='Register New User', icon="📝")
    st.page_link("pages/forgot_username.py", label='Forgot Username', icon="👤")
    st.page_link("pages/forgot_password.py", label='Forgot Password', icon="🔑")