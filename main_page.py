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


def skill_gain(df, skill_path, tier):
    df = df.copy()
    df1 = df.copy()
    try:
        user_data = db.reference("users/").child(st.session_state['username']).get()
        st.session_state['point_spend'] = int(user_data['point_spend'])
    except:
        st.session_state['point_spend'] = 0  
    if "available" not in st.session_state:
        st.session_state['available'] = skill_points - st.session_state['point_spend']
    try:
        user_data = db.reference("users/").child(st.session_state['username']).get()
        st.session_state['known'] = ast.literal_eval(user_data['known'])
    except:
        st.session_state["known"] = []  
    point_cost = []
    keep_rows = []
    df['Prerequisite'] = df['Prerequisite'].fillna('None')
    warrior_max = 0
    rogue_max = 0
    healer_max = 0
    mage_max = 0
    bard_max = 1
    known_data = df[df['Skill Name'].isin(st.session_state['known'])]
    display_data = known_data.copy()[['Skill Name', 'Description', 'Limitations', 'Prerequisite']].drop_duplicates(subset=['Skill Name'])
    if not known_data.empty:
        if not known_data[known_data['Path'] == 'Warrior'].empty:
            warrior_max = known_data[known_data['Path'] == 'Warrior']['Tier'].max() + 1
        if not known_data[known_data['Path'] == 'Rogue'].empty:
            rogue_max = known_data[known_data['Path'] == 'Rogue']['Tier'].fillna(0).max() + 1
        if not known_data[known_data['Path'] == 'Healer'].empty:
            healer_max = known_data[known_data['Path'] == 'Healer']['Tier'].fillna(0).max() + 1
        if not known_data[known_data['Path'] == 'Mage'].empty:
            mage_max = known_data[known_data['Path'] == 'Mage']['Tier'].fillna(0).max() + 1
        if not known_data[known_data['Path'] == 'Bard'].empty:
            bard_max = known_data[known_data['Path'] == 'Bard']['Tier'].fillna(0).max() + 1
    known_skill_list = list(known_data['Skill Name'].unique())
    for index, row in df.iterrows():
        if row['Path'] != skill_path:
            if row['Path'] != 'Bard':
                if row['Tier'] == 0:
                    point_cost.append(2)
                else:
                    point_cost.append(row['Tier']*2)
            else:
                point_cost.append(row['Tier'])
        else:
            point_cost.append(row['Tier'])
        if row['Prerequisite'] != 'None':
            if row['Prerequisite'] not in known_skill_list:
                pass
        else:
            keep_rows.append(index)
    df['Point Cost'] = point_cost
    if not known_data.empty:
        tier_max = known_data[known_data['Path'] == skill_path]['Tier'].max() + 1
    else:
        tier_max = 0
    df = df[df['Point Cost'] <= tier_max]
    warrior_index = list(df[(df['Path'] == 'Warrior') & (df['Tier'] <= warrior_max)].index)
    rogue_index = list(df[(df['Path'] == 'Rogue') & (df['Tier'] <= rogue_max)].index)
    healer_index = list(df[(df['Path'] == 'Healer') & (df['Tier'] <= healer_max)].index)
    mage_index = list(df[(df['Path'] == 'Mage') & (df['Tier'] <= mage_max)].index)
    bard_index = list(df[(df['Path'] == 'Bard') & (df['Tier'] <= bard_max)].index)
    if tier_max >= 3:
        skill_keep = warrior_index + rogue_index + healer_index + mage_index + bard_index
    else:
        skill_keep = warrior_index + rogue_index + healer_index + mage_index
    df = df.filter(items=keep_rows, axis=0)
    df = df.filter(items=skill_keep, axis=0)
    df = df[df['Point Cost'] <= st.session_state['available']]
    df = df[df['Skill Name'] != 'Cross-Training']
    df = df[df['Tier'] <= tier]
    if 'Read/Write Arcana' not in known_skill_list:
        df = df[df['Spell'] == False]
    known_index = list(df[df['Skill Name'].isin(st.session_state['known'])].index)
    df = df.drop(known_index)
    new_skill = st.selectbox('Pick New Skill', list(df['Skill Name'].unique()))
    if st.button('Gain Skill'):
        gain_df = df[df['Skill Name'] == new_skill]
        idxmin = gain_df.groupby(['Skill Name'])['Point Cost'].idxmin()
        skill_df = gain_df.loc[idxmin]
        st.session_state['point_spend'] = st.session_state['point_spend'] + skill_df['Point Cost'].values[0]
        st.session_state['available'] = skill_points - st.session_state['point_spend']
        known_list = st.session_state['known']
        known_list.append(skill_df['Skill Name'].values[0])
        st.session_state['known'] = known_list
        doc_ref = db.reference("users/").child(st.session_state['username'])
        doc_ref.update({
            "known":str(st.session_state['known']),
            "point_spend":str(st.session_state['point_spend']),
        })
        point_cost = []
        keep_rows = []
        df['Prerequisite'] = df['Prerequisite'].fillna('None')
        warrior_max = 0
        rogue_max = 0
        healer_max = 0
        mage_max = 0
        bard_max = 1
        known_data = df[df['Skill Name'].isin(st.session_state['known'])]
        display_data = known_data.copy()[['Skill Name', 'Description', 'Limitations', 'Prerequisite']].drop_duplicates(subset=['Skill Name'])
        if not known_data.empty:
            if not known_data[known_data['Path'] == 'Warrior'].empty:
                warrior_max = known_data[known_data['Path'] == 'Warrior']['Tier'].max() + 1
            if not known_data[known_data['Path'] == 'Rogue'].empty:
                rogue_max = known_data[known_data['Path'] == 'Rogue']['Tier'].fillna(0).max() + 1
            if not known_data[known_data['Path'] == 'Healer'].empty:
                healer_max = known_data[known_data['Path'] == 'Healer']['Tier'].fillna(0).max() + 1
            if not known_data[known_data['Path'] == 'Mage'].empty:
                mage_max = known_data[known_data['Path'] == 'Mage']['Tier'].fillna(0).max() + 1
            if not known_data[known_data['Path'] == 'Bard'].empty:
                bard_max = known_data[known_data['Path'] == 'Bard']['Tier'].fillna(0).max() + 1
        known_skill_list = list(known_data['Skill Name'].unique())
        for index, row in df.iterrows():
            if row['Path'] != skill_path:
                if row['Path'] != 'Bard':
                    if row['Tier'] == 0:
                        point_cost.append(2)
                    else:
                        point_cost.append(row['Tier']*2)
                else:
                    point_cost.append(row['Tier'])
            else:
                point_cost.append(row['Tier'])
            if row['Prerequisite'] != 'None':
                if row['Prerequisite'] not in known_skill_list:
                    pass
            else:
                keep_rows.append(index)
        df['Point Cost'] = point_cost
        if not known_data.empty:
            tier_max = known_data[known_data['Path'] == skill_path]['Tier'].max() + 1
        else:
            tier_max = 0
        df = df[df['Point Cost'] <= tier_max]
        warrior_index = list(df[(df['Path'] == 'Warrior') & (df['Tier'] <= warrior_max)].index)
        rogue_index = list(df[(df['Path'] == 'Rogue') & (df['Tier'] <= rogue_max)].index)
        healer_index = list(df[(df['Path'] == 'Healer') & (df['Tier'] <= healer_max)].index)
        mage_index = list(df[(df['Path'] == 'Mage') & (df['Tier'] <= mage_max)].index)
        bard_index = list(df[(df['Path'] == 'Bard') & (df['Tier'] <= bard_max)].index)
        if tier_max >= 3:
            skill_keep = warrior_index + rogue_index + healer_index + mage_index + bard_index
        else:
            skill_keep = warrior_index + rogue_index + healer_index + mage_index
        df = df.filter(items=keep_rows, axis=0)
        df = df.filter(items=skill_keep, axis=0)
        df = df[df['Point Cost'] <= st.session_state['available']]
        df = df[df['Skill Name'] != 'Cross-Training']
        df = df[df['Tier'] <= tier]
        if 'Read/Write Arcana' not in known_skill_list:
            df = df[df['Spell'] == False]
        known_index = list(df[df['Skill Name'].isin(st.session_state['known'])].index)
        df = df.drop(known_index)
        st.rerun()
    remove_skill = st.selectbox('Pick Skill To Remove', st.session_state['known'])
    if st.button("Remove Skill"):
        gain_df = df1[df1['Skill Name'] == remove_skill]
        idxmin = gain_df.groupby(['Skill Name'])['Point Cost'].idxmin()
        skill_df = gain_df.loc[idxmin]
        st.session_state['point_spend'] = st.session_state['point_spend'] - skill_df['Point Cost'].values[0]
        st.session_state['available'] = skill_points - st.session_state['point_spend']
        known_list = st.session_state['known']
        known_list.remove(skill_df['Skill Name'].values[0])
        st.session_state['known'] = known_list
        doc_ref = db.reference("users/").child(st.session_state['username'])
        doc_ref.update({
            "known":str(st.session_state['known']),
            "point_spend":str(st.session_state['point_spend']),
        })
        st.rerun()
    return df, display_data


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
        faction = user_data['faction']
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

    
    tab1, tab2,tab3 = st.tabs(['Character Sheet', 'Edit Character', 'Add Skills'])


    player = st.session_state["name"]


    with tab2:
        with st.form('my_form'):
            character_name_input = st.text_input('Character Name', value=character_name, key='form_char')
            path_input = st.selectbox('Path', path_list, index=path_list.index(path), key='form_path')
            faction_input = st.selectbox('Faction', faction_list, index=faction_list.index(faction), key='form_faction')
            uploaded_file = st.file_uploader('Upload Profile Picture', type=['png','gif','jpg','jpeg'], key='form_image')
            if uploaded_file is not None:
                form_image = uploaded_file.getvalue()
                pic_name = '{}.{}'.format(st.session_state['username'],uploaded_file.name.split('.')[1])
                image = Image.open(io.BytesIO(form_image))
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

    if 'form_char' in st.session_state:
        character_name = st.session_state['form_char']
    if 'form_path' in st.session_state:
        path = st.session_state['form_path']
    if 'form_faction' in st.session_state:
        faction = st.session_state['form_faction']
    if uploaded_file is not None:
        profile_image = st.session_state['form_image']


    with tab3:
        df = pd.read_excel('Skills_Table.xlsx')
        df['Tier'] = df.Tier.astype(int)
        skill_path = path[2:]
        point_cost = []
        for index, row in df.iterrows():
            if row['Path'] != skill_path:
                if row['Path'] != 'Bard':
                    if row['Tier'] == 0:
                        point_cost.append(2)
                    else:
                        point_cost.append(row['Tier']*2)
                else:
                    point_cost.append(row['Tier'])
            else:
                point_cost.append(row['Tier'])
        df['Point Cost'] = point_cost
        df, display_df = skill_gain(df, skill_path, tier)
        "## Known Skills"
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        "## Available Skills"
        st.dataframe(df, hide_index=True, use_container_width=True)

    


    with tab1:
        df = pd.read_excel('Skills_Table.xlsx')
        known = st.session_state['known']
        known_data = df[df['Skill Name'].isin(known)]
        display_data = known_data[['Skill Name', 'Description', 'Limitations', 'Prerequisite']].drop_duplicates(subset=['Skill Name']).copy()
        points_available = skill_points - st.session_state['point_spend']
        with st.container(border=True):
            my_grid = grid([4,6],1)
            my_grid.container(border=True).image(profile_image)
            player_data = pd.DataFrame({
                'Category': ['Character: ','Player: ','Path: ','Faction: ','Tier: ','Skill Points: '],
                'Information': [character_name,player,path,faction,tier,points_available]
                                })
            my_grid.dataframe(player_data, hide_index=True, use_container_width=True)
            my_grid.dataframe(display_data.astype(str), hide_index=True, use_container_width=True)






    

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


