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
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype,
)

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
    "🧚‍♀️ The Court of Ashes",
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
    "🕊️ The White Ravens"
]
faction_colors = {
    "🧝 Unaffilated":'burlywood',
    "🏴 Blackthorne Company":'black',
    "💰 Guild of the Black Sky":'darkkhaki',
    "🛡 Eponore":"yellow",
    "⚜️ Catalpa":"red",
    "🍷 Cedar Hill":"fuscia",
    "🧚‍♀️ The Court of Ashes":'purple',
    "🧛‍♂️ The Dismissed":'firebrick',
    "💀 Geth":'gray',
    "❄️ Grimfrost":"deepskyblue",
    "🌳 The Grove":"green",
    "🌙 The Irregulars":'navy',
    "⚖️ The Order":'black',
    "🎪 Prismatic Troupe":'lime',
    "⚔️ Sunsteel Company":"darkseagreen",
    "🦁 Kult of Tharros":"crimson",
    "🐴 Vidarian Khanate":"maroon",
    "🏹 The Wardens":"olive",
    "🕊️ The White Ravens":"gainsboro"
}

path_list = [
    '🗡 Warrior',
    '🪤 Rogue',
    '🩹 Healer',
    '🔮 Wizard'
]

def get_tier(events):
    return floor((sqrt(8*events)-1)/2)

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
            user_df = filter_dataframe(user_df)
            st.dataframe(user_df, hide_index=True)
            tier_df = user_df.groupby('Tier')['Username'].count().reset_index().rename(columns={'Username':'Players'})
            st.plotly_chart(
                px.bar(tier_df, x='Tier', y='Players', title='Number of Players by Tier').update_layout(
                    xaxis = dict(
                        tickmode = 'array',
                        tickvals = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                        ticktext = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five','Six', 'Seven','Eight', 'Nine', 'Ten']
                    ),
                    yaxis = dict(
                            tickmode = 'linear',
                            tick0 = 0,
                            dtick = 1
                    )
                ).update_traces(marker_color='rgb(230,171,2)')
            )
            st.plotly_chart(
                px.histogram(user_df, x='Earned Points', nbins=20, title='Points Earned by Players').update_layout(
                        yaxis = dict(
                            tickmode = 'linear',
                            tick0 = 0,
                            dtick = 1,
                            title='Players'
                        )
                    ).update_traces(marker_color='rgb(230,171,2)')
                )
            st.plotly_chart(
                px.histogram(user_df, x='Available Points', nbins=20, title='Points Available by Players').update_layout(
                        yaxis = dict(
                            tickmode = 'linear',
                            tick0 = 0,
                            dtick = 1,
                            title='Players'
                        )
                    ).update_traces(marker_color='rgb(230,171,2)')
                )
            player_events = []
            for player in user_df['Username']:
                try:
                    user_events = pd.DataFrame(json.loads(user_data[player]['event_info']))
                    user_events.reset_index(drop=True, inplace=True)
                    user_events = user_events[user_events['Event Type'] != "🪚 Work Weekend"]
                    try:
                        user_events['Event Date'] = pd.to_datetime(user_events['Event Date'], format="%B %Y")
                    except:
                        pass
                    try:
                        user_events['Event Date'] = pd.to_datetime(user_events['Event Date'], unit='ms')
                    except:
                        pass
                    player_events.append(pd.DataFrame({'Date':list(user_events['Event Date']),'Player':player}))
                except:
                    pass
            attend = pd.concat(player_events)
            attend['Date'] = attend.Date - pd.offsets.MonthEnd(0) - pd.offsets.MonthBegin(1)
            attend = attend.groupby('Date').nunique().reset_index()
            st.plotly_chart(
                px.line(attend, x='Date', y='Player', title='Attendance Over Time').update_layout(
                        yaxis = dict(
                            tickmode = 'linear',
                            dtick = 1,
                            title = 'Players'
                        )
                    ).update_traces(line_color='rgb(230,171,2)')
            )
            
            if st.session_state['username'] in st.secrets['admins']:
                faction_df = user_df.groupby('Faction')['Username'].count().reset_index().rename(columns={'Username':'Players'})
                st.plotly_chart(
                    px.bar(faction_df, y='Faction', x='Players', title='Number of Players by Faction', orientation='h', color='Faction', color_discrete_map=faction_colors).update_layout(
                        xaxis = dict(
                            tickmode = 'linear',
                            tick0 = 0,
                            dtick = 1
                        ),
                        yaxis = dict(
                            tickmode = 'array',
                            tickvals = faction_list,
                            ticktext = faction_list
                        ),
                        showlegend = False
                    )
                )

        with tab2:
            df = pd.read_excel('Skills_Table.xlsx')
            character_choice = st.selectbox('Select User:', user_df['Username'], key='sheet_user', index=list(user_df['Username']).index(st.session_state['username']))
            try:
                character_data = user_data[character_choice]
                try:
                    known = ast.literal_eval(character_data['known'])
                except:
                    known = []
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
                        'Information': [character_data['character_name'],character_data['name'],character_data['path'],character_data['faction'],user_df[user_df['Username'] == character_choice]['Tier'].values[0],user_df[user_df['Username'] == character_choice]['Available Points'].values[0]]
                                        })
                    my_grid.dataframe(player_data, hide_index=True, use_container_width=True)
                    my_grid.dataframe(display_data, hide_index=True, use_container_width=True)
            except:
                st.info("Data does not exist for this user")
        with tab3:
            character_choice = st.selectbox('Select User:', user_df['Username'], key='event_user', index=list(user_df['Username']).index(st.session_state['username']))
            try:
                character_data = user_data[character_choice]
                user_events = pd.DataFrame(json.loads(character_data['event_info']))
                user_events.reset_index(drop=True, inplace=True)
                try:
                    user_events['Event Date'] = pd.to_datetime(user_events['Event Date'], format="%B %Y").apply(lambda x: x.strftime("%B %Y"))
                except:
                    pass
                try:
                    user_events['Event Date'] = pd.to_datetime(user_events['Event Date'], unit='ms').apply(lambda x: x.strftime("%B %Y"))
                except:
                    pass
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