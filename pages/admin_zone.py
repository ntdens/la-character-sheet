import json
import streamlit as st
import streamlit.components.v1 as components
import streamlit_authenticator as stauth
from streamlit_extras.grid import grid
from st_pages import show_pages_from_config, add_page_title, hide_pages
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db, storage
from math import floor, sqrt
import ast
import smtplib
from email.mime.text import MIMEText
import plotly.express as px

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
    if st.session_state['username'] in (st.secrets['admins'] or list(st.secrets['faction_leaders'])):
        if st.session_state['username'] in list(st.secrets['faction_leaders']):
            faction_filter = st.secrets['faction_leaders'][st.session_state['username']]
        else:
            faction_filter = None
        user_data = db.reference("users/").get()
        tab1, tab2,tab3 = st.tabs(['Player List', 'Character View', 'Event View'])
        user_table = []
        for key in user_data.keys():
            try:
                user_events = pd.DataFrame(json.loads(user_data[key]['event_info']))
                user_events.reset_index(drop=True, inplace=True)
                tier = get_tier(len(user_events[user_events['Event Type'] != "🪚 Work Weekend"]))
                skill_points = int(user_events["Skill Points"].sum())
                try:
                    avail_points = int(user_events["Skill Points"].sum()) - int(user_data[key]['point_spend'])
                except:
                    avail_points = skill_points
            except:
                skill_points = 0
                tier = 0
                avail_points = skill_points

            user_table.append({
                'Username':key,
                'Player':user_data[key]['name'],
                'Character':user_data[key]['character_name'],
                'Faction':user_data[key]['faction'],
                'Path':user_data[key]['path'],
                'Tier':tier,
                'Earned Points':skill_points,
                "Available Points":avail_points
            })
        user_df = pd.DataFrame(user_table)
        if faction_filter != None:
            user_df = user_df[user_df['Faction'] == faction_filter]
        with tab1:
            leader_data = user_df[user_df['Username'] == st.session_state['username']]
            st.write("## Welcome {}, Leader of {}".format(leader_data['Character'].values[0],leader_data['Faction'].values[0]))
            st.dataframe(user_df, hide_index=True)
            chart_grid = grid(3)
            chart_grid.plotly_chart(
                px.histogram(user_df, x='Tier', category_orders=dict(Tier=list(range(0,10))))
            )
        with tab2:
            df = pd.read_excel('Skills_Table.xlsx')
            character_choice = st.selectbox('Select User:', user_df['Username'], key='sheet_user', index=list(user_df['Username']).index(st.session_state['username']))
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
            character_choice = st.selectbox('Select User:', user_df['Username'], key='event_user', index=list(user_df['Username']).index(st.session_state['username']))
            try:
                character_data = user_data[character_choice]
                user_events = pd.DataFrame(json.loads(character_data['event_info']))
                user_events.reset_index(drop=True, inplace=True)
                st.dataframe(user_events, hide_index=True, use_container_width=True)
            except:
                st.info("Data does not exist for this user")
    else:
        st.warning('Not an admin. Access denied. Whomp whomp.')
        st.write("### Request Admin Access")
        with st.form('admin_access'):
            name_input = st.text_input('Name', value=st.session_state['name'], key='admin_name')
            reason_input = st.text_input('Reason', key='admin_reason')
            submitted = st.form_submit_button('Submit Request')
            if submitted:
                st.info('Request email sent.')
                sender_email = "larpadventerurescharactersheet@gmail.com"  # Enter your address
                receiver_email = "larpadventerurescharactersheet@gmail.com"  # Enter receiver address
                password = st.secrets['email_password']
                body = """
                Username: {}
                Name: {}
                Reason: {}
                """.format(st.session_state['username'], name_input, reason_input)
                msg = MIMEText(body)
                msg['Subject'] = 'LARP Character Sheet Admin Request'
                msg['From'] = "larpadventerurescharactersheet@gmail.com"
                msg['To'] = "larpadventerurescharactersheet@gmail.com"
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
                server.quit()
        st.write("### Request Faction Leader Access")
        with st.form('faction_access'):
            name_input = st.text_input('Name', value=st.session_state['name'], key='faction_name')
            faction_input = st.selectbox('Faction', faction_list, key='form_faction')
            submitted = st.form_submit_button('Submit Request')
            if submitted:
                st.info('Request email sent.')
                sender_email = "larpadventerurescharactersheet@gmail.com"  # Enter your address
                receiver_email = "larpadventerurescharactersheet@gmail.com"  # Enter receiver address
                password = st.secrets['email_password']
                body = """
                Username: {}
                Name: {}
                Faction: {}
                """.format(st.session_state['username'], name_input, faction_input)
                msg = MIMEText(body)
                msg['Subject'] = 'LARP Character Sheet Faction Admin Request'
                msg['From'] = "larpadventerurescharactersheet@gmail.com"
                msg['To'] = "larpadventerurescharactersheet@gmail.com"
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
                server.quit()
                
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