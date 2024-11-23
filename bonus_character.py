import json
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_modal import Modal
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db, storage
from math import floor, sqrt
import io
import os
from PIL import Image as ImageCheck
import re
from sheet_helpers import APP_PATH, sidebar_about

faction_list = [
    "🧝 Unaffiliated",
    # "🏴 Blackthorne Company",
    "💰 Guild of the Black Sky",
    "⚜️ Catalpa",
    "🍷 Cedar Hill",
    "🧚‍♀️ The Court of Ashes",
    "🧛‍♂️ The Dismissed",
    "👑 Eponore",
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


st.sidebar.title("About")
sidebar_about()

#authenticate users
if st.session_state["authentication_status"]:
    st.info(f"Check out the [User Guide]({APP_PATH}/User%20Guide?tab=Additional%20Characters) for more info.", icon=":material/help:")
    user_data = db.reference("users/").child(st.session_state['username']).get()
    try:
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
                    profile_image = "https://64.media.tumblr.com/ac71f483d395c1ad2c627621617149be/tumblr_o8wg3kqct31uxrf2to1_640.jpg"
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
                        bucket = storage.bucket()
                        for b in bucket.list_blobs(prefix=st.session_state['username']):
                            all_pics = re.compile(fr"^{st.session_state['username']}/{char_to_delete}\.[a-zA-Z]{{3,4}}$")
                            if all_pics.match(b.name):
                                b.delete()
                        db.reference("users/").child("{}/characters/{}".format(st.session_state['username'],char_to_delete)).delete()
                        popup.close()
                        st.rerun()
                    if st.button("I've Changed My Mind"):
                        popup.close()
        else:
            st.warning('No additional characters found', icon=":material/no_accounts:")
            char_name_list = []
    except:
        st.warning('No additional characters found', icon=":material/no_accounts:")
        char_name_list = []
    st.write('### Create Additional Character')
    with st.expander('Add New Character'):
        with st.form('my_form'):
            character_name_input = st.text_input('Character Name', key='form_char', value='')
            path_input = st.selectbox('Path', path_list, key='form_path')
            faction_input = st.selectbox('Faction', faction_list, key='form_faction')
            uploaded_file = st.file_uploader('Upload Profile Picture', type=['png','gif','jpg','jpeg'], key='form_image')
            copy_events = st.checkbox('Copy Main Character Events?')
            if uploaded_file is not None:
                form_image = uploaded_file.getvalue()
                pic_name = '{}.{}'.format(character_name_input,uploaded_file.name.split('.')[1])
                image = ImageCheck.open(io.BytesIO(form_image))
                image.save(pic_name)
            submitted = st.form_submit_button('Generate Character')
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
                    if copy_events:
                        if 'event_info' in user_data.keys():
                            doc_ref.update({
                                "event_info":user_data['event_info']
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
    # st.page_link(st.Page("pages/register_user.py"), label='Register New User', icon="📝")
    # st.page_link(st.Page("pages/forgot_username.py"), label='Forgot Username', icon="👤")
    # st.page_link(st.Page("pages/forgot_password.py"), label='Forgot Password', icon="🔑")

elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
    # st.page_link(st.Page("pages/register_user.py"), label='Register New User', icon="📝")
    # st.page_link(st.Page("pages/forgot_username.py"), label='Forgot Username', icon="👤")
    # st.page_link(st.Page("pages/forgot_password.py"), label='Forgot Password', icon="🔑")