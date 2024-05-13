import json
import streamlit as st
import streamlit_authenticator as stauth
from st_pages import show_pages_from_config, add_page_title, hide_pages
from streamlit_modal import Modal
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db, storage
from math import floor, sqrt
from sheet_helpers import APP_PATH


add_page_title(layout='wide')

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Username', 'Forgot Password', 'User Management'])

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

def link_create(page):
    return f'<a href="{APP_PATH}{page.replace(" ","%20")}" target="_self">{page}</a>'

def material_icon(icon_name):
    return f'<i class="material-icons">{icon_name}</i>'

#login widget
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

st.sidebar.title("About")
st.sidebar.markdown(
    """
    **This app is maintained by Nate Densmore (Kython). Please reach out to him if you have 
    any questions or concerns. This app is a volunteer passion project, not an official product 
    of LARP Adventures.**
"""
)


#authenticate login
authenticator.login()

#authenticate users
if st.session_state["authentication_status"]:
    list_of_tabs = [
        'Getting Started',
        'Character Sheet',
        'Events',
        'Skills',
        'Additional Characters',
        'Profile',
        'Admin Zone'
        ]
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(list_of_tabs)
    with tab1:
        st.header('Getting Started', divider='orange')
        st.subheader('Welcome!')
        st.markdown(
            '''
                Hello there, and welcome to the LARP Adventures Character Sheet creator!
                This app is designed to help make the process of creating, maintaining, and tracking
                your character as easy as possible. This guide will walk you through each of the steps in creating
                your first character, as well as more information on each section of the app.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Adding Events')
        st.markdown(
            f'''
                One of the first things to do is record what events you have been to. You can do this over in the
                {link_create('Events')} section of the app. If you are a new player, simply record the name, date and type of
                event you are going to/just came back from, and hit the Save Events button. If you are a more seasoned player, 
                add all the events you have been to. This is important for calculating your Tier and Skill Point total.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Creating Your Character')
        st.markdown(
            f'''
                Once your events are all recorded, it's time to head over to the <a href="{APP_PATH}" target="_self">Character Sheet</a>
                page. This page is divided into three tabs. The first tab holds your completed character sheet. The second tab is where you
                actually create and edit your character. It is here you should go next. Enter your character name, path, faction, and even 
                upload a picture if you wish!
            '''
        ,unsafe_allow_html=True)
        st.subheader('Adding Skills')
        st.markdown(
            f'''
                After creating your character, you can start adding in your skills. The skills you can take are based on your 
                Tier, Path, Available Skill Points, and which skills you have taken (learn more about these rules on the [LARP Adventures
                Wiki](https://www.legendkeeper.com/app/cldqg1nj1yesa08919vutosks/cldqwqv13009d033cx0ouo7sf/)). If this is your first event
                and are Tier 0, you will additionally be limited to only picking up three skills to start with.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Using Your Character Sheet')
        st.markdown(
            f'''
                Once your skills are added, your character sheet is ready to be viewed and used! On the Character Sheet tab you can view your
                character with all of the information you have entered. Here you can see the character image you chose, character name, player name, 
                faction, tier, current available skill points, and all the skills your character knows. You can also export your character into
                a PDF if you so desire.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Wrapping Up')
        st.markdown(
            f'''
                And that's all you need to know to get started! Hopefully this tool becomes a helpful resource for maintaining and building your 
                characters. Feel free to explore the rest of the app, the rest of this guide, create {link_create('Additional Characters')} and 
                just have fun!
            '''
        ,unsafe_allow_html=True)
    with tab2:
        st.header('Character Sheet', divider='orange')
        st.subheader('Selecting Your Character')
        st.markdown(
            f'''
                If you have created any {link_create('Additional Characters')}, at the top of your page you will see a drop down to select
                which character you want to view. If you do not have any additional characters there will be no dropdown and only
                your main character will be shown. Your main character is always shown by defualt.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Character Sheet Tab')
        st.markdown(
            f'''
                This is the main focus of the app, bringing are your info together into one character sheet. Here you can see most of your 
                relevant character information in one place, as well as export your info for offline use or to print out. There are three 
                types of character sheets you can generate for PDF: One that has just your photo and basic information, one that also includes 
                your skill list, and one that includes your skills and events. The buttons to generate these are located on the right side beneath
                the faction emblem. Once your PDF is generated, a new button will appear prompting you to download the Character Sheet. For the 
                Known Skills table you can double click on any cell to read the full contents. You can search the table by hitting the 
                {material_icon("search")} button in the upper right hand corner. You can also download the table as a csv by hitting the
                {material_icon("download")} button in the same location.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Edit Character Tab')
        st.markdown(
            f'''
                Here is where you can update your character's name, faction, path, and upload an image for your character sheet. Currently
                only accepting png, jpg, and gif image types. If you change your path, you will lose all current known skills and point spend
                and will have to rebuild your skills from the beginning. 
            '''
        ,unsafe_allow_html=True)
        st.subheader('Add Skills Tab')
        st.markdown(
            f'''
                This is where you add/remove skills to your character. The skills you can add are based off of your path, tier, skill points 
                and what skills you have earned. You can find a complete list of skills either on the {link_create("Skills")} page or by 
                heading over to the [LARP Adventures Wiki](https://www.legendkeeper.com/app/cldqg1nj1yesa08919vutosks/cldqwqv13009d033cx0ouo7sf/). 
                Both the Pick New Skill and Pick Skill To Remove dropdowns are searchable. There is also a table of skills you have available to you
                 at the bottom of the page you can filter and explore.
            '''
        ,unsafe_allow_html=True)   
    # st.markdown(
    #     f'''
    #         Go to the <a href="{APP_PATH}/User%20Guide#adding-events" target="_self">User Guide</a> 
    #         Go to the [User Guide]({APP_PATH}/User%20Guide#using-your-character-sheet) 
    #     '''
    # ,unsafe_allow_html=True)
    # st.info(f"Check out the [events]({APP_PATH}/Events) page")
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