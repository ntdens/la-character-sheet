import json
import streamlit as st
import streamlit.components.v1 as components
import streamlit_authenticator as stauth
from streamlit_extras.grid import grid
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
from sheet_helpers import APP_PATH, sidebar_about
from PIL import Image
import io



faction_list = [
    "🧝 Unaffiliated",
    "🏴 Blackthorne Company",
    "💰 Guild of the Black Sky",
    "⚜️ Catalpa",
    "🍷 Cedar Hill",
    "🧚‍♀️ The Court of Ashes",
    "🧛‍♂️ The Dismissed",
    "👑 Eponore",
    "💀 Geth",
    "❄️ Grimfrost",
    "🌳 The Grove",
    "🍃 The House of Silver Branches",
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
faction_colors = {
    "🧝 Unaffiliated":'burlywood',
    # "🏴 Blackthorne Company":'darkslategray',
    "💰 Guild of the Black Sky":'darkkhaki',
    "👑 Eponore":"yellow",
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
    "🧝 Unaffiliated",
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
    '🩸 Healer',
    '🔮 Mage'
]

def use_calc(path, base, mod, unit):
    tier = tier_df[tier_df['Path'] == path].iloc[0]['Tier']
    use_count = base + eval(str(mod).replace('t', str(tier)))
    return f'{use_count} {unit}', use_count

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
                elif column in ['Profession(s)', 'Organization(s)']:
                    print(list(df.explode(column)[column].unique()))
                    user_list_input = right.multiselect(
                        f"{column}",
                        list(df.explode(column)[column].unique()),
                        default=list(df.explode(column)[column].unique()),
                        key=f'{column}_select'
                    )
                    df = df[df[column].apply(lambda x:any(a in x for a in user_list_input))]
                elif isinstance(df[column], pd.CategoricalDtype) or df[column].nunique() < 10:
                    user_cat_input = right.multiselect(
                        f"{column}",
                        df[column].unique(),
                        default=list(df[column].unique())
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

st.sidebar.title("About")
sidebar_about()

#authenticate users
if st.session_state["authentication_status"]:
    st.info(f"Check out the [User Guide]({APP_PATH}/User%20Guide?tab=Admin%20Zone) for more info.", icon=":material/help:")
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
                tier = get_tier(len(user_events[(user_events['Event Type'] != "🪚 Work Weekend")  & (user_events['Event Type'] != "🗳️ Survey/Misc")]))
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
            if 'professions' in user_data[key].keys():
                prof = ast.literal_eval(user_data[key]['professions'])
                if not prof:
                    prof = None
            else:
                prof = None
            if 'orgs' in user_data[key].keys():
                orgs = ast.literal_eval(user_data[key]['orgs'])
                if not orgs:
                    orgs = None
            else:
                orgs = None
            if 'character_name' in user_data[key].keys():
                character_name = user_data[key]['character_name']
            else:
                character_name = ''
            if 'faction' in user_data[key].keys():
                faction = user_data[key]['faction']
            else:
                faction = ''
            if 'path' in user_data[key].keys():
                path = user_data[key]['path']
            else:
                path = ''
            if 'name' in user_auth[key].keys():
                player = user_auth[key]['name']
            elif 'first_name' in user_auth[key].keys():
                player = user_auth[key]['first_name'] + ' ' + user_auth[key]['last_name']
            else:
                player = ''
            user_table.append({
                'Username':key,
                'Character':character_name,
                'Player':player,
                'Faction':faction,
                'Path':path,
                'Tier':tier,
                'Profession(s)':prof,
                'Organization(s)':orgs,
                'Earned Points':skill_points,
                "Available Points":avail_points,
                'Event Info':event_info
            })
            if 'characters' in user_data[key]:
                for c in user_data[key]['characters']:
                    c_info = user_data[key]['characters'][c]
                    try:
                        user_events = pd.DataFrame(json.loads(c_info['event_info']))
                        user_events.reset_index(drop=True, inplace=True)
                        tier = get_tier(len(user_events[(user_events['Event Type'] != "🪚 Work Weekend")  & (user_events['Event Type'] != "🗳️ Survey/Misc")]))
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
                    if 'professions' in c_info.keys():
                        prof = ast.literal_eval(c_info['professions'])
                    else:
                        prof = None
                    if 'orgs' in c_info.keys():
                        orgs = ast.literal_eval(c_info['orgs'])
                    else:
                        orgs = None
                    user_table.append({
                        'Username':key,
                        'Player':user_auth[key]['name'],
                        'Character':c_info['character_name'],
                        'Faction':c_info['faction'],
                        'Path':c_info['path'],
                        'Tier':tier,
                        'Profession(s)':prof,
                        'Organization(s)':orgs,
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
            st.header("Welcome {} ,  Leader of {}{} !".format(leader_data['Character'].values[0], add_the_string, leader_data['Faction'].values[0]), divider='rainbow')
            user_df = filter_dataframe(user_df)
            st.dataframe(user_df.drop(columns=['Event Info']), hide_index=True, use_container_width=True)
            if not user_df.empty:
                tier_df = user_df.groupby('Tier')['Username'].count().reset_index().rename(columns={'Username':'Players'})
                path_df = user_df.groupby('Path')['Username'].count().reset_index().rename(columns={'Username':'Players'})
                prof_df = user_df.explode('Profession(s)').groupby('Profession(s)')['Username'].nunique().reset_index().rename(columns={'Username':'Players', 'Profession(s)':'Profession'})
                if 'Profession(s)_select' in st.session_state:
                    prof_df = prof_df[prof_df['Profession'].isin(st.session_state['Profession(s)_select'])]
                org_df = user_df.explode('Organization(s)').groupby('Organization(s)')['Username'].nunique().reset_index().rename(columns={'Username':'Players', 'Organization(s)':'Organization'})
                if 'Organization(s)_select' in st.session_state:
                    org_df = org_df[org_df['Organization'].isin(st.session_state['Organization(s)_select'])]
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
                    px.bar(path_df, x='Path', y='Players', title='Number of Players by Path', category_orders={'Path':path_list}).update_layout(
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
                    px.bar(prof_df, x='Profession', y='Players', title='Number of Players by Profession').update_layout(
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
                    px.bar(org_df, x='Organization', y='Players', title='Number of Players by Organization').update_layout(
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
                            user_events = user_events[(user_events['Event Type'] != "🪚 Work Weekend")  & (user_events['Event Type'] != "🗳️ Survey/Misc")]
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
            try:
                character_choice = st.selectbox('Select User:', user_df['Username'].unique(), key='sheet_user', index=list(user_df['Username'].unique()).index(st.session_state['username']))
            except:
                character_choice = st.selectbox('Select User:', user_df['Username'], key='sheet_user')
            try:
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
                try:
                    bio = character_data['bio']
                except:
                    bio = ''
                known_data = df[df['Skill Name'].isin(known)]
                use_df = pd.read_excel('Skill Use.xlsx')
                char_df = user_df[(user_df['Username'] == character_choice) & (user_df['Character'] == char_name)]
                tier_df = pd.DataFrame({'Path':['Warrior', 'Rogue', 'Healer', 'Mage', 'Bard', 'Artificer', char_df['Path'].values[0].split(' ')[1]], 'Tier':[0,0,0,0,0,0, char_df['Tier'].values[0]]})
                tier_df = pd.concat([known_data, tier_df]).groupby('Path')['Tier'].max().reset_index()
                use_df[['Uses', 'Use Count']] = pd.DataFrame(use_df.apply(lambda x:use_calc(x['Path'], x['Base'], x['Tier Modifer'], x['Unit']), axis=1).to_list())
                use_df = use_df[['Skill Name', 'Path', 'Tier', 'Uses', 'Use Count']]
                known_data = pd.merge(known_data, use_df, on=['Skill Name','Path','Tier'], how='left')
                display_data = known_data.sort_values('Use Count', ascending=False).drop_duplicates('Skill Name').sort_index().sort_values('Tier')[['Skill Name', 'Uses', 'Description', 'Limitations', 'Phys Rep', 'Augment', 'Special']].copy()
                try:
                    image_location = character_data['pic_name']
                    bucket = storage.bucket()
                    blob = bucket.blob(image_location)
                    profile_image = Image.open(io.BytesIO(blob.download_as_bytes()))
                except:
                    profile_image = "https://64.media.tumblr.com/ac71f483d395c1ad2c627621617149be/tumblr_o8wg3kqct31uxrf2to1_640.jpg"
                with st.container(border=True):
                    col1, col2 = st.columns([6,4])
                    with col1:
                        st.image(profile_image, use_container_width=True)
                    with col2:
                        char_df = user_df[(user_df['Username'] == character_choice) & (user_df['Character'] == char_name)]
                        prof_data = char_df['Profession(s)'].values[0]
                        if isinstance(prof_data,list):
                            prof_data = ' , '.join(prof_data)
                        org_data = char_df['Organization(s)'].values[0]
                        if isinstance(prof_data,list):
                            org_data = ' , '.join(prof_data)
                        player_data = pd.DataFrame({
                            'Category': ['Character  : ','Player  : ','Path  : ','Faction  : ','Profession(s)  : ','Organization(s)  : ','Tier  : ','Skill Points  : '],
                            'Information': [character_data['character_name'],char_df['Player'].values[0],char_df['Path'].values[0],char_df['Faction'].values[0],prof_data,org_data,char_df['Tier'].values[0],char_df['Available Points'].values[0]]
                                            })
                        for index, row in player_data.iterrows():
                            st.subheader(f'{row.Category}   {row.Information}', divider='orange')
                        # st.dataframe(player_data, hide_index=True, use_container_width=True)
                        bucket = storage.bucket()
                        if character_data['faction'] not in ["🧝 Unaffiliated","🤖 NPC"]:
                            blob = bucket.blob("faction_logos/{}.jpg".format(character_data['faction']))
                            logo = blob.download_as_bytes()
                            st.image(logo, use_container_width=True)
                        else:
                            blob = bucket.blob("faction_logos/la_logo.png")
                            logo = blob.download_as_bytes()
                            st.image(logo, use_container_width=True)
                    if st.session_state['username'] in st.secrets['admins']:
                        st.markdown("<u><h2 style='text-align: center;'>Biography</h2></u>", unsafe_allow_html=True)
                        st.write(bio)
                        st.markdown("<u><h2 style='text-align: center;'>Known Skills</h2></u>", unsafe_allow_html=True)
                        st.dataframe(display_data, hide_index=True, use_container_width=True)
            except:
                st.info("Data does not exist for this user")
        with tab3:
            try:
                character_choice = st.selectbox('Select User:', user_df['Username'].unique(), key='event_user', index=list(user_df['Username']).index(st.session_state['username']))
            except:
                character_choice = st.selectbox('Select User:', user_df['Username'], key='event_user')
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
        st.error('Not an admin. Access denied. Whomp whomp.',icon=':material/sentiment_sad:')
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

elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')