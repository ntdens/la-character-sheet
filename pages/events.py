import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from st_pages import show_pages_from_config, add_page_title, hide_pages
from datetime import date

st.set_page_config(layout='wide')
add_page_title()

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Username', 'Forgot Password', 'User Management'])

event_dict = {
    "☀️ Day Event":'1',
    "⛺️ Campout Event":'2',
    "🎆 Festival Event":'3',
    "🪚 Work Weekend":'1'
}

def df_on_change(df):
    state = st.session_state['df_editor']
    for updates in state["added_rows"]:
           st.session_state["df"].loc[len(st.session_state["df"])] = updates
    for index, updates in state["edited_rows"].items():
        for key, value in updates.items():
            st.session_state["df"].loc[st.session_state["df"].index == index, key] = value
        st.session_state["df"].loc[st.session_state["df"].index == index, "Skill Points"] = st.session_state["df"].loc[st.session_state["df"].index == index, "Event Type"].replace(event_dict).astype(int) + st.session_state["df"].loc[st.session_state["df"].index == index, "NPC"].astype(int) + st.session_state["df"].loc[st.session_state["df"].index == index, "Merchant Overtime"].astype(int) + st.session_state["df"].loc[st.session_state["df"].index == index, "Bonus Skill Points"]


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
    data_df = pd.DataFrame(
        {
            'Event Name' : ['First Event!'],
            'Event Date' : [date(2024, 1, 1)],
            'Event Type' : ["☀️ Day Event"],
            'NPC' : [False],
            'Merchant Overtime': [False],
            'Bonus Skill Points' : [0],
        }
    )
    data_df['Skill Points'] = data_df['Event Type'].replace(event_dict).astype(int) + data_df['NPC'].astype(int) + data_df['Merchant Overtime'].astype(int) + data_df['Bonus Skill Points']
    
    def editor():
        if "df" not in st.session_state:
            st.session_state["df"] = data_df
        st.data_editor(
            st.session_state["df"].reset_index(drop=True),
            key="df_editor",
            column_config={
                "Event Name": st.column_config.TextColumn(
                    help='Name of event',
                    default='New Event'
                ),
                "Event Date" : st.column_config.DateColumn(
                    format="MMMM YYYY",
                ),
                "Event Type": st.column_config.SelectboxColumn(
                    help='Type of Event',
                    options=[
                        "☀️ Day Event",
                        "⛺️ Campout Event",
                        "🎆 Festival Event",
                        "🪚 Work Weekend"
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
            on_change=df_on_change,
            args=[data_df],
        )
    editor()


    

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

with open('./config.yaml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False)