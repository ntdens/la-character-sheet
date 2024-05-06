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
            character_choice = st.selectbox('Select User:', user_df['Username'], key='sheet_user')
            try:
                character_data = user_data[character_choice]
                user_events = pd.DataFrame(json.loads(character_data['event_info']))
                user_events.reset_index(drop=True, inplace=True)
                known = ast.literal_eval(character_data['known'])
                known_data = df[df['Skill Name'].isin(known)]
                display_data = known_data[['Skill Name', 'Description', 'Limitations', 'Prerequisite']].drop_duplicates(subset=['Skill Name']).copy()
                image_location = character_data['pic_name']
                bucket = storage.bucket()
                blob = bucket.blob(image_location)
                profile_image = blob.download_as_bytes()
                with st.container(border=True):
                    my_grid = grid([4,6],1)
                    my_grid.container(border=True).image(profile_image)
                    player_data = pd.DataFrame({
                        'Category': ['Character: ','Player: ','Path: ','Faction: ','Tier: ','Skill Points: '],
                        'Information': [character_data['character_name'],config['credentials']['usernames'][character_choice]['name'],character_data['path'],character_data['faction'],user_df[user_df['Username'] == character_choice]['Tier'].values[0],user_df[user_df['Username'] == character_choice]['Skill Points'].values[0]]
                                        })
                    my_grid.dataframe(player_data, hide_index=True, use_container_width=True)
                    my_grid.dataframe(display_data.astype(str), hide_index=True, use_container_width=True)
            except:
                st.info("Data does not exist for this user")
        with tab3:
            character_choice = st.selectbox('Select User:', user_df['Username'], key='event_user')
            try:
                character_data = user_data[character_choice]
                user_events = pd.DataFrame(json.loads(character_data['event_info']))
                user_events.reset_index(drop=True, inplace=True)
                st.dataframe(user_events, hide_index=True)
            except:
                st.info("Data does not exist for this user")
    else:
        st.warning('Not an admin. Access denied. Whomp whomp.')


    # player = st.session_state["name"]


    # with tab2:
    #     with st.form('my_form'):
    #         character_name_input = st.text_input('Character Name', value=character_name, key='form_char')
    #         path_input = st.selectbox('Path', path_list, index=path_list.index(path), key='form_path')
    #         faction_input = st.selectbox('Faction', faction_list, index=faction_list.index(faction), key='form_faction')
    #         uploaded_file = st.file_uploader('Upload Profile Picture', type=['png','gif','jpg','jpeg'], key='form_image')
    #         if uploaded_file is not None:
    #             form_image = uploaded_file.getvalue()
    #             pic_name = '{}.{}'.format(st.session_state['username'],uploaded_file.name.split('.')[1])
    #             image = Image.open(io.BytesIO(form_image))
    #             image.save(pic_name)
    #         submitted = st.form_submit_button('Save Edits')
    #         if submitted:
    #             doc_ref = db.reference("users/").child(st.session_state['username'])
    #             doc_ref.update({
    #                 "character_name":character_name_input,
    #                 "path":path_input,
    #                 "faction":faction_input,
    #             })
    #             if uploaded_file is not None:
    #                 doc_ref.update({
    #                 "pic_name":pic_name
    #                 })
    #                 bucket = storage.bucket()
    #                 blob = bucket.blob(pic_name)
    #                 blob.upload_from_filename(pic_name)
    #                 os.remove(pic_name)

    # if 'form_char' in st.session_state:
    #     character_name = st.session_state['form_char']
    # if 'form_path' in st.session_state:
    #     path = st.session_state['form_path']
    # if 'form_faction' in st.session_state:
    #     faction = st.session_state['form_faction']
    # if uploaded_file is not None:
    #     profile_image = st.session_state['form_image']


    # with tab3:
    #     df = pd.read_excel('Skills_Table.xlsx')
    #     df['Tier'] = df.Tier.astype(int)
    #     skill_path = path[2:]
    #     point_cost = []
    #     for index, row in df.iterrows():
    #         if row['Path'] != skill_path:
    #             if row['Path'] != 'Bard':
    #                 if row['Tier'] == 0:
    #                     point_cost.append(2)
    #                 else:
    #                     point_cost.append(row['Tier']*2)
    #             else:
    #                 point_cost.append(row['Tier'])
    #         else:
    #             point_cost.append(row['Tier'])
    #     df['Point Cost'] = point_cost
    #     df, display_df = skill_gain(df, skill_path, tier)
    #     "## Known Skills"
    #     st.dataframe(display_df, hide_index=True, use_container_width=True)
    #     "## Available Skills"
    #     st.dataframe(df, hide_index=True, use_container_width=True)

    


    # with tab1:
    #     df = pd.read_excel('Skills_Table.xlsx')
    #     known = st.session_state['known']
    #     known_data = df[df['Skill Name'].isin(known)]
    #     display_data = known_data[['Skill Name', 'Description', 'Limitations', 'Prerequisite']].drop_duplicates(subset=['Skill Name']).copy()
    #     points_available = skill_points - st.session_state['point_spend']
    #     with st.container(border=True):
    #         my_grid = grid([4,6],1)
    #         my_grid.container(border=True).image(profile_image)
    #         player_data = pd.DataFrame({
    #             'Category': ['Character: ','Player: ','Path: ','Faction: ','Tier: ','Skill Points: '],
    #             'Information': [character_name,player,path,faction,tier,points_available]
    #                             })
    #         my_grid.dataframe(player_data, hide_index=True, use_container_width=True)
    #         my_grid.dataframe(display_data.astype(str), hide_index=True, use_container_width=True)






    

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