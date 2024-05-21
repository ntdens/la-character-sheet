import json
import streamlit as st
import streamlit_authenticator as stauth
from st_pages import show_pages_from_config, add_page_title, hide_pages
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db, storage
from math import floor, sqrt
import io
import ast
import os
from PIL import Image as ImageCheck
from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.pagesizes import B7, B8, portrait
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from sheet_helpers import APP_PATH, sidebar_about

add_page_title(layout='wide')

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Username', 'Forgot Password', 'User Management'])


def use_calc(path, base, mod, unit):
    tier = tier_df[tier_df['Path'] == path].iloc[0]['Tier']
    use_count = base + eval(str(mod).replace('t', str(tier)))
    return f'{use_count} {unit}', use_count

def get_tier(events):
    return floor((sqrt(8*events)-1)/2)

def generate_pdf(spells, print_friendly):
    styles = getSampleStyleSheet()

    PAGESIZE = portrait(B7)

    font_file = 'GaramondUS.ttf'
    sedan_font = TTFont('GaramondUS', font_file)
    pdfmetrics.registerFont(sedan_font)

    font_file = 'GaramondUSB.ttf'
    sedan_font = TTFont('GaramondUSB', font_file)
    pdfmetrics.registerFont(sedan_font)

    font_file = 'GaramondUSI.ttf'
    sedan_font = TTFont('GaramondUSI', font_file)
    pdfmetrics.registerFont(sedan_font)

    font_file = 'GaramondUSBI.ttf'
    sedan_font = TTFont('GaramondUSBI', font_file)
    pdfmetrics.registerFont(sedan_font)

    pdfmetrics.registerFontFamily('GaramondUS',normal='GaramondUS',bold='GaramondUSB',italic='GaramondUSI',boldItalic='GaramondUSBI')

    font_file = 'The_Wild_Breath_of_Zelda.otf'
    zelda_font = TTFont('Zelda', font_file)
    pdfmetrics.registerFont(zelda_font)

    Title = "LARP Adventures Spell Cards"
    def myFirstPage(canvas, doc):
        canvas.saveState()
        if not print_friendly:
            canvas.drawImage('OLD_PAPER_TEXTURE.jpg',0,0)
        canvas.restoreState()

    def myLaterPages(canvas, doc):
        canvas.saveState()
        if not print_friendly:
            canvas.drawImage('OLD_PAPER_TEXTURE.jpg',0,0)
        canvas.restoreState()

    styles["Title"].fontName = 'SedanSC'
    styles["Title"].fontSize = 10
    styles["Title"].alignment = TA_LEFT

    bio_style = ParagraphStyle('bio')
    bio_style.fontName = 'SedanSC'
    bio_style.fontSize = 10
    bio_style.alignment = TA_LEFT
    bio_style.firstLineIndent = 1*cm

    spell_name = ParagraphStyle('spellname',
        fontSize=12,
        fontName='Zelda',
        alignment = TA_LEFT
    )

    spell_style = ParagraphStyle('spellstyle',
        fontSize=10,
        fontName='GaramondUS',
        alignment = TA_LEFT
    )

    doc = SimpleDocTemplate("spell_cards.pdf", pagesize=PAGESIZE, title='LARP Adventures Spell Cards', rightMargin=.1*cm,leftMargin=.1*cm,topMargin=.1*cm,bottom_margin=.1*cm)
    Story = []
    for _, row in spells.iterrows():
        Story.append(Paragraph(row['Skill Name'], style=spell_name))
        try:
            spell_text = user_data['spellbook'][row['Skill Name'].replace('/','_')]
        except:
            spell_text = ''
        Story.append(Paragraph(f"<i>{spell_text}</i>"))
        Story.append(Paragraph(f'<b>Description:</b> {")".join(row["Description"].split(")")[1:])}'))
        if row['Uses'] != '':
            Story.append(Paragraph(f'<b>Uses:</b> {row["Uses"]}'))
        Story.append(Paragraph(f'<b>Limitations:</b> {row["Limitations"]}'))
        Story.append(Paragraph(f'<b>Phys Rep:</b> {row["Phys Rep"]}'))
        Story.append(PageBreak())
    doc.build(Story, onFirstPage=myFirstPage, onLaterPages=myLaterPages)

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
    st.info(f"Check out the [User Guide]({APP_PATH}/User%20Guide?tab=Spellbook) for more info.", icon=":material/help:")
    try:
        user_data = db.reference("users/").child(st.session_state['username']).get()
        all_pics = []
        try:
            all_pics.append(user_data['pic_name'])
        except:
            pass
        char_path = st.session_state['username']
        if 'characters' in user_data.keys():
            for c in user_data['characters']:
                try:
                    all_pics.append(user_data['characters'][c]['pic_name'])
                except:
                    pass
            char_select = st.selectbox('Pick Character', options=[user_data['character_name']] + list(user_data['characters']))
            if char_select != user_data['character_name']:
                user_data = user_data['characters'][char_select]
                char_path = "{}/characters/{}".format(st.session_state['username'], char_select)
        if 'event_info' in user_data.keys():
            user_events = user_data['event_info']
            data_df = pd.DataFrame(json.loads(user_events))
            data_df.reset_index(drop=True, inplace=True)
            skill_points = int(data_df["Skill Points"].sum())
            tier = get_tier(len(data_df[(data_df['Event Type'] != "🪚 Work Weekend")  & (data_df['Event Type'] != "🗳️ Survey/Misc")]))
        else:
            skill_points = 0
            tier = 0
        if 'character_name' in user_data.keys():
            character_name = user_data['character_name']
        else:
            character_name = ""
        if 'path' in user_data.keys():
            path = user_data['path']
        else:
            path = '🗡 Warrior'
        if 'faction' in user_data.keys():
            faction = user_data['faction']
        else:
            faction = "🧝 Unaffiliated"
        if 'pic_name' in user_data.keys():
            image_location = user_data['pic_name']
            all_pics.append(image_location)
            bucket = storage.bucket()
            blob = bucket.blob(image_location)
            profile_image = ImageCheck.open(io.BytesIO(blob.download_as_bytes()))
        else:
            profile_image = "https://64.media.tumblr.com/ac71f483d395c1ad2c627621617149be/tumblr_o8wg3kqct31uxrf2to1_640.jpg"
        if 'bio' in user_data.keys():
            bio = user_data['bio']
        else:
            bio = ''
        if 'point_spend' in user_data.keys():
            st.session_state['point_spend'] = int(user_data['point_spend'])
        else:
            st.session_state['point_spend'] = 0
        if "available" not in st.session_state:
            st.session_state['available'] = skill_points - st.session_state['point_spend']
        if 'known' in user_data.keys():
            st.session_state['known'] = ast.literal_eval(user_data['known'])
        else:
            st.session_state["known"] = []
        if 'professions' in user_data.keys():
            prof = ast.literal_eval(user_data['professions'])
        else:
            prof = None
        if 'orgs' in user_data.keys():
            orgs = ast.literal_eval(user_data['orgs'])
        else:
            orgs = None
    except:
        skill_points = 0
        tier = 0
        character_name = ""
        path = '🗡 Warrior'
        faction = "🧝 Unaffiliated"
        profile_image = "https://64.media.tumblr.com/ac71f483d395c1ad2c627621617149be/tumblr_o8wg3kqct31uxrf2to1_640.jpg"
        bio = ''
        st.session_state["known"] = []
        st.session_state['point_spend'] = 0
        st.session_state['available'] = skill_points - st.session_state['point_spend']
        prof = None
        orgs = None

    df = pd.read_excel('Skills_Table.xlsx')
    df = df[df['Spell'] == True]
    known = st.session_state['known']
    known_data = df[df['Skill Name'].isin(known)]
    use_df = pd.read_excel('Skill Use.xlsx')
    tier_df = pd.DataFrame({'Path':['Warrior', 'Rogue', 'Healer', 'Mage', 'Bard', 'Artificer', path.split(' ')[1]], 'Tier':[0,0,0,0,0,0, tier]})
    tier_df = pd.concat([known_data, tier_df]).groupby('Path')['Tier'].max().reset_index()
    use_df[['Uses', 'Use Count']] = pd.DataFrame(use_df.apply(lambda x:use_calc(x['Path'], x['Base'], x['Tier Modifer'], x['Unit']), axis=1).to_list())
    use_df = use_df[['Skill Name', 'Path', 'Tier', 'Uses', 'Use Count']]
    known_data = pd.merge(known_data, use_df, on=['Skill Name','Path','Tier'], how='left')
    spells = known_data.sort_values('Use Count', ascending=False).drop_duplicates('Skill Name').sort_index().sort_values('Tier')[['Skill Name', 'Uses', 'Description', 'Limitations', 'Phys Rep']].copy()
    spells = spells.fillna('')
    if spells.empty:
        st.warning(f'{character_name} knowns no spells',icon=':material/psychology_alt:')
    else:
        with st.form('spell_card_generation'):
            st.markdown('**Spell Card PDF Options:**')
            print_friendly = st.checkbox('Printer Friendly Sheet')
            pdf_submit = st.form_submit_button('Generate Spell Cards PDF', use_container_width=True)
        if pdf_submit:
            with st.spinner('Generating PDF'):
                generate_pdf(spells, print_friendly)
                blob = bucket.blob(st.session_state['username'] + '/spell_cards.pdf')
                blob.upload_from_filename('spell_cards.pdf')
                os.remove('spell_cards.pdf')
                blob = bucket.blob(st.session_state['username'] + '/spell_cards.pdf')
                pdf_data = blob.download_as_bytes()
                st.download_button(label="Download Spell Cards",
                    data=pdf_data,
                    file_name="{}_spells.pdf".format(character_name),
                    mime='application/octet-stream',
                    use_container_width=True,
                    type='primary'
                )
        for _, row in spells.iterrows():
            st.subheader(row['Skill Name'], divider='orange')
            col1, col2 = st.columns([1,1])
            with col1:
                st.markdown(f'**Description:** {")".join(row["Description"].split(")")[1:])}')
                if row['Uses'] != '':
                    st.markdown(f'**Uses:** {row["Uses"]}')
                st.markdown(f'**Limitations:** {row["Limitations"]}')
                st.markdown(f'**Phys Rep:** {row["Phys Rep"]}')
            with col2:
                word_count = int(row['Phys Rep'].split(' ')[0])
                try:
                    spell_text = user_data['spellbook'][row['Skill Name'].replace('/','_')]
                except:
                    spell_text = ''
                st.markdown(f'**Spell:**  *{spell_text}*')
                allow_editing = st.checkbox('Edit Spell', key=f'{row["Skill Name"]}_edit')
                if allow_editing:
                    with st.form(f'spell_input_{row["Skill Name"]}'):
                        spell_input = st.text_area('Spell Text', key=f'text_area_{row["Skill Name"]}', value=spell_text)
                        submit = st.form_submit_button('Save Spell')
                        spell_length = len(spell_input.split())
                        if submit:
                            if spell_length >= word_count:
                                doc_ref = db.reference("users/").child(char_path)
                                doc_ref.update({
                                    f"spellbook/{row['Skill Name'].replace('/','_')}":spell_input
                                })
                                st.rerun()
                            else:
                                st.warning('Spell too short. Need {} more word(s)'.format(word_count - spell_length), icon=':material/trending_up:')


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

