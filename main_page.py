import yaml
from yaml.loader import SafeLoader
import json
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_extras.grid import grid
from streamlit_extras.stylable_container import stylable_container
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from st_pages import show_pages_from_config, add_page_title, hide_pages
import firebase_admin
from firebase_admin import credentials, db, storage
from math import floor, sqrt
import io
import PIL.Image as Image
import os


add_page_title()

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
    try:
        user_data = db.reference("users/").child(st.session_state['username']).get()
        user_events = user_data['event_info']
        data_df = pd.DataFrame(json.loads(user_events))
        data_df.reset_index(drop=True, inplace=True)
        skill_points = int(data_df["Skill Points"].sum())
        tier = get_tier(len(data_df[data_df['Event Type'] != "🪚 Work Weekend"]))
    except:
        skill_points = 0
        tier = 0
    try:
        user_data = db.reference("users/").child(st.session_state['username']).get()
        character_name = user_data['character_name']
    except:
        character_name = ""
    
    try:
        user_data = db.reference("users/").child(st.session_state['username']).get()
        path = user_data['path']
    except:
        path = '🗡 Warrior'

    try:
        user_data = db.reference("users/").child(st.session_state['username']).get()
        faction= user_data['faction']
    except:
        faction = "🧝 Unaffilated"

    try:
        user_data = db.reference("users/").child(st.session_state['username']).get()
        image_location = user_data['pic_name']
        bucket = storage.bucket()
        blob = bucket.blob(image_location)
        profile_image = blob.download_as_bytes()
    except:
        profile_image = "https://static.wixstatic.com/media/e524a6_cb4ccb346db54d2d9b00dbaee7610a97~mv2.png/v1/crop/x_0,y_3,w_800,h_795/fill/w_160,h_153,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/e524a6_cb4ccb346db54d2d9b00dbaee7610a97~mv2.png"

    
    player = st.session_state["name"]
    with st.container(border=True):
        my_grid = grid([4,6], 1)
        my_grid.container(border=True).image(profile_image)
        my_grid.text(f"""
                    Character: {character_name}
                    Player: {player}
                    Path: {path}
                    Faction: {faction}
                    Tier: {tier}
                    Skill Points: {skill_points}
                    """)
        my_grid.dataframe()

    with st.form('my_form'):
        character_name_input = st.text_input('Character Name', value=character_name)
        path_input = st.selectbox('Path', path_list, index=path_list.index(path))
        faction_input = st.selectbox('Faction', faction_list, index=faction_list.index(faction))
        uploaded_file = st.file_uploader('Upload Profile Picture')
        if uploaded_file is not None:
            pic_data = uploaded_file.getvalue()
            pic_name = '{}_{}'.format(st.session_state['username'],uploaded_file.name)
            image = Image.open(io.BytesIO(pic_data))
            image.save(pic_name)
        submitted = st.form_submit_button('Save Edits')
        if submitted:
            doc_ref = db.reference("users/").child(st.session_state['username'])
            doc_ref.update({
                "character_name":character_name_input,
                "path":path_input,
                "faction":faction_input,
            })
            if uploaded_file is not None:
                doc_ref.update({
                "pic_name":pic_name
                })
                bucket = storage.bucket()
                blob = bucket.blob(pic_name)
                blob.upload_from_filename(pic_name)
                os.remove(pic_name)
            st.rerun()


    

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


