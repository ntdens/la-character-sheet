import json
import streamlit as st
import streamlit_authenticator as stauth
from st_pages import show_pages_from_config, add_page_title, hide_pages
from streamlit_modal import Modal
import pandas as pd
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype,
)
import firebase_admin
from firebase_admin import credentials, db, storage
from math import floor, sqrt
import io
import PIL.Image as Image
import os
import ast
import plotly.graph_objects as go
from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, portrait
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import numpy as np
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
import emoji
import requests
from PIL import Image as ImageCheck
from unicodedata import normalize

add_page_title(layout='wide')

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Username', 'Forgot Password', 'User Management'])

faction_list = [
    "🧝 Unaffilated",
    # "🏴 Blackthorne Company",
    "💰 Guild of the Black Sky",
    "⚜️ Catalpa",
    "🍷 Cedar Hill",
    "🧚‍♀️ The Court of Ashes",
    "🧛‍♂️ The Dismissed",
    "🛡 Eponore",
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
    "🕊️ The White Ravens",
    "🤖 NPC"
]

path_list = [
    '🗡 Warrior',
    '🪤 Rogue',
    '🩸 Healer',
    '🔮 Mage'
]

skill_paths = [
    'Warrior',
    'Rogue',
    'Healer',
    'Mage'
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
    
    tab1, tab2 = st.tabs(['Additional Characters', 'Add New Character'])

    user_data = db.reference("users/").child(st.session_state['username']).get()

    with tab1:
        if 'characters' in user_data.keys():
            popup = Modal('Warning', key='confirm-intent')
            character_data = user_data['characters']
            character_list = []
            for c in character_data.keys():
                c_data = character_data[c]
                path = c_data['path']
                faction = c_data['faction']
                current_name = c_data['character_name']
                try:
                    user_events = c_data['event_info']
                    data_df = pd.DataFrame(json.loads(user_events))
                    data_df.reset_index(drop=True, inplace=True)
                    skill_points = int(data_df["Skill Points"].sum())
                    tier = get_tier(len(data_df[data_df['Event Type'] != "🪚 Work Weekend"]))
                except:
                    skill_points = 0
                    tier = 0
                try:
                    avail_points = int(user_events["Skill Points"].sum()) - int(c['point_spend'])
                except:
                    avail_points = skill_points
                try:
                    image_location = c_data['pic_name']
                    bucket = storage.bucket()
                    blob = bucket.blob(image_location)
                    profile_image = blob.download_as_bytes()
                except:
                    profile_image = "https://static.wixstatic.com/media/e524a6_cb4ccb346db54d2d9b00dbaee7610a97~mv2.png/v1/crop/x_0,y_3,w_800,h_795/fill/w_160,h_153,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/e524a6_cb4ccb346db54d2d9b00dbaee7610a97~mv2.png"
                character_list.append({'Character':c,'Current Name':current_name, 'Path':path,'Faction':faction, 'Tier':tier, 'Skill Points':avail_points})
            char_df = pd.DataFrame(character_list)
            char_name_list = list(char_df['Character']) 
            st.dataframe(char_df, hide_index=True, use_container_width=True)
            st.write('### Delete Additional Character')
            with st.form('del_char'):
                char_to_delete = st.selectbox('Character', char_df['Character'])
                if st.form_submit_button('Delete Character', type='primary'):
                    popup.open()
            if popup.is_open():
                with popup.container():
                    st.write('Are you sure you want to delete {}?'.format(char_to_delete))
                    if st.button('Yes, Delete', type='primary'):
                        db.reference("users/").child("{}/characters/{}".format(st.session_state['username'],char_to_delete)).delete()
                        popup.close()
                        st.rerun()
                    if st.button("I've Changed My Mind"):
                        popup.close()
        else:
            st.warning('No additional characters found')
            char_name_list = []

    with tab2:
        with st.form('my_form'):
            character_name_input = st.text_input('Character Name', key='form_char', value='')
            path_input = st.selectbox('Path', path_list, key='form_path')
            faction_input = st.selectbox('Faction', faction_list, key='form_faction')
            uploaded_file = st.file_uploader('Upload Profile Picture', type=['png','gif','jpg','jpeg'], key='form_image')
            if uploaded_file is not None:
                form_image = uploaded_file.getvalue()
                pic_name = '{}.{}'.format(character_name_input,uploaded_file.name.split('.')[1])
                image = ImageCheck.open(io.BytesIO(form_image))
                image.save(pic_name)
            submitted = st.form_submit_button('Save Edits')
            if submitted:
                if character_name_input == '':
                    st.error('Please enter an unique character name')
                elif character_name_input in (char_name_list + [user_data['character_name']]):
                    st.error('You already have a character with that name')
                else:
                    doc_ref = db.reference("users/").child("{}/characters/{}".format(st.session_state['username'], character_name_input))
                    doc_ref.update({
                        "character_name":character_name_input,
                        "path":path_input,
                        "faction":faction_input,
                    })
                    if uploaded_file is not None:
                        pic_location = '{}/{}.{}'.format(st.session_state['username'],character_name_input,uploaded_file.name.split('.')[1])
                        doc_ref.update({
                        "pic_name":pic_location
                        })
                        bucket = storage.bucket()
                        blob = bucket.blob(pic_location)
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