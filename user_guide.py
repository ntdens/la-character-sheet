import json
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_modal import Modal
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from sheet_helpers import APP_PATH, sidebar_about
import uuid

if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase"], strict=False)
    creds = credentials.Certificate(key_dict)
    defualt_app = firebase_admin.initialize_app(creds, {
        'databaseURL': 'https://la-character-sheets-default-rtdb.firebaseio.com',
        'storageBucket':'la-character-sheets.appspot.com'
    })

with open( "style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)

def link_create(page):
    return f'[{page}]({APP_PATH}/{page.replace(" ","%20")})'

def material_icon(icon_name):
    return f'<i class="material-icons">{icon_name}</i>'

# Generic function to inject js_code
def inject_native_js_code(source: str) -> None:
    div_id = uuid.uuid4()

    st.components.v1.html(
        f"""
    <div style="display:none" id="{div_id}">
        <script>
            {source}
        </script>
    </div>
    """,
        width=0,
        height=0,
    )

def js_click_component(component_id: str):

    source = f"""
            var tab = window.parent.document.querySelector('[id*={component_id}]');
            tab.click();
        """

    inject_native_js_code(source)

st.sidebar.title("About")
sidebar_about()

#authenticate users
if st.session_state["authentication_status"]:
    list_of_tabs = [
        'Getting Started',
        'Character Sheet',
        'Events',
        'Spellbook',
        'Skills',
        'Additional Characters',
        'Profile',
        'Admin Zone'
        ]
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(list_of_tabs)
    query = st.query_params.to_dict()
    if "tab" in query.keys():
        js_click_component(f"tab-{list_of_tabs.index(query['tab'])}")
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
                Once your events are all recorded, it's time to head over to the [Character Sheet]({APP_PATH})
                page. This page is divided into three tabs. The first tab holds your completed character sheet. The second tab is where you
                actually create and edit your character. It is here you should go next. Enter your character name, path, faction, professions, 
                organziations, and even upload a picture if you wish!
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
                Here is where you can update your character's name, faction, path, biography, professions, organizations, and upload an image 
                for your character sheet. Currently only accepting png, jpg, and gif image types. If you change your path, you will lose all 
                current known skills and point spend and will have to rebuild your skills from the beginning. 
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
    with tab3:
        st.header('Events', divider='orange')
        st.subheader('How It Works')
        st.markdown(
            f'''
                This is the page to keep track of all of the events you have been to. You can add the Event Name, Event Date, Event Type, 
                mark off whether you were an NPC or did merchant overtime, and mark any additional skill points earned (i.e. Trollmas donation 
                or incliment weather survivor). Once you have added all your information and hit save, the app will calculate the number of skill
                points earned and update the table. This data is used to determine Skill Points and Tier for your character.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Types of Events')
        st.markdown(
            f'''
                There are currently six different event types being tracked:
                * **☀️ Day Event**: These are normal one day events and worth one skill point.
                * **⛺️ Campout Event**: These are Friday-Sunday events and are worth two skill points.
                * **🎆 Festival Event**: These are Thursday-Sunday events and are worth three skill points.
                * **👾 Virtual Event**: These are counted the same as day events.
                * **🪚 Work Weekend**: These are for working up in Oakenshield outside of an event. You get one skill point but no Tier progress.
                * **🗳️ Survey/Misc**: For completing surveys/any other bonus points earned outside of an event.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Adding a New Event')
        st.markdown(
            f'''
                To add a new event, simply click on the next empty row and start typing in the details. You should see a {material_icon("add")} 
                icon appear on hover. You can also hit the {material_icon("add")} on the upper right corner of the table to add a new row. 
                When adding events it is important to add in the date of the event. While the date will keep track of the specific day in the
                background, any day is fine if you only care about month/year. Once you are done adding your event(s), hit the Save Events button
                in the lower left to save the table to the database.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Removing Events')
        st.markdown(
            f'''
                To remove events from the table, first click to the far left of the row you want to delete. You should see a 
                {material_icon("check_box_outline_blank")} on hover, which turns into a {material_icon("check_box")} on click. Once you have
                selected all the rows you want to get rid of, hit the {material_icon("delete")} button in the upper right (should be the far left icon 
                of the group). Once that is done, hit the Save Events button to save your changes to the database.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Other Functions')
        st.markdown(
            f'''
                As with the rest of the tables in this app, you can search the table by hitting the {material_icon("search")} button in 
                the upper right hand corner. You can also download the table as a csv by hitting the {material_icon("download")} button 
                in the same location.
            '''
        ,unsafe_allow_html=True)
    with tab4:
        st.header('Spellbook', divider='orange')
        st.subheader('How It Works')
        st.markdown(
            f'''
                Here you can keep track of and add text to all of the spells you have learned through your Path(s) skill tree.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Editing a Spell')
        st.markdown(
            f'''
                To edit a spell, hit the Edit Spell checkbox within the spell you want to add or edit the text for. Once selected, an editable 
                text box will appear. Once done, hit the Save Spell button to add the changes to the database. If the spell does not meet 
                length requirements it will not save.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Generating Spell Cards')
        st.markdown(
            f'''
                You can generate printable spell cards by using the form at the top of the page. You can set the cards to either be playing 
                card or index car sized.
            '''
        ,unsafe_allow_html=True)
    with tab5:
        st.header('Skills', divider='orange')
        st.subheader('How It Works')
        st.markdown(
            f'''
                This page has every skill available to players in LARP Adventures. By checking the Add filters box at the top you can filter 
                down to what skills you are interested in. The table works the same way as other tables in the application. You can double 
                click on any cell to expand its contents. You can search the table by hitting the {material_icon("search")} button in 
                the upper right hand corner, and you can download the table as a csv by hitting the {material_icon("download")} button 
                in the same location.
            '''
        ,unsafe_allow_html=True)
    with tab6:
        st.header('Additional Characters', divider='orange')
        st.subheader('How It Works')
        st.markdown(
            f'''
                Here is where you can build more characters besides for just your main character. This is useful if you want to build 
                out an NPC character, or if you play multiple characters. Once you add a new character, you will get new dropdowns on the 
                [Character Sheet]({APP_PATH}) and {link_create('Events')} pages. Use those to select which character you want to build out 
                at the time.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Adding a Character')
        st.markdown(
            f'''
                To add a character, simply open the Add New Character expander and fill out the relevant information. If creating an NPC 
                select "🤖 NPC" underneath the Faction selection. Whatever name you choose here will be the character's key in the database, 
                so it has to be different from your other character's names, and will be what you pick on the dropdown selectors. Even if you 
                change the name of the character on the [Character Sheet]({APP_PATH}) page, the dropdown choice will remain whatever you originally 
                chose for the character. Once you are done filling out the form and hit save, your new character will be generated.
            '''
        ,unsafe_allow_html=True)
        st.subheader('Removing a Character')
        st.markdown(
            f'''
                To remove a character, select them from the dropdown under Delete Additional Character. Once you hit delete, a pop-up will appear 
                confirming your intent to delete. Once you confirm a second time, the character is deleted from the database.
            '''
        ,unsafe_allow_html=True)
    with tab7:
        st.header('Profile', divider='orange')
        st.subheader("Overview")
        st.markdown(
            f'''
                The profile page is a simple summary of your user infomation. It shows you your registered username, name, and email. Here you 
                can updated your name and email, as well as change your password.
            '''
        ,unsafe_allow_html=True)
        st.subheader("Changing Your Password")
        st.markdown(
            f'''
                To change your password, simply click the reset password button. You will get a formprompting you to enter your old password, 
                a new password, and to repeat that new password to confirm. Once you hit reset, if everything is filled out properly, your new password 
                will be set.
            '''
        ,unsafe_allow_html=True)
        st.subheader("Updating Your Details")
        st.markdown(
            f'''
                To change your name or email, click on the Update User Details button and fill out the form. Once you hit update your profile 
                will be updated. You are not able to update your username at this time.
            '''
        ,unsafe_allow_html=True)
    with tab8:
        st.header('Admin Zone', divider='orange')
        st.subheader("What Is It?")
        st.markdown(
            f'''
                The Admin Zone is to provide an overview of the realm's character sheets to Organizers and Faction Leaders. It can show metrics 
                such as tier and path breakdowns, and give the ability to view (not modify) other character sheets.
            '''
        ,unsafe_allow_html=True)
        st.subheader("What Is Admin Access?")
        st.markdown(
            f'''
                Admin Access is reserved for the Organizers and the app's developers. It gives an overview of metrics across everyone's character 
                sheets, and the ability to pull up full character sheets and event attendance. If you're an organzier and want to apply for Admin 
                access, fill out the form and you will be added as soon as possible.
            '''
        ,unsafe_allow_html=True)
        st.subheader("What Is Faction Leader Access?")
        st.markdown(
            f'''
                Faction Leader Access is to help enable Faction Leaders to have an overview on the state of their own faction. They will get a smaller 
                set of metrics covering only people in their faction. They can also pull up character sheets of members in their faction, but only with 
                the basic information attached such as name, tier and path. :red[**They will *not* be able to see what skills you have learned.**] This is to ensure 
                players have some sort of privacy around thier character and the ability to have fun secrets. If you want to know someone's skills, reach 
                out to the directly. To apply for Faction Leader Access, fill out the form and you will be added as soon as possible.
            '''
        ,unsafe_allow_html=True)

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