import json
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from st_pages import show_pages_from_config, add_page_title, hide_pages
from datetime import date
import firebase_admin
from firebase_admin import credentials, db
from sheet_helpers import APP_PATH, sidebar_about

add_page_title(layout='wide')

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Username', 'Forgot Password', 'User Management'])

event_dict = {
    "☀️ Day Event":1,
    "⛺️ Campout Event":2,
    "🎆 Festival Event":3,
    "👾 Virtual Event":1,
    "🪚 Work Weekend":1,
    "🗳️ Survey/Misc":1
}

def df_on_change(df):
    state = st.session_state['df_editor']
    for updates in state["added_rows"]:
        st.session_state["df"].loc[len(st.session_state["df"])] = updates
    for index, updates in state["edited_rows"].items():
        for key, value in updates.items():
            st.session_state["df"].loc[st.session_state["df"].index == index, key] = value
        st.session_state["df"].loc[st.session_state["df"].index == index, "Skill Points"] = st.session_state["df"].loc[st.session_state["df"].index == index, "Event Type"].replace(event_dict).astype(int) + st.session_state["df"].loc[st.session_state["df"].index == index, ["NPC","Merchant Overtime"]].astype(int).max(axis=1) + st.session_state["df"].loc[st.session_state["df"].index == index, "Bonus Skill Points"]
    for update in state['deleted_rows']:
        st.session_state["df"] = st.session_state["df"].drop(update)
    st.session_state["df"].reset_index(drop=True, inplace=True)


if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase"], strict=False)
    creds = credentials.Certificate(key_dict)
    defualt_app = firebase_admin.initialize_app(creds, {
        'databaseURL': 'https://la-character-sheets-default-rtdb.firebaseio.com',
        'storageBucket':'la-character-sheets.appspot.com'
    })

with open( "style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>', unsafe_allow_html= True)

config = db.reference("auth").get()

st.sidebar.title("About")
sidebar_about()

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
    st.info(f"Check out the [User Guide]({APP_PATH}/User%20Guide?tab=Events) for more info. Skill Points column only updates once events are saved.", icon=":material/help:")
    try:
        user_data = db.reference("users/").child(st.session_state['username']).get()
        char_path = st.session_state['username']
        if 'characters' in user_data.keys():
            char_select = st.selectbox('Pick Character', options=[user_data['character_name']] + list(user_data['characters']))
            if char_select != user_data['character_name']:
                user_data = user_data['characters'][char_select]
                char_path = "{}/characters/{}".format(st.session_state['username'], char_select)
        user_events = user_data['event_info']
        data_df = pd.DataFrame(json.loads(user_events))
        data_df.reset_index(drop=True, inplace=True)
        try:
            data_df['Event Date'] = pd.to_datetime(data_df['Event Date'], format="%B %Y")
        except:
            pass
        try:
            data_df['Event Date'] = pd.to_datetime(data_df['Event Date'], unit='ms')
        except:
            pass
    except:
        data_df = pd.DataFrame(
            {
                'Event Name' : ['First Event!'],
                'Event Date' : [date(2024, 1, 1)],
                'Event Type' : ["☀️ Day Event"],
                'NPC' : [False],
                'Merchant Overtime': [False],
                'Bonus Skill Points' : [0],
                'Skill Points': [1]
            }
        )
    data_df = data_df.sort_values('Event Date', ascending=True).reset_index(drop=True)
    with st.form('event_data'):
        event_df = st.data_editor(
        data_df,
        key="df_editor",
        column_config={
            "Event Name": st.column_config.TextColumn(
                help='Name of event',
            ),
            "Event Date": st.column_config.DateColumn(
                format="MMMM YYYY"
            ),
            "Event Type": st.column_config.SelectboxColumn(
                help='Type of Event',
                options=[
                    "☀️ Day Event",
                    "⛺️ Campout Event",
                    "🎆 Festival Event",
                    "👾 Virtual Event",
                    "🪚 Work Weekend",
                    "🗳️ Survey/Misc"
                ],
                width='medium',
                default="☀️ Day Event"
            ),
            'NPC': st.column_config.CheckboxColumn(default=False),
            'Merchant Overtime': st.column_config.CheckboxColumn(default=False),
            'Bonus Skill Points' : st.column_config.NumberColumn(
                help='Any additional SP earned on top of NPC and Merchant bonus points',
                step=1,
                default=0
            ),
            "Skill Points":st.column_config.NumberColumn(
                default=1,
                disabled=True
            )
        },
        num_rows='dynamic',
        height=950,
        use_container_width=True
        )
        submit_events = st.form_submit_button('Save Events')
    if submit_events:
        if event_df['Event Date'].isnull().any():
            st.warning('Please fill in all dates')
        else:
            event_df['Skill Points'] = event_df["Event Type"].replace(event_dict).astype(int) + event_df[["NPC","Merchant Overtime"]].astype(int).max(axis=1) + event_df["Bonus Skill Points"]
            doc_ref = db.reference("users/").child(char_path)
            doc_ref.update({
                "event_info":event_df.to_json()
            })
            st.success('Events saved to database')
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
