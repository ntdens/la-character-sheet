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
    # "🏴 Blackthorne Company",
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
    # "🏴 Blackthorne Company":'black',
    "💰 Guild of the Black Sky":'darkkhaki',
    "🛡 Eponore":"yellow",
    "⚜️ Catalpa":"red",
    "🍷 Cedar Hill":"fuchsia",
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

add_the = [
    "🧝 Unaffilated",
    # "🏴 Blackthorne Company",
    "💰 Guild of the Black Sky",
    "🎪 Prismatic Troupe",
    "⚔️ Sunsteel Company",
    "🦁 Kult of Tharros",
    "🐴 Vidarian Khanate",   
]

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
            if column != "Event Info":
                left, right = st.columns((1, 20))
                if is_numeric_dtype(df[column]):
                    _min = df[column].min()
                    _max = df[column].max()
                    if _min != _max:
                        if not df.empty:
                            user_num_input = right.slider(
                                f"{column}",
                                min_value=_min,
                                max_value=_max,
                                value=(_min, _max),
                                step=1,
                            )
                            df = df[df[column].between(*user_num_input, inclusive='both')]
                # Treat columns with < 10 unique values as categorical
                elif isinstance(df[column], pd.CategoricalDtype) or df[column].nunique() < 10:
                    user_cat_input = right.multiselect(
                        f"{column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]
                elif is_datetime64_any_dtype(df[column]):
                    user_date_input = right.date_input(
                        f"{column}",
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
                        f"Search in {column}",
                    )
                    if user_text_input:
                        df = df[df[column].astype(str).str.lower().str.contains(user_text_input.lower())]

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
    if st.session_state['username'] in (st.secrets['admins'] + list(st.secrets['faction_leaders'])):
        if st.session_state['username'] in list(st.secrets['faction_leaders']):
            faction_filter = st.secrets['faction_leaders'][st.session_state['username']]
        else:
            faction_filter = None
        user_data = db.reference("users/").get()
        user_auth = db.reference("auth").child('credentials/usernames/').get()
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
                event_info = user_data[key]['event_info']
            except:
                skill_points = 0
                tier = 0
                avail_points = skill_points
                event_info = "{}"
            try:
                user_table.append({
                    'Username':key,
                    'Player':user_auth[key]['name'],
                    'Character':user_data[key]['character_name'],
                    'Faction':user_data[key]['faction'],
                    'Path':user_data[key]['path'],
                    'Tier':tier,
                    'Earned Points':skill_points,
                    "Available Points":avail_points,
                    'Event Info':event_info
                })
            except:
                pass
            if 'characters' in user_data[key]:
                for c in user_data[key]['characters']:
                    c_info = user_data[key]['characters'][c]
                    try:
                        user_events = pd.DataFrame(json.loads(c_info['event_info']))
                        user_events.reset_index(drop=True, inplace=True)
                        tier = get_tier(len(user_events[user_events['Event Type'] != "🪚 Work Weekend"]))
                        skill_points = int(user_events["Skill Points"].sum())
                        try:
                            avail_points = int(user_events["Skill Points"].sum()) - int(c_info['point_spend'])
                        except:
                            avail_points = skill_points
                        event_info = c_info['event_info']
                    except:
                        skill_points = 0
                        tier = 0
                        avail_points = skill_points
                        event_info = "{}"
                    user_table.append({
                        'Username':key,
                        'Player':user_auth[key]['name'],
                        'Character':c_info['character_name'],
                        'Faction':c_info['faction'],
                        'Path':c_info['path'],
                        'Tier':tier,
                        'Earned Points':skill_points,
                        "Available Points":avail_points,
                        'Event Info': event_info
                    })
        user_df = pd.DataFrame(user_table)
        user_df = user_df[user_df['Faction'] != "🤖 NPC"]
        if faction_filter != None:
            user_df = user_df[user_df['Faction'] == faction_filter]
        with tab1:
            leader_data = user_df[user_df['Username'] == st.session_state['username']]
            if leader_data['Faction'].values[0] in add_the:
                add_the_string = 'the '
            else:
                add_the_string = ''
            st.write("## Welcome {}, Leader of {}{}".format(leader_data['Character'].values[0], add_the_string, leader_data['Faction'].values[0]))
            user_df = filter_dataframe(user_df)
            st.dataframe(user_df.drop(columns=['Event Info']), hide_index=True, use_container_width=True)
            tier_df = user_df.groupby('Tier')['Username'].count().reset_index().rename(columns={'Username':'Players'})
            path_df = user_df.groupby('Path')['Username'].count().reset_index().rename(columns={'Username':'Players'})
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
                    ),
                    plot_bgcolor = 'rgba(0, 0, 0, 0)',
                    paper_bgcolor= 'rgba(0, 0, 0, 0)'
                ).update_traces(marker_color='rgb(230,171,2)')
            , use_container_width=True)
            st.plotly_chart(
                px.bar(path_df, x='Path', y='Players', title='Number of Players by Path').update_layout(
                    yaxis = dict(
                            tickmode = 'linear',
                            tick0 = 0,
                            dtick = 1
                    ),
                    plot_bgcolor = 'rgba(0, 0, 0, 0)',
                    paper_bgcolor= 'rgba(0, 0, 0, 0)'
                ).update_traces(marker_color='rgb(230,171,2)')
            , use_container_width=True)
            st.plotly_chart(
                px.histogram(user_df, x='Earned Points', nbins=20, title='Points Earned by Players').update_layout(
                        yaxis = dict(
                            tickmode = 'linear',
                            tick0 = 0,
                            dtick = 1,
                            title='Players'
                        ),
                        plot_bgcolor = 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)'
                    ).update_traces(marker_color='rgb(230,171,2)')
                , use_container_width=True)
            st.plotly_chart(
                px.histogram(user_df, x='Available Points', nbins=20, title='Points Available by Players').update_layout(
                        yaxis = dict(
                            tickmode = 'linear',
                            tick0 = 0,
                            dtick = 1,
                            title='Players'
                        ),
                        plot_bgcolor = 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)'
                    ).update_traces(marker_color='rgb(230,171,2)')
                , use_container_width=True)
            player_events = []
            for _, row in user_df.iterrows():
                try:
                    user_events = pd.DataFrame(json.loads(row['Event Info']))
                    if not user_events.empty:
                        user_events = user_events[user_events['Event Type'] != "🪚 Work Weekend"]
                        try:
                            user_events['Event Date'] = pd.to_datetime(user_events['Event Date'], format="%B %Y")
                        except:
                            pass
                        try:
                            user_events['Event Date'] = pd.to_datetime(user_events['Event Date'], unit='ms')
                        except:
                            pass
                        player_events.append(pd.DataFrame({'Date':list(user_events['Event Date']),'Player':row['Username'], 'Faction':row['Faction']}))
                except:
                    pass
            attend = pd.concat(player_events)
            attend['Date'] = attend.Date - pd.offsets.MonthEnd(0) - pd.offsets.MonthBegin(1)
            attend = attend.groupby('Date')['Player'].nunique()
            idx = pd.date_range(attend.index.min(), attend.index.max(), freq='1MS')
            attend = attend.reindex(idx, fill_value=0).reset_index().rename(columns={'index':'Date'})
            st.plotly_chart(
                px.line(attend, x='Date', y='Player', title='Attendance Over Time').update_layout(
                        yaxis = dict(
                            tickmode = 'linear',
                            dtick = 1,
                            title = 'Players',
                            rangemode='tozero'
                        ),
                        plot_bgcolor = 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)'
                    ).update_traces(line_color='rgb(230,171,2)')
            , use_container_width=True)
            
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
                        showlegend = False,
                        plot_bgcolor = 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)'
                    )
                , use_container_width=True)
                faction_attend = pd.concat(player_events)
                faction_attend['Date'] = faction_attend.Date - pd.offsets.MonthEnd(0) - pd.offsets.MonthBegin(1)
                faction_attend = faction_attend.groupby(['Faction','Date']).nunique().reset_index()
                filled_dates = []
                for f in faction_attend['Faction'].unique():
                    fadf = faction_attend[faction_attend['Faction'] == f].set_index('Date')
                    idx = pd.date_range(fadf.index.min(), fadf.index.max(), freq='1MS')
                    fadf = fadf.reindex(idx, fill_value=0).reset_index().rename(columns={'index':'Date'})
                    fadf['Faction'] = f
                    filled_dates.append(fadf)
                faction_attend = pd.concat(filled_dates)
                st.plotly_chart(
                    px.line(faction_attend, y='Player', x='Date', title='Attendance by Faction', line_group='Faction', color='Faction', color_discrete_map=faction_colors).update_layout(
                        yaxis = dict(
                            tickmode = 'linear',
                            dtick = 1,
                            title = 'Players',
                            rangemode='tozero'
                        ),
                        plot_bgcolor = 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)'
                    )
                , use_container_width=True)

        with tab2:
            df = pd.read_excel('Skills_Table.xlsx')
            character_choice = st.selectbox('Select User:', user_df['Username'], key='sheet_user', index=list(user_df['Username'].unique()).index(st.session_state['username']))
            # try:
            character_data = user_data[character_choice]
            char_name = character_data['character_name']
            if 'characters' in character_data.keys():
                char_select = st.selectbox('Pick Character', options=[character_data['character_name']] + list(character_data['characters']), key='sheet_char')
                if char_select != character_data['character_name']:
                    character_data = character_data['characters'][char_select]
                    char_path = "{}/characters/{}".format(st.session_state['username'], char_select)
                    char_name = character_data['character_name']
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
                profile_image = "https://64.media.tumblr.com/ac71f483d395c1ad2c627621617149be/tumblr_o8wg3kqct31uxrf2to1_640.jpg"
            with st.container(border=True):
                col1, col2 = st.columns([6,4])
                with col1:
                    st.container(border=True).image(profile_image)
                with col2:
                    player_data = pd.DataFrame({
                        'Category': ['Character: ','Player: ','Path: ','Faction: ','Tier: ','Skill Points: '],
                        'Information': [character_data['character_name'],user_df[(user_df['Username'] == character_choice) & (user_df['Character'] == char_name)]['Player'].values[0],character_data['path'],character_data['faction'],user_df[(user_df['Username'] == character_choice) & (user_df['Character'] == char_name)]['Tier'].values[0],user_df[(user_df['Username'] == character_choice) & (user_df['Character'] == char_name)]['Available Points'].values[0]]
                                        })
                    st.dataframe(player_data, hide_index=True, use_container_width=True)
                    bucket = storage.bucket()
                    if character_data['faction'] != "🧝 Unaffilated" or "🤖 NPC":
                        blob = bucket.blob("faction_logos/{}.jpg".format(character_data['faction']))
                        logo = blob.download_as_bytes()
                        st.image(logo)
                    else:
                        blob = bucket.blob("faction_logos/la_logo.jpg")
                        logo = blob.download_as_bytes()
                        st.image(logo)
                st.dataframe(display_data, hide_index=True, use_container_width=True)
            # except:
            #     st.info("Data does not exist for this user")
        with tab3:
            character_choice = st.selectbox('Select User:', user_df['Username'].unique(), key='event_user', index=list(user_df['Username']).index(st.session_state['username']))
            try:
                character_data = user_data[character_choice]
                if 'characters' in character_data.keys():
                    char_select = st.selectbox('Pick Character', options=[character_data['character_name']] + list(character_data['characters']), key='event_char')
                    if char_select != character_data['character_name']:
                        character_data = character_data['characters'][char_select]
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
                st.dataframe(user_events, hide_index=True, use_container_width=True, height=950)
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