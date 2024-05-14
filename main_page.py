import json
import streamlit as st
import streamlit_authenticator as stauth
from st_pages import show_pages_from_config, add_page_title, hide_pages
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db, storage
from math import floor, sqrt
import io
import PIL.Image as Image
import os
import ast
import plotly.graph_objects as go
from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, portrait
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import numpy as np
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
import emoji
import requests
from PIL import Image as ImageCheck
from unicodedata import normalize
from sheet_helpers import APP_PATH, filter_dataframe

add_page_title(layout='wide')

show_pages_from_config()

hide_pages(['Register New User', 'Forgot Username', 'Forgot Password', 'User Management'])

faction_list = [
    "🧝 Unaffiliated",
    # "🏴 Blackthorne Company",
    "💰 Guild of the Black Sky",
    "⚜️ Catalpa",
    "🍷 Cedar Hill",
    "🧚‍♀️ The Court of Ashes",
    "🧛‍♂️ The Dismissed",
    "🛡 Eponore",
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

def available_skills(df, skill_path, tier, user_data):
    df = df.copy()
    point_cost = []
    for _, row in df.iterrows():
        if row['Path'] != skill_path:
            if row['Path'] != 'Bard':
                if row['Tier'] == 0:
                    point_cost.append(2)
                else:
                    point_cost.append(row['Tier']*2)
            else:
                point_cost.append(row['Tier'])
        else:
            point_cost.append(row['Tier'])
    df['Point Cost'] = point_cost
    df = df[df['Point Cost'] <= tier]
    known_data = df[df['Skill Name'].isin(st.session_state['known'])].copy()
    if not known_data.empty:
        path_data = []
        for p in skill_paths:
            if not known_data[known_data['Path'] == p].empty:
                path_max = known_data[known_data['Path'] == p]['Tier'].max() + 1
                path_data.append(df[(df['Path'] == p) & (df['Tier'] <= path_max)])
            else:
                path_data.append(df[(df['Path'] == p) & (df['Tier'] == 0)])
        if tier >= 3:
            if not known_data[known_data['Path'] == 'Bard'].empty:
                path_max = known_data[known_data['Path'] == 'Bard']['Tier'].max() + 1
                path_data.append(df[(df['Path'] == 'Bard') & (df['Tier'] <= path_max)])
            else:
                path_data.append(df[(df['Path'] == 'Bard') & (df['Tier'] == 1)])
        df = pd.concat(path_data)
        current_path = known_data[known_data['Path'] == skill_path]['Tier'].max() + 1
        df = df[df['Point Cost'] <= current_path]
    else:
        df = df[(df['Path'] == skill_path) & (df['Tier'] == 0)]
    df = df[df['Point Cost'] <= st.session_state['available']]
    df = df[df['Skill Name'] != 'Cross-Training']
    if 'Read/Write Arcana' not in list(known_data['Skill Name']):
        df = df[df['Spell'] == False]
    known_skills = list(known_data['Skill Name'].unique())
    filter_known = []
    for _, row in df.iterrows():
        if row['Skill Name'] in known_skills:
            filter_known.append(True)
        else:
            filter_known.append(False)
    df['Known'] = filter_known
    df = df[df['Known'] == False]
    known_skills.append('None')
    df = df[df['Prerequisite'].fillna('None').isin(known_skills)]
    df = df.drop(columns=['Known'])
    # df = pd.merge(df, known_data, on=list(df.columns), how='outer', indicator=True).query("_merge != 'both'").drop('_merge', axis=1).reset_index(drop=True)
    if tier == 0 and len(known_skills) >= 4:
        df = pd.DataFrame(columns=df.columns)
    return df

def skill_gain(df, skill_path, tier, char_path, user_data):
    df = df.copy()
    df1 = df.copy()
    df = available_skills(df, skill_path, tier, user_data)
    new_skill = st.selectbox('Pick New Skill', list(df['Skill Name'].unique()))
    if df.empty:
        gain_button = st.button('Gain Skill', disabled=True)
    else:
        if st.button('Gain Skill'):
            gain_df = df[df['Skill Name'] == new_skill].copy()
            idxmin = gain_df.groupby(['Skill Name'])['Point Cost'].idxmin()
            skill_df = gain_df.loc[idxmin]
            st.session_state['point_spend'] = st.session_state['point_spend'] + skill_df['Point Cost'].values[0]
            st.session_state['available'] = skill_points - st.session_state['point_spend']
            known_list = st.session_state['known']
            known_list.append(skill_df['Skill Name'].values[0])
            doc_ref = db.reference("users/").child(char_path)
            doc_ref.update({
                "known":str(st.session_state['known']),
                "point_spend":str(st.session_state['point_spend']),
            })
            df = available_skills(df, skill_path, tier, user_data)
            st.rerun()
    remove_skill = st.selectbox('Pick Skill To Remove', st.session_state['known'])
    if len(st.session_state['known']) == 0:
        remove_button = st.button('Remove Skill', disabled=True)
    else:
        if st.button("Remove Skill"):
            gain_df = df1[df1['Skill Name'] == remove_skill].copy()
            idxmin = gain_df.groupby(['Skill Name'])['Point Cost'].idxmin()
            skill_df = gain_df.loc[idxmin]
            st.session_state['point_spend'] = st.session_state['point_spend'] - skill_df['Point Cost'].values[0]
            st.session_state['available'] = skill_points - st.session_state['point_spend']
            known_list = st.session_state['known']
            known_list.remove(skill_df['Skill Name'].values[0])
            doc_ref = db.reference("users/").child(char_path)
            doc_ref.update({
                "known":str(st.session_state['known']),
                "point_spend":str(st.session_state['point_spend']),
            })
            st.rerun()
        return df

def replace_with_emoji_pdf(text, size):
    """
    Reportlab's Paragraph doesn't accept normal html <image> tag's attributes
    like 'class', 'alt'. Its a little hack to remove those attrbs
    """

    for e in emoji.analyze(text):
        e_icon = e.chars
        try:
            emoji_code = "-".join(f"{ord(c):x}" for c in e_icon)
            url = f"https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/{emoji_code}.png"
            im = ImageCheck.open(requests.get(url, stream=True).raw)
            text = text.replace(e_icon, '<img height={} width={} src="{}"/>'.format(size, size, url))
        except:
            emoji_code = [f"{ord(c):x}" for c in e_icon][0]
            url = f"https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/{emoji_code}.png"
            im = ImageCheck.open(requests.get(url, stream=True).raw)
            text = text.replace(e_icon, '<img height={} width={} src="{}"/>'.format(size, size, url))
    return normalize('NFKD', text).encode('ascii','ignore')

def generate_pdf(player_data, profile_image, logo_image, bio, display_data = pd.DataFrame(), user_events = pd.DataFrame()):
    PAGE_WIDTH, PAGE_HEIGHT= letter
    styles = getSampleStyleSheet()

    PAGESIZE = portrait(letter)

    font_file = 'SedanSC-Regular.ttf'
    sedan_font = TTFont('SedanSC', font_file)
    pdfmetrics.registerFont(sedan_font)

    font_file = 'The_Wild_Breath_of_Zelda.otf'
    zelda_font = TTFont('Zelda', font_file)
    pdfmetrics.registerFont(zelda_font)

    Title = "LARP Adventures Character Sheet"
    def myFirstPage(canvas, doc):
        canvas.saveState()
        canvas.drawImage('OLD_PAPER_TEXTURE.jpg',0,0)
        canvas.drawImage('la_logo.png', doc.leftMargin, doc.height + doc.bottomMargin + doc.topMargin - 4*cm, 3*cm, 3*cm, mask='auto')
        canvas.setFont('Zelda',16)
        canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-doc.topMargin, Title)
        canvas.setFont('SedanSC',9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % (doc.page))
        canvas.restoreState()

    def myLaterPages(canvas, doc):
        canvas.saveState()
        canvas.drawImage('OLD_PAPER_TEXTURE.jpg',0,0)
        canvas.setFont('SedanSC',9)
        canvas.drawString(inch, 0.75 * inch, "Page %d" % (doc.page))
        canvas.restoreState()

    character_info_style = TableStyle(
        [
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ]
    )

    skill_info_style = TableStyle(
        [
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ]
    )

    styles["Title"].fontName = 'SedanSC'
    styles["Title"].fontSize = 10
    styles["Title"].alignment = TA_LEFT

    bio_style = ParagraphStyle('bio')
    bio_style.fontName = 'SedanSC'
    bio_style.fontSize = 10
    bio_style.alignment = TA_LEFT
    bio_style.firstLineIndent = 1*cm

    break_style = ParagraphStyle('breakstyle',
        fontSize=14,
        fontName='Zelda',
        alignment = TA_CENTER
    )

    def table_gen(table_data, headers=False, tstyle=character_info_style, skill_table=False):
        table_data = table_data.map(lambda x:replace_with_emoji_pdf(x, styles['Title'].fontSize) if isinstance(x, str) else str(x))
        if headers:
            if skill_table:
                t1 = Table([[Paragraph(col, style=styles['Title']) for col in table_data.columns]] + np.array(table_data.map(lambda x:Paragraph(x, style=styles['Title']))).tolist(), style=tstyle, repeatRows=1, colWidths=(None,5*inch))
            else:
                t1 = Table([[Paragraph(col, style=styles['Title']) for col in table_data.columns]] + np.array(table_data.map(lambda x:Paragraph(x, style=styles['Title']))).tolist(), style=tstyle, repeatRows=1)
        else:
            t1 = Table(np.array(table_data.map(lambda x:Paragraph(x, style=styles['Title']))).tolist(), style=tstyle, repeatRows=1)
        return t1
    t1 = table_gen(player_data)
    doc = SimpleDocTemplate("table.pdf", pagesize=letter)

    table_style = TableStyle(
        [
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            ('BOX', (0,0), (-1,-1), 0.25, colors.black),
            ('SPAN', (0, 0), (0, -1)),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'CENTER')
        ]
    )
    profile = Image(profile_image,width=4*inch,height=4*inch,kind='proportional')
    logo = Image(logo_image,width=4*inch,height=2*inch,kind='proportional')

    data_table = [
        [profile, t1], 
        ['', logo],
    ]
    final_table = Table(data_table, style=table_style)
    if not display_data.empty:
        t2 = table_gen(display_data, headers=True, tstyle=skill_info_style, skill_table=True)
    if not user_events.empty:
        t3 = table_gen(user_events, headers=True, tstyle=skill_info_style)

    doc = SimpleDocTemplate("character_sheet.pdf", pagesize=PAGESIZE, title='LARP Adventures Character Sheet')
    Story = [Spacer(1,1*inch)]
    Story.append(final_table)
    Story.append(Spacer(1,2*cm))
    Story.append(Paragraph('<u>Biography</u>', style=break_style))
    Story.append(Spacer(1,1*cm))
    Story.append(Paragraph(bio, style=bio_style))
    Story.append(PageBreak())
    if not display_data.empty:
        Story.append(Paragraph('<u>Skills</u>', style=break_style))
        Story.append(Spacer(1,1*cm))
        Story.append(t2)
        Story.append(PageBreak())
    if not user_events.empty:
        Story.append(Paragraph('<u>Events</u>', style=break_style))
        Story.append(Spacer(1,1*cm))
        Story.append(t3)
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
st.sidebar.markdown(
    """
    **This app is maintained by Nate Densmore (Kython). Please reach out to him if you have 
    any questions or concerns. This app is a volunteer passion project, not an official product 
    of LARP Adventures.**
"""
)

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
        try:
            user_events = user_data['event_info']
            data_df = pd.DataFrame(json.loads(user_events))
            data_df.reset_index(drop=True, inplace=True)
            skill_points = int(data_df["Skill Points"].sum())
            tier = get_tier(len(data_df[data_df['Event Type'] != "🪚 Work Weekend"]))
        except:
            skill_points = 0
            tier = 0
        try:
            character_name = user_data['character_name']
        except:
            character_name = ""
        try:
            path = user_data['path']
        except:
            path = '🗡 Warrior'
        try:
            faction = user_data['faction']
        except:
            faction = "🧝 Unaffiliated"
        try:
            image_location = user_data['pic_name']
            all_pics.append(image_location)
            bucket = storage.bucket()
            blob = bucket.blob(image_location)
            profile_image = blob.download_as_bytes()
        except:
            profile_image = "https://64.media.tumblr.com/ac71f483d395c1ad2c627621617149be/tumblr_o8wg3kqct31uxrf2to1_640.jpg"
        try:
            bio = user_data['bio']
        except:
            bio = ''
        try:
            st.session_state['point_spend'] = int(user_data['point_spend'])
        except:
            st.session_state['point_spend'] = 0
        if "available" not in st.session_state:
            st.session_state['available'] = skill_points - st.session_state['point_spend']
        try:
            st.session_state['known'] = ast.literal_eval(user_data['known'])
        except:
            st.session_state["known"] = []
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

    st.info(f"Check out the [User Guide]({APP_PATH}/User%20Guide?tab=Character%20Sheet) for more info", icon=":material/help:")
    
    tab1, tab2,tab3 = st.tabs(['Character Sheet', 'Edit Character', 'Add Skills'])

    player = st.session_state["name"]

    with tab2:
        st.error('Warning: Changing your Path will reset all of your Skills', icon=":material/reset_wrench:")
        with st.form('my_form'):
            character_name_input = st.text_input('Character Name', value=character_name, key='form_char')
            path_input = st.selectbox('Path', path_list, index=path_list.index(path), key='form_path')
            faction_input = st.selectbox('Faction', faction_list, index=faction_list.index(faction), key='form_faction')
            bio_input = st.text_area('Biography', value=bio, key='form_bio')
            uploaded_file = st.file_uploader('Upload Profile Picture', type=['png','gif','jpg','jpeg'], key='form_image')
            if uploaded_file is not None:
                form_image = uploaded_file.getvalue()
                pic_name = '{}.{}'.format(st.session_state['username'],uploaded_file.name.split('.')[1])
                image = ImageCheck.open(io.BytesIO(form_image))
                image.save(pic_name)
            submitted = st.form_submit_button('Save Edits')
            if submitted:
                doc_ref = db.reference("users/").child(char_path)
                if path != path_input:
                    db.reference("users/").child(f"{char_path}/known").delete()
                    db.reference("users/").child(f"{char_path}/point_spend").delete()
                doc_ref.update({
                    "character_name":character_name_input,
                    "path":path_input,
                    "faction":faction_input,
                    "bio":bio_input
                })
                if uploaded_file is not None:
                    origial_character = db.reference("users/").child(st.session_state['username']).get()
                    if char_select == origial_character['character_name']:
                        pic_location = '{}/profile_pic.{}'.format(st.session_state['username'],uploaded_file.name.split('.')[1])
                    else:
                        pic_location = '{}/{}.{}'.format(st.session_state['username'],char_select,uploaded_file.name.split('.')[1])
                    all_pics.append(pic_location)
                    doc_ref.update({
                    "pic_name":pic_location
                    })
                    bucket = storage.bucket()
                    blob = bucket.blob(pic_location)
                    blob.upload_from_filename(pic_name)
                    for b in bucket.list_blobs(prefix=st.session_state['username']):
                        if b.name not in all_pics:
                            b.delete()
                    os.remove(pic_name)
                st.rerun()
        character_name = st.session_state['form_char']
    if 'form_path' in st.session_state:
        path = st.session_state['form_path']
    if 'form_faction' in st.session_state:
        faction = st.session_state['form_faction']
    if 'form_bio' in st.session_state:
        bio = st.session_state['form_bio']

    with tab3:
        try:
            st.session_state['point_spend'] = int(user_data['point_spend'])
        except:
            st.session_state['point_spend'] = 0
        points_available = skill_points - st.session_state['point_spend']
        st.write("### Points Available :",points_available)
        st.info(
            f'Make sure to update your [Events]({APP_PATH}/Events) for full Tier/Skill Points. Skill dropdown selectors are searchable.',
            icon=':material/info:'
            )
        df = pd.read_excel('Skills_Table.xlsx')
        df['Tier'] = df.Tier.astype(int)
        skill_path = path[2:]
        point_cost = []
        for index, row in df.iterrows():
            if row['Path'] != skill_path:
                if row['Path'] != 'Bard':
                    if row['Tier'] == 0:
                        point_cost.append(2)
                    else:
                        point_cost.append(row['Tier']*2)
                else:
                    point_cost.append(row['Tier'])
            else:
                point_cost.append(row['Tier'])
        df['Point Cost'] = point_cost
        df = skill_gain(df, skill_path, tier, char_path, user_data)
        "## Known Skills"
        df1 = pd.read_excel('Skills_Table.xlsx')
        known = st.session_state['known']
        known_data = df1[df1['Skill Name'].isin(known)]
        display_data = known_data[['Skill Name', 'Description', 'Limitations', 'Phys Rep']].drop_duplicates(subset=['Skill Name']).copy()
        st.dataframe(display_data, hide_index=True, use_container_width=True)
        "## Available Skills"
        # try:
        st.dataframe(filter_dataframe(df), hide_index=True, use_container_width=True)
        # except:
        #     st.warning("You've filtered too far. Try again")


    with tab1:
        df = pd.read_excel('Skills_Table.xlsx')
        known = st.session_state['known']
        known_data = df[df['Skill Name'].isin(known)]
        display_data = known_data[['Skill Name', 'Description', 'Limitations', 'Phys Rep']].drop_duplicates(subset=['Skill Name']).copy()
        display_data = display_data.fillna('')
        points_available = skill_points - st.session_state['point_spend']
        with st.container(border=True):
            col1, col2 = st.columns([6,4])
            with col1:
                try:
                    bucket = storage.bucket()
                    blob = bucket.blob(pic_location)
                    profile_image = blob.download_as_bytes()
                except:
                    pass
                i1, i2, i3 = st.columns([1,6,1])
                with i1:
                    st.write("")

                with i2:
                    st.image(profile_image)

                with i3:
                    st.write("")
            with col2:
                player_data = pd.DataFrame({
                    'Category': ['Character  : ','Player  : ','Path  : ','Faction  : ','Tier  : ','Skill Points  : '],
                    'Information': [character_name,player,path,faction,tier,points_available]
                                    })
                for index, row in player_data.iterrows():
                    st.subheader(f'{row.Category}   {row.Information}', divider='orange')
                # st.dataframe(player_data, hide_index=True, use_container_width=True)
                bucket = storage.bucket()
                try:
                    if faction not in ["🧝 Unaffiliated","🤖 NPC"]:
                        blob = bucket.blob("faction_logos/{}.jpg".format(faction))
                        logo = blob.download_as_bytes()
                    else:
                        blob = bucket.blob("faction_logos/la_logo.png")
                        logo = blob.download_as_bytes()
                except:
                        blob = bucket.blob("faction_logos/la_logo.png")
                        logo = blob.download_as_bytes()
                fi1, fi2, fi3 = st.columns([1,6,1])
                with fi1:
                    st.write("")

                with fi2:
                    st.image(logo, use_column_width=True)

                with fi3:
                    st.write("")
                blob = bucket.blob("faction_logos/la_logo.png")
                blob.download_to_filename('la_logo.png')
                logo_image = 'la_logo.png'
                if st.button('Generate Character Sheet PDF', use_container_width=True):
                    with st.spinner('Generating PDF'):
                        try:
                            user_data = db.reference("users/").child(char_path).get()
                            try:
                                image_location = user_data['pic_name']
                                bucket = storage.bucket()
                                blob = bucket.blob(image_location)
                                blob.download_to_filename(user_data['pic_name'].split('/')[1])
                                profile_image = user_data['pic_name'].split('/')[1]
                            except:
                                bucket = storage.bucket()
                                blob = bucket.blob("faction_logos/la_logo.png")
                                blob.download_to_filename('logo.jpg')
                                profile_image = 'logo.jpg'
                            if faction not in ["🧝 Unaffiliated","🤖 NPC"]:
                                blob = bucket.blob("faction_logos/{}.jpg".format(faction))
                                blob.download_to_filename(faction + '.jpg')
                                logo_image = faction + '.jpg'
                            else:
                                blob = bucket.blob("faction_logos/la_logo.png")
                                blob.download_to_filename('la_logo.png')
                                logo_image = 'la_logo.png'
                            generate_pdf(player_data, profile_image, logo_image, bio)
                            blob = bucket.blob(st.session_state['username'] + '/character_sheet.pdf')
                            blob.upload_from_filename('character_sheet.pdf')
                            os.remove('character_sheet.pdf')
                            os.remove(profile_image)
                            os.remove(logo_image)
                            if os.path.isfile('la_logo.png'):
                                os.remove('la_logo.png')
                            blob = bucket.blob(st.session_state['username'] + '/character_sheet.pdf')
                            pdf_data = blob.download_as_bytes()
                            st.download_button(label="Download Character Sheet",
                                data=pdf_data,
                                file_name="{}.pdf".format(character_name),
                                mime='application/octet-stream',
                                use_container_width=True,
                                type='primary'
                            )
                        except:
                            st.warning('Not enough data to generate')
                if st.button('Generate Character Sheet PDF w/ Skills', use_container_width=True):
                    with st.spinner('Generating PDF'):
                        try:
                            user_data = db.reference("users/").child(st.session_state['username']).get()
                            try:
                                image_location = user_data['pic_name']
                                bucket = storage.bucket()
                                blob = bucket.blob(image_location)
                                blob.download_to_filename(user_data['pic_name'].split('/')[1])
                                profile_image = user_data['pic_name'].split('/')[1]
                            except:
                                bucket = storage.bucket()
                                blob = bucket.blob("faction_logos/la_logo.png")
                                blob.download_to_filename('logo.jpg')
                                profile_image = 'logo.jpg'
                            if faction not in ["🧝 Unaffiliated","🤖 NPC"]:
                                blob = bucket.blob("faction_logos/{}.jpg".format(faction))
                                blob.download_to_filename(faction + '.jpg')
                                logo_image = faction + '.jpg'
                            else:
                                blob = bucket.blob("faction_logos/la_logo.png".format(faction))
                                blob.download_to_filename('la_logo.png')
                                logo_image = 'la_logo.png'
                            
                            generate_pdf(player_data, profile_image, logo_image, bio, display_data[['Skill Name', 'Description']])
                            blob = bucket.blob(st.session_state['username'] + '/character_sheet.pdf')
                            blob.upload_from_filename('character_sheet.pdf')
                            os.remove('character_sheet.pdf')
                            os.remove(profile_image)
                            os.remove(logo_image)
                            if os.path.isfile('la_logo.png'):
                                os.remove('la_logo.png')
                            blob = bucket.blob(st.session_state['username'] + '/character_sheet.pdf')
                            pdf_data = blob.download_as_bytes()
                            st.download_button(label="Download Character Sheet",
                                data=pdf_data,
                                file_name="{}.pdf".format(character_name),
                                mime='application/octet-stream',
                                use_container_width=True,
                                type='primary'
                            )
                        except:
                            st.warning('Not enough data to generate')
                if st.button('Generate Character Sheet PDF w/ Skills and Events', use_container_width=True):
                    with st.spinner('Generating PDF'):
                        # try:
                        user_data = db.reference("users/").child(st.session_state['username']).get()
                        try:
                            image_location = user_data['pic_name']
                            bucket = storage.bucket()
                            blob = bucket.blob(image_location)
                            blob.download_to_filename(user_data['pic_name'].split('/')[1])
                            profile_image = user_data['pic_name'].split('/')[1]
                        except:
                            bucket = storage.bucket()
                            blob = bucket.blob("faction_logos/la_logo.png")
                            blob.download_to_filename('logo.jpg')
                            profile_image = 'logo.jpg'
                        if faction not in ["🧝 Unaffiliated","🤖 NPC"]:
                            blob = bucket.blob("faction_logos/{}.jpg".format(faction))
                            blob.download_to_filename(faction + '.jpg')
                            logo_image = faction + '.jpg'
                        else:
                            blob = bucket.blob("faction_logos/la_logo.png".format(faction))
                            blob.download_to_filename('la_logo.png')
                            logo_image = 'la_logo.png'
                        user_events = pd.DataFrame(json.loads(user_events))
                        user_events.reset_index(drop=True, inplace=True)
                        try:
                            user_events['Event Date'] = pd.to_datetime(user_events['Event Date'], format="%B %Y").apply(lambda x:x.strftime("%B %Y"))
                        except:
                            pass
                        try:
                            user_events['Event Date'] = pd.to_datetime(user_events['Event Date'], unit='ms').apply(lambda x:x.strftime("%B %Y"))
                        except:
                            pass
                        user_events[['Bonus Skill Points', 'Skill Points']] = user_events[['Bonus Skill Points', 'Skill Points']].astype(int)
                        generate_pdf(player_data, profile_image, logo_image, bio, display_data[['Skill Name', 'Description']], user_events)
                        blob = bucket.blob(st.session_state['username'] + '/character_sheet.pdf')
                        blob.upload_from_filename('character_sheet.pdf')
                        os.remove('character_sheet.pdf')
                        os.remove(profile_image)
                        os.remove(logo_image)
                        if os.path.isfile('la_logo.png'):
                            os.remove('la_logo.png')
                        blob = bucket.blob(st.session_state['username'] + '/character_sheet.pdf')
                        pdf_data = blob.download_as_bytes()
                        st.download_button(label="Download Character Sheet",
                            data=pdf_data,
                            file_name="{}.pdf".format(character_name),
                            mime='application/octet-stream',
                            use_container_width=True,
                            type='primary'
                        )
                        # except:
                        #     st.warning('Not enough data to generate')
            st.markdown("<u><h2 style='text-align: center;'>Biography</h2></u>", unsafe_allow_html=True)
            st.write(bio)
            st.markdown("<u><h2 style='text-align: center;'>Known Skills</h2></u>", unsafe_allow_html=True)
            st.dataframe(display_data.astype(str), hide_index=True, use_container_width=True, height=800)


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


