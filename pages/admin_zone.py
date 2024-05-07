import yaml
from yaml.loader import SafeLoader
import json
import streamlit as st
import streamlit.components.v1 as components
import streamlit_authenticator as stauth
from streamlit_extras.grid import grid
from streamlit_extras.stylable_container import stylable_container
from st_pages import show_pages_from_config, add_page_title, hide_pages
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import firebase_admin
from firebase_admin import credentials, db, storage
from math import floor, sqrt
import io
import PIL.Image as Image
import os
import numpy as np
import ast

add_page_title(layout='wide')

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Username', 'Forgot Password', 'User Management'])

faction_list = [
    "🧝 Unaffilated",
    "🏴 Blackthorne Company",
    "💰 Guild of the Black Sky",
    "🛡 Eponore",
    "⚜️ Catalpa",
    "🍷 Cedar Hill",
    "🧛‍♂️ The Dismissed",
    "💀 Geth",
    "❄️ Grimfrost",
    "🌳 The Grove",
    "🌙 The Irregulars",
    "⚖️ The Order",
    "🎪 Prismatic Troupe",
    "⚔️ Sunsteel Company",
    "🦁 Kult of Tharros",
    "🐴 Vidarian Khanate",
    "🏹 The Wardens",
    "🕊️ The White Ravens "
]

path_list = [
    '🗡 Warrior',
    '🪤 Rogue',
    '🩹 Healer',
    '🔮 Wizard'
]

def get_tier(events):
    return floor((sqrt(8*events)-1)/2)

if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase"], strict=False)
    creds = credentials.Certificate(key_dict)
    defualt_app = firebase_admin.initialize_app(creds, {
        'databaseURL': 'https://la-character-sheets-default-rtdb.firebaseio.com',
        'storageBucket':'la-character-sheets.appspot.com'
    })

with open( "style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

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
    if st.session_state['username'] in st.secrets['admins']:
        user_data = db.reference("users/").get()
        tab1, tab2,tab3 = st.tabs(['Player List', 'Character View', 'Event View'])
        user_table = []
        for key in user_data.keys():
            try:
                user_events = pd.DataFrame(json.loads(user_data[key]['event_info']))
                user_events.reset_index(drop=True, inplace=True)
                tier = get_tier(len(user_events[user_events['Event Type'] != "🪚 Work Weekend"]))
                try:
                    skill_points = int(user_events["Skill Points"].sum()) - int(user_data[key]['point_spend'])
                except:
                    skill_points = int(user_events["Skill Points"].sum())
            except:
                skill_points = 0
                tier = 0

            user_table.append({
                'Username':key,
                'Player':user_data[key]['name'],
                'Character':user_data[key]['character_name'],
                'Faction':user_data[key]['faction'],
                'Path':user_data[key]['path'],
                'Tier':tier,
                'Skill Points':skill_points
            })
        user_df = pd.DataFrame(user_table)
        with tab1:
            st.dataframe(user_df, hide_index=True)
        with tab2:
            df = pd.read_excel('Skills_Table.xlsx')
            character_choice = st.selectbox('Select User:', user_df['Username'], key='sheet_user', index=list(user_df['Username']).index('ntdens'))
            try:
                character_data = user_data[character_choice]
                user_events = pd.DataFrame(json.loads(character_data['event_info']))
                user_events.reset_index(drop=True, inplace=True)
                known = ast.literal_eval(character_data['known'])
                known_data = df[df['Skill Name'].isin(known)]
                display_data = known_data[['Skill Name', 'Description', 'Limitations', 'Prerequisite']].drop_duplicates(subset=['Skill Name']).copy()
                try:
                    image_location = character_data['pic_name']
                    bucket = storage.bucket()
                    blob = bucket.blob(image_location)
                    profile_image = blob.download_as_bytes()
                except:
                    profile_image = "https://static.wixstatic.com/media/e524a6_cb4ccb346db54d2d9b00dbaee7610a97~mv2.png/v1/crop/x_0,y_3,w_800,h_795/fill/w_160,h_153,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/e524a6_cb4ccb346db54d2d9b00dbaee7610a97~mv2.png"
                with st.container(border=True):
                    my_grid = grid([4,6],1)
                    my_grid.container(border=True).image(profile_image)
                    player_data = pd.DataFrame({
                        'Category': ['Character: ','Player: ','Path: ','Faction: ','Tier: ','Skill Points: '],
                        'Information': [character_data['character_name'],character_data['name'],character_data['path'],character_data['faction'],user_df[user_df['Username'] == character_choice]['Tier'].values[0],user_df[user_df['Username'] == character_choice]['Skill Points'].values[0]]
                                        })
                    my_grid.dataframe(player_data, hide_index=True, use_container_width=True)
                    my_grid.dataframe(display_data.astype(str), hide_index=True, use_container_width=True)
            except:
                st.info("Data does not exist for this user")
        with tab3:
            character_choice = st.selectbox('Select User:', user_df['Username'], key='event_user', index=list(user_df['Username']).index('ntdens'))
            try:
                character_data = user_data[character_choice]
                user_events = pd.DataFrame(json.loads(character_data['event_info']))
                user_events.reset_index(drop=True, inplace=True)
                st.dataframe(user_events, hide_index=True)
            except:
                st.info("Data does not exist for this user")
    else:
        st.warning('Not an admin. Access denied. Whomp whomp.')

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