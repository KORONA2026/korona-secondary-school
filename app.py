import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import hashlib
import base64
import re
import os
import time
from io import BytesIO

# Maktaba ya kutengeneza PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DB_NAME = "admission_register.db"

# Kazi ya kufanya neno la siri kuwa salama (Hash Password)
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# Kutengeneza Database na Table zote
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 1. Table ya Watumiaji (Users)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'User'
        )
    ''')
    # 2. Table ya Mabweni
    c.execute('''
        CREATE TABLE IF NOT EXISTS dorms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dorm_name TEXT UNIQUE NOT NULL,
            capacity INTEGER NOT NULL
        )
    ''')
    # 3. Table ya Wanafunzi
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admno TEXT UNIQUE NOT NULL,
            jina_mwanafunzi TEXT NOT NULL,
            class_form TEXT,
            comb TEXT,
            tarehe_kuripoti DATE,
            tarehe_kuzaliwa DATE,
            uraia TEXT DEFAULT 'Mtanzania',
            jina_baba_mlezi TEXT,
            kazi_yake TEXT,
            simu TEXT,
            shule_aliyotoka TEXT,
            shule_anayokwenda TEXT,
            mahali_alipotoka TEXT,
            pay_slip TEXT DEFAULT 'Haijaletwa',
            rim TEXT DEFAULT 'Haijaletwa',
            reki TEXT DEFAULT 'Haijaletwa',
            jembe TEXT DEFAULT 'Haijaletwa',
            graph_2 TEXT DEFAULT 'Haijaletwa',
            hard_bloom TEXT DEFAULT 'Haijaletwa',
            kwanja TEXT DEFAULT 'Haijaletwa',
            squizer TEXT DEFAULT 'Haijaletwa',
            soft_broom TEXT DEFAULT 'Haijaletwa',
            file_2 TEXT DEFAULT 'Haijaletwa',
            ndoo TEXT DEFAULT 'Haijaletwa',
            bweni_id INTEGER,
            tarehe_kuondoka DATE,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY(bweni_id) REFERENCES dorms(id)
        )
    ''')
    # 4. Table ya Mipangilio (Settings)
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Mipangilio ya mwanzo (Default Settings)
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('school_name', 'PANGANI HALISI SECONDARY SCHOOL')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('school_logo', '')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('expiry_date', '2030-12-31')")
    
    # Akaunti kuu ya Admin kiotomatiki kama haipo (Username: admin, Password: admin123)
    hashed_admin_pass = make_hashes("admin123")
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", hashed_admin_pass, "Admin"))
    
    # Kuingiza yale Mabweni 8 ya Excel yako kiotomatiki
    mabweni_ya_excel = ["SERENGETI", "MWL NYERERE", "TARANGIRE", "RUAHA", "MKOMAZI", "NGORONGORO", "MANYARA", "MIKUMI"]
    for bweni in mabweni_ya_excel:
        try:
            c.execute("INSERT OR IGNORE INTO dorms (dorm_name, capacity) VALUES (?, ?)", (bweni, 60))
        except:
            pass
            
    conn.commit()
    conn.close()

init_db()

# Kazi za kupata mipangilio kutoka database
def get_setting(key, default_val=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default_val

def get_school_name():
    return get_setting('school_name', 'Korona Secondary School')

# Kazi ya kupata Admission Number inayofuata kiotomatiki
def get_next_admno():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT admno FROM students ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        last_adm = row[0]
        try:
            numbers = re.findall(r'\d+', last_adm)
            if numbers:
                last_num_str = numbers[-1]
                next_num = int(last_num_str) + 1
                next_num_str = str(next_num).zfill(len(last_num_str))
                pos = last_adm.rfind(last_num_str)
                return last_adm[:pos] + next_num_str + last_adm[pos+len(last_num_str):]
            else:
                return str(int(last_adm) + 1)
        except:
            return ""
    return "1001"

# Kazi ya kutengeneza PDF ya Madeni ya Vifaa
def generate_madeni_pdf(dataframe, shule_name):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.HexColor('#1e3a8a'), alignment=1
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=colors.HexColor('#475569'), alignment=1
    )
    cell_style = ParagraphStyle(
        'CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.black
    )
    cell_bold_style = ParagraphStyle(
        'CellBoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.black
    )

    story.append(Paragraph(shule_name.upper(), title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"RIPOTI YA WANAFUNZI NA VIFAA WANAVYODAIWA", subtitle_style))
    story.append(Paragraph(f"Tarehe ya Ripoti: {date.today().strftime('%d-%m-%Y')}", subtitle_style))
    story.append(Spacer(1, 15))
    
    data = [["S/N", "Adm No", "Jina la Mwanafunzi", "Darasa", "Comb", "Bweni", "Vifaa Anavyodaiwa"]]
    
    for idx, row in enumerate(dataframe.to_dict('records'), start=1):
        data.append([
            Paragraph(str(idx), cell_style),
            Paragraph(str(row['Admission No']), cell_bold_style),
            Paragraph(str(row['Jina la Mwanafunzi']), cell_bold_style),
            Paragraph(str(row['Darasa']), cell_style),
            Paragraph(str(row['Combination']), cell_style),
            Paragraph(str(row['Bweni']), cell_style),
            Paragraph(str(row['Anachodaiwa Tu (Vifaa)']), cell_style)
        ])
        
    col_widths = [25, 45, 130, 45, 35, 65, 207]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# Kazi ya kutengeneza PDF ya Muhtasari wa Ukusanyaji wa Vifaa
def generate_ukusanyaji_pdf(dataframe, shule_name):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.HexColor('#1e3a8a'), alignment=1
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=colors.HexColor('#475569'), alignment=1
    )
    cell_style = ParagraphStyle(
        'CellStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=13, textColor=colors.black
    )
    cell_bold_style = ParagraphStyle(
        'CellBoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=colors.black
    )

    story.append(Paragraph(shule_name.upper(), title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"RIPOTI YA MUHTASARI WA UKUSANYAJI WA VIFAA", subtitle_style))
    story.append(Paragraph(f"Tarehe ya Ripoti: {date.today().strftime('%d-%m-%Y')}", subtitle_style))
    story.append(Spacer(1, 15))
    
    data = [["Kifaa (Luggage Item)", "Waliileta (✓)", "Bado Hawajaleta (✗)", "Hawahusiki (H)", "Ufanisi (%)"]]
    
    for row in dataframe.to_dict('records'):
        data.append([
            Paragraph(str(row['Kifaa (Luggage Item)']), cell_bold_style),
            Paragraph(str(row['Waliileta (✓)']), cell_style),
            Paragraph(str(row['Bado Hawajaleta (✗)']), cell_style),
            Paragraph(str(row['Hawahusiki (H)']), cell_style),
            Paragraph(str(row['Ufanisi (%)']), cell_bold_style)
        ])
        
    col_widths = [160, 90, 110, 100, 72]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

SCHOOL_NAME = get_school_name()
SCHOOL_LOGO_BASE64 = get_setting('school_logo', '')
EXPIRY_DATE_STR = get_setting('expiry_date', '2030-12-31')

st.set_page_config(page_title=f"{SCHOOL_NAME} System", page_icon="🏫", layout="wide")

def render_metric_card(title, value, bg_color="#4F46E5", text_color="#ffffff", icon="📊"):
    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 22px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 15px; color: {text_color}; border: 1px solid rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; opacity: 0.9;">
            <span style="font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;">{title}</span>
            <span style="font-size: 24px;">{icon}</span>
        </div>
        <div style="font-size: 32px; font-weight: 800; margin-top: 10px; letter-spacing: -0.5px;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def display_logo(height=100, sidebar=False):
    if SCHOOL_LOGO_BASE64:
        logo_html = f"<img src='data:image/png;base64,{SCHOOL_LOGO_BASE64}' style='height:{height}px; max-width:100%; object-fit:contain;'>"
        if sidebar:
            st.sidebar.markdown(f"<center>{logo_html}</center>", unsafe_allow_html=True)
        else:
            st.markdown(f"<center>{logo_html}</center>", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'role' not in st.session_state:
    st.session_state['role'] = ""

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT password, role FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    if data:
        if check_hashes(password, data[0]):
            return data[1]
    return False

# --- LOG IN PAGE ---
if not st.session_state['logged_in']:
    st.markdown("<br>", unsafe_allow_html=True)
    display_logo(height=120, sidebar=False)
    st.markdown(f"<center><h2 style='color:#1e3a8a;'>🏫 {SCHOOL_NAME}</h2><h4 style='color:#64748b;'>Admission & Dorms Management System</h4></center>", unsafe_allow_html=True)
    st.markdown("---")
    
    col_l1, col_l2, col_l3 = st.columns([1,1.5,1])
    with col_l2:
        st.markdown("<div style='background-color:#f1f5f9; padding:30px; border-radius:10px;'>", unsafe_allow_html=True)
        st.subheader("Ingia Kwenye Mfumo (Login)")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Login", use_container_width=True):
            role = login_user(username, password)
            if role:
                try:
                    exp_date = datetime.strptime(EXPIRY_DATE_STR, "%Y-%m-%d").date()
                except:
                    exp_date = date(2030, 12, 31)
                
                if date.today() > exp_date and role != 'Admin':
                    st.error("❌ Mfumo umefikia ukomo wa matumizi. Tafadhali wasiliana na Mtengenezaji wa Mfumo.")
                else:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['role'] = role
                    st.success(f"Karibu, {username}")
                    st.rerun()
            else:
                st.error("⚠️ Username au Password sio sahihi!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR & MENU ---
display_logo(height=90, sidebar=True)
st.sidebar.markdown(f"<h3 style='text-align: center; color: #1e3a8a; margin-top: 5px; font-size: 18px;'>{SCHOOL_NAME}</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"👤 Mtumiaji: **{st.session_state['username']}** ({st.session_state['role']})")

if st.sidebar.button("Log Out", use_container_width=True):
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""
    st.rerun()

st.title(f"🏫 {SCHOOL_NAME}")
st.markdown("<p style='color:#64748b; font-size:16px;'>Mfumo wa Dahili na Usimamizi wa Mabweni</p>", unsafe_allow_html=True)
st.markdown("---")

menu = [
    "📊 Dashboard & Dorm Status", 
    "📈 Summary ya Vifaa & Dahili (Analytics)",
    "➕ Register New Student", 
    "🔍 View & Manage Records (Actions)", 
    "🛏️ Admin: Manage Dorm Capacity",
    "⚙️ User Management & Settings"
]
choice = st.sidebar.selectbox("MAIN MENU", menu)

def get_all_dorms():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM dorms", conn)
    conn.close()
    return df

# --- MENU 1: DASHBOARD ---
if choice == "📊 Dashboard & Dorm Status":
    st.subheader("📊 Muhtasari wa Shule na Mabweni")
    conn = sqlite3.connect(DB_NAME)
    df_students = pd.read_sql_query("SELECT * FROM students", conn)
    df_dorms = pd.read_sql_query("SELECT * FROM dorms", conn)
    
    total_active = len(df_students[df_students['status'] == 'Active'])
    total_transferred = len(df_students[df_students['status'] == 'Transferred'])
    total_graduated = len(df_students[df_students['status'] == 'Graduated'])
    total_dropout = len(df_students[df_students['status'] == 'Dropout'])
    
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        render_metric_card("Wanafunzi Active", total_active, bg_color="#10B981", text_color="#ffffff", icon="🧑‍🎓")
    with m_col2:
        render_metric_card("Waliohama (Transferred)", total_transferred, bg_color="#3B82F6", text_color="#ffffff", icon="🚪")
    with m_col3:
        render_metric_card("Waliofuzu (Graduated)", total_graduated, bg_color="#F59E0B", text_color="#ffffff", icon="🎓")
        
    m_col4, m_col5 = st.columns(2)
    with m_col4:
        render_metric_card("Waliacha Shule (Dropout)", total_dropout, bg_color="#EF4444", text_color="#ffffff", icon="⚠️")
    with m_col5:
        render_metric_card("Jumla ya Mabweni", len(df_dorms), bg_color="#6B7280", text_color="#ffffff", icon="🏢")
    
    st.markdown("---")
    st.subheader("🛏️ Live Dormitory Occupancy (Hali ya Mabweni)")
    
    dorm_status_data = []
    for index, row in df_dorms.iterrows():
        c = conn.cursor()
        c.execute('''
            SELECT COUNT(*) FROM students 
            WHERE bweni_id = ? AND status = 'Active' AND (tarehe_kuondoka IS NULL OR tarehe_kuondoka = '' OR tarehe_kuondoka = 'None')
        ''', (row['id'],))
        allocated = c.fetchone()[0]
        
        rem = row['capacity'] - allocated
        percentage_full = (allocated / row['capacity']) * 100 if row['capacity'] > 0 else 0
        
        dorm_status_data.append({
            "id": row['id'],
            "Jina la Bweni": row['dorm_name'],
            "Uwezo (Capacity)": row['capacity'],
            "Wanafunzi Waliopo": allocated,
            "Nafasi Zilizo Wazi": rem if rem >= 0 else 0,
            "Asilimia ya Ujazaji": f"{percentage_full:.1f}%",
            "Hali": "IMEJAA ❌" if rem <= 0 else "Inafaa ✅"
        })
    
    df_dorm_status = pd.DataFrame(dorm_status_data)
    st.dataframe(df_dorm_status.drop(columns=['id']), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔍 Orodha ya Wanafunzi na Vifaa Wanavyodaiwa")
    
    df_madeni = pd.read_sql_query('''
        SELECT students.admno, students.jina_mwanafunzi, students.class_form, students.comb, 
               dorms.dorm_name, students.pay_slip, students.rim, students.reki, students.jembe, 
               students.graph_2, students.hard_bloom, students.kwanja, students.squizer, 
               students.soft_broom, students.file_2, students.ndoo
        FROM students 
        LEFT JOIN dorms ON students.bweni_id = dorms.id
        WHERE students.status = 'Active'
    ''', conn)
    
    if df_madeni.empty:
        st.info("Hakuna wanafunzi walio 'Active' kwenye mfumo kwa sasa.")
    else:
        vifaa_check_list = ["pay_slip", "rim", "reki", "jembe", "graph_2", "hard_bloom", "kwanja", "squizer", "soft_broom", "file_2", "ndoo"]
        
        rows_madeni = []
        for index, row in df_madeni.iterrows():
            madeni_yake = []
            for kifaa in vifaa_check_list:
                if str(row[kifaa]).lower().strip() == 'haijaletwa':
                    madeni_yake.append(kifaa.upper().replace("_2", "").replace("_", " "))
            
            deni_text = ", ".join(madeni_yake) if madeni_yake else "Hana Deni ✅"
            
            rows_madeni.append({
                "Admission No": row['admno'],
                "Jina la Mwanafunzi": row['jina_mwanafunzi'],
                "Darasa": row['class_form'] if row['class_form'] else "Hajapangwa",
                "Combination": row['comb'] if row['comb'] else "-",
                "Bweni": row['dorm_name'] if pd.notna(row['dorm_name']) else "Kutwa (Day)",
                "Anachodaiwa Tu (Vifaa) curve": madeni_yake,
                "Anachodaiwa Tu (Vifaa)": deni_text
            })
            
        df_madeni_final = pd.DataFrame(rows_madeni)
        
        st.markdown("#### 🎯 Filter Orodha ya Wanafunzi")
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            filter_darasa = st.selectbox("Chuja kwa Darasa:", ["Zote"] + sorted(list(df_madeni_final['Darasa'].unique())))
        with fc2:
            filter_bweni = st.selectbox("Chuja kwa Bweni:", ["Zote"] + sorted(list(df_madeni_final['Bweni'].unique())))
        with fc3:
            search_query = st.text_input("✍️ Tafuta kwa jina au namba:", placeholder="Andika jina au admission no...")
        
        df_filtered = df_madeni_final
        if filter_darasa != "Zote":
            df_filtered = df_filtered[df_filtered['Darasa'] == filter_darasa]
        if filter_bweni != "Zote":
            df_filtered = df_filtered[df_filtered['Bweni'] == filter_bweni]
            
        if search_query:
            q = search_query.lower()
            df_filtered = df_filtered[
                df_filtered['Jina la Mwanafunzi'].str.lower().str.contains(q, na=False) |
                df_filtered['Admission No'].str.lower().str.contains(q, na=False) |
                df_filtered['Combination'].str.lower().str.contains(q, na=False)
            ]
            
        st.write(f"Wanafunzi waliopatikana kulingana na vigezo vyako: **{len(df_filtered)}**")
        st.dataframe(df_filtered.drop(columns=['Anachodaiwa Tu (Vifaa) curve']), use_container_width=True, hide_index=True)
        
        pdf_buffer = generate_madeni_pdf(df_filtered, SCHOOL_NAME)
        st.download_button(
            label="📥 Download Ripoti Hii ya Madeni Kama PDF",
            data=pdf_buffer,
            file_name=f"Ripoti_Madeni_Vifaa_{date.today().strftime('%Y-%m-%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
    conn.close()

# --- MENU 2: SUMMARY YA VIFAA & DAHILI (ANALYTICS) ---
elif choice == "📈 Summary ya Vifaa & Dahili (Analytics)":
    st.subheader("📈 Uchambuzi na Summary ya Kukusanya Vifaa Mashuleni")
    
    conn = sqlite3.connect(DB_NAME)
    df_st = pd.read_sql_query("SELECT * FROM students WHERE status='Active'", conn)
    conn.close()
    
    if df_st.empty:
        st.info("Hakuna data za wanafunzi walio hai ili kuzalisha summary.")
    else:
        st.markdown("#### 1. Item-Level Analysis (Muhtasari wa Makusanyo ya Kila Kifaa)")
        vifaa_cols = ["pay_slip", "rim", "reki", "jembe", "graph_2", "hard_bloom", "kwanja", "squizer", "soft_broom", "file_2", "ndoo"]
        
        summary_rows = []
        for col in vifaa_cols:
            imeletwa = len(df_st[df_st[col].str.lower().str.strip().isin(['imeletwa', '1', '2', '3'])])
            haijaletwa = len(df_st[df_st[col].str.lower().str.strip() == 'haijaletwa'])
            haleti = len(df_st[df_st[col].str.lower().str.strip() == 'haleti'])
            total = imeletwa + haijaletwa + haleti
            
            asilimia = (imeletwa / (total - haleti) * 100) if (total - haleti) > 0 else 0
            
            summary_rows.append({
                "Kifaa (Luggage Item)": col.upper().replace("_2", "").replace("_", " "),
                "Waliileta (✓)": imeletwa,
                "Bado Hawajaleta (✗)": haijaletwa,
                "Hawahusiki (H)": haleti,
                "Ufanisi (%)": f"{asilimia:.1f}%"
            })
            
        df_summary_vifaa = pd.DataFrame(summary_rows)
        st.dataframe(df_summary_vifaa, use_container_width=True, hide_index=True)
        
        ukusanyaji_pdf_buffer = generate_ukusanyaji_pdf(df_summary_vifaa, SCHOOL_NAME)
        st.download_button(
            label="📥 Download Ripoti ya Taarifa za Ukusanyaji Kama PDF",
            data=ukusanyaji_pdf_buffer,
            file_name=f"Ripoti_Ukusanyaji_Vifaa_{date.today().strftime('%Y-%m-%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        st.markdown("---")
        st.markdown("#### 2. Muhtasari wa Kiakademik (Dahili kwa Kila Kidato)")
        classes = ["Form 1", "Form 2", "Form 3", "Form 4", "Form 5", "Form 6"]
        class_summary = []
        for cls in classes:
            c_count = len(df_st[df_st['class_form'] == cls])
            if c_count > 0:
                class_summary.append({"Kidato (Class)": cls, "Jumla ya Wanafunzi": c_count})
        if class_summary:
            st.dataframe(pd.DataFrame(class_summary), use_container_width=True, hide_index=True)

# --- MENU 3: REGISTER NEW STUDENT ---
elif choice == "➕ Register New Student":
    st.subheader("➕ Sajili Wanafunzi")
    
    tab_single, tab_bulk = st.tabs(["📝 Fomu ya Mwanafunzi Mmoja", "📤 Bulk Upload kutoka Excel/CSV"])
    
    dorms_df = get_all_dorms()
    dorm_options = {row['dorm_name']: row['id'] for index, row in dorms_df.iterrows()}
    dorm_options["Day Student (Kutwa)"] = None
    
    status_options_vifaa = ["Imeletwa", "Haijaletwa", "Haleti", "1", "2", "3"]
    
    with tab_single:
        suggested_admno = get_next_admno()
        
        with st.form(key='admission_form', clear_on_submit=True):
            st.markdown("<h5 style='color:#1e3a8a;'>👤 1. TAARIFA ZA ADMISSION</h5>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                admno = st.text_input("ADMISSION NO *", value=suggested_admno)
                jina_mwanafunzi = st.text_input("Jina la Mwanafunzi *")
                class_form = st.selectbox("CLASS/FORM", ["Form 1", "Form 2", "Form 3", "Form 4", "Form 5", "Form 6"])
            with c2:
                comb = st.text_input("COMBINATION")
                tarehe_kuripoti = st.date_input("TAREHE YA KURIPOTI")
                tarehe_kuzaliwa = st.date_input("TAREHE YA KUZALIWA", value=datetime(2010, 1, 1))
            with c3:
                uraia = st.text_input("URAIA", value="Mtanzania")
                shule_aliyotoka = st.text_input("SHULE ALIYOTOKA")
                chaguo_bweni = st.selectbox("PANGA BWENI", list(dorm_options.keys()))
                
            st.markdown("<h5 style='color:#1e3a8a;'>⚙️ Hali ya Usajili (Status)</h5>", unsafe_allow_html=True)
            reg_status = st.selectbox("Hali ya Mwanafunzi (Status)", ["Active", "Transferred", "Graduated", "Dropout"])

            st.markdown("<h5 style='color:#1e3a8a;'>📞 2. WAZAZI & MAKAZI</h5>", unsafe_allow_html=True)
            c4, c5, c6 = st.columns(3)
            with c4:
                jina_baba_mlezi = st.text_input("JINA LA BABA / MLEZI")
            with c5:
                kazi_yake = st.text_input("KAZI YA BABA / MLEZI")
            with c6:
                simu = st.text_input("SIMU YAKE")
                mahali_alipotoka = st.text_input("MAHALI ALIPOTOKA")
                shule_anayokwenda = st.text_input("SHULE ANAYOKWENDA (Kama anahama)")

            st.markdown("<h5 style='color:#1e3a8a;'>🧹 3. HALI YA VIFAA</h5>", unsafe_allow_html=True)
            c7, c8, c9, c10 = st.columns(4)
            vifaa_list = ["PAY_SLIP", "RIM", "REKI", "JEMBE", "GRAPH_2", "HARD_BLOOM", "KWANJA", "SQUIZER", "SOFT_BROOM", "FILE_2", "NDOO"]
            vifaa_inputs = {}
            
            all_cols = [c7, c8, c9, c10]
            for i, kifaa in enumerate(vifaa_list):
                with all_cols[i % 4]:
                    vifaa_inputs[kifaa.lower()] = st.selectbox(f"{kifaa}", status_options_vifaa, index=1)

            submit = st.form_submit_button("Hifadhi Mwanafunzi", use_container_width=True)
            
            if submit:
                if not admno or not jina_mwanafunzi:
                    st.error("⚠️ ADMISSION NO na Jina la Mwanafunzi ni lazima!")
                else:
                    selected_id = dorm_options[chaguo_bweni]
                    try:
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO students (admno, jina_mwanafunzi, class_form, comb, tarehe_kuripoti, tarehe_kuzaliwa, uraia, jina_baba_mlezi, kazi_yake, simu, shule_aliyotoka, shule_anayokwenda, mahali_alipotoka, pay_slip, rim, reki, jembe, graph_2, hard_bloom, kwanja, squizer, soft_broom, file_2, ndoo, bweni_id, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (admno, jina_mwanafunzi, class_form, comb, str(tarehe_kuripoti), str(tarehe_kuzaliwa), uraia, jina_baba_mlezi, kazi_yake, simu, shule_aliyotoka, shule_anayokwenda, mahali_alipotoka, vifaa_inputs['pay_slip'], vifaa_inputs['rim'], vifaa_inputs['reki'], vifaa_inputs['jembe'], vifaa_inputs['graph_2'], vifaa_inputs['hard_bloom'], vifaa_inputs['kwanja'], vifaa_inputs['squizer'], vifaa_inputs['soft_broom'], vifaa_inputs['file_2'], vifaa_inputs['ndoo'], selected_id, reg_status))
                        conn.commit()
                        conn.close()
                        st.success(f"🟢 Mwanafunzi {jina_mwanafunzi} amesajiliwa kikamilifu na taarifa zimehifadhiwa!")
                        time.sleep(1.5)
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("⚠️ ADMISSION NO hii tayari ipo kwa mwanafunzi mwingine!")

    with tab_bulk:
        st.markdown("#### Pakia faili la Excel/CSV lenye orodha ya Wanafunzi")
        st.info("Hakikisha faili lako lina safu (columns) zenye majina: **admno** na **jina_mwanafunzi**.")
        up_file = st.file_uploader("Chagua faili la Excel au CSV", type=["xlsx", "csv"], key="bulk_student_upload")
        
        if up_file:
            df_u = pd.read_excel(up_file) if up_file.name.endswith('.xlsx') else pd.read_csv(up_file)
            st.write("Mvinyo wa Data Zako (Preview):")
            st.dataframe(df_u.head())
            
            if st.button("Hifadhi Wanafunzi Hawa Wote kwa Mkupuo", use_container_width=True):
                conn = sqlite3.connect(DB_NAME)
                saved_count = 0
                for _, r in df_u.iterrows():
                    a_no = str(r.get('admno', r.get('ADMISSION NO', ''))).strip()
                    jina = str(r.get('jina_mwanafunzi', r.get('Jina la Mwanafunzi', ''))).strip()
                    d_form = str(r.get('class_form', r.get('CLASS/FORM', 'Form 1'))).strip()
                    
                    if a_no and jina:
                        try:
                            c = conn.cursor()
                            c.execute('''
                                INSERT OR IGNORE INTO students (admno, jina_mwanafunzi, class_form, status, pay_slip, rim, reki, jembe, graph_2, hard_bloom, kwanja, squizer, soft_broom, file_2, ndoo) 
                                VALUES (?, ?, ?, 'Active', 'Haijaletwa', 'Haijaletwa', 'Haijaletwa', 'Haijaletwa', 'Haijaletwa', 'Haijaletwa', 'Haijaletwa', 'Haijaletwa', 'Haijaletwa', 'Haijaletwa', 'Haijaletwa')
                            ''', (a_no, jina, d_form))
                            saved_count += 1
                        except:
                            pass
                conn.commit()
                conn.close()
                st.success(f"🟢 Jumla ya wanafunzi {saved_count} wameingizwa na kuhifadhiwa kikamilifu kwenye mfumo!")
                time.sleep(1.5)
                st.rerun()

# --- MENU 4: VIEW & MANAGE RECORDS ---
elif choice == "🔍 View & Manage Records (Actions)":
    st.subheader("🔍 Usimamizi, Uhariri na Kufuta Wanafunzi")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query('''
        SELECT students.*, dorms.dorm_name FROM students 
        LEFT JOIN dorms ON students.bweni_id = dorms.id
    ''', conn)
    conn.close()
    
    if df.empty:
        st.info("Sajili haina wanafunzi kwa sasa.")
    else:
        st.markdown("#### 📥 Export Data za Usajili")
        csv_data = df.drop(columns=['id', 'bweni_id'], errors='ignore').to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data Zote Kama Excel (CSV File)",
            data=csv_data,
            file_name=f"Usajili_Wanafunzi_{date.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.markdown("---")
        
        search = st.text_input("Tafuta kwa Jina au ADMISSION NO:")
        if search:
            df = df[df['jina_mwanafunzi'].str.contains(search, case=False, na=False) | df['admno'].str.contains(search, case=False, na=False)]
            
        st.write("### Orodha ya Wanafunzi")
        st.dataframe(df.drop(columns=['id', 'bweni_id'], errors='ignore'), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("⚙️ Action Center: Edit au Futa (Delete) Mwanafunzi")
        
        selected_adm = st.selectbox("Chagua ADMNO ya mwanafunzi kufanya ACTION:", df['admno'].tolist())
        row_data = df[df['admno'] == selected_adm].iloc[0]
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            st.markdown(f"<div style='background-color:#fee2e2; padding:15px; border-radius:5px;'><strong>Eneo la Hatari:</strong> Kufuta kabisa rekodi ya mwanafunzi.</div>", unsafe_allow_html=True)
            if st.session_state['role'] == 'Admin':
                if st.button(f"🗑️ FUTA REKODI YA {selected_adm}", use_container_width=True):
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute("DELETE FROM students WHERE admno = ?", (selected_adm,))
                    conn.commit()
                    conn.close()
                    st.success("🟢 Rekodi ya mwanafunzi imefutwa kabisa na mabadiliko yamehifadhiwa!")
                    time.sleep(1.5)
                    st.rerun()
            else:
                st.info("Ni akaunti ya 'Admin' tu inayoruhusiwa kufuta kabisa wanafunzi.")

        with col_act2:
            st.info(f"ℹ️ **Mwanafunzi aliyechaguliwa:** {row_data['jina_mwanafunzi']} | **Hali ya sasa:** {row_data['status']}")
            
        st.markdown("#### ✏️ Hariri Taarifa Zote za Mwanafunzi Hapa chini")
        with st.form("edit_student_form"):
            st.markdown("<h5 style='color:#1e3a8a;'>👤 1. TAARIFA ZA ADMISSION & MASOMO</h5>", unsafe_allow_html=True)
            c_e1, c_e2, c_e3 = st.columns(3)
            with c_e1:
                e_name = st.text_input("Jina la Mwanafunzi", value=row_data['jina_mwanafunzi'])
                e_form = st.selectbox("Class/Form", ["Form 1", "Form 2", "Form 3", "Form 4", "Form 5", "Form 6"], index=["Form 1", "Form 2", "Form 3", "Form 4", "Form 5", "Form 6"].index(row_data['class_form']) if row_data['class_form'] in ["Form 1", "Form 2", "Form 3", "Form 4", "Form 5", "Form 6"] else 0)
                
                status_list = ["Active", "Transferred", "Graduated", "Dropout"]
                curr_status = row_data['status'] if row_data['status'] in status_list else "Active"
                e_status = st.selectbox("Status", status_list, index=status_list.index(curr_status))
            with c_e2:
                e_comb = st.text_input("Combination", value=row_data['comb'] if pd.notna(row_data['comb']) else "")
                
                try:
                    curr_rep_date = datetime.strptime(str(row_data['tarehe_kuripoti']), "%Y-%m-%d").date() if row_data['tarehe_kuripoti'] else date.today()
                except: curr_rep_date = date.today()
                try:
                    curr_birth_date = datetime.strptime(str(row_data['tarehe_kuzaliwa']), "%Y-%m-%d").date() if row_data['tarehe_kuzaliwa'] else date(2010, 1, 1)
                except: curr_birth_date = date(2010, 1, 1)
                
                e_tarehe_kuripoti = st.date_input("Tarehe ya Kuripoti", value=curr_rep_date)
                e_tarehe_kuzaliwa = st.date_input("Tarehe ya Kuzaliwa", value=curr_birth_date)
            with c_e3:
                e_uraia = st.text_input("Uraia", value=row_data['uraia'] if pd.notna(row_data['uraia']) else "Mtanzania")
                e_shule_aliyotoka = st.text_input("Shule Aliyotoka", value=row_data['shule_aliyotoka'] if pd.notna(row_data['shule_aliyotoka']) else "")
                
                dorms_df = get_all_dorms()
                d_map = {r['dorm_name']: r['id'] for i, r in dorms_df.iterrows()}
                d_map["Day Student (Kutwa)"] = None
                curr_d_name = row_data['dorm_name'] if pd.notna(row_data['dorm_name']) else "Day Student (Kutwa)"
                e_dorm = st.selectbox("Badili Bweni", list(d_map.keys()), index=list(d_map.keys()).index(curr_d_name) if curr_d_name in d_map else 0)

            st.markdown("<h5 style='color:#1e3a8a;'>📞 2. WAZAZI, MAKAZI & SAFARI</h5>", unsafe_allow_html=True)
            c_e4, c_e5, c_e6 = st.columns(3)
            with c_e4:
                e_jina_baba = st.text_input("Jina la Baba / Mlezi", value=row_data['jina_baba_mlezi'] if pd.notna(row_data['jina_baba_mlezi']) else "")
                e_kazi_yake = st.text_input("Kazi Yake", value=row_data['kazi_yake'] if pd.notna(row_data['kazi_yake']) else "")
            with c_e5:
                e_simu = st.text_input("Simu Yake", value=row_data['simu'] if pd.notna(row_data['simu']) else "")
                e_mahali_alipotoka = st.text_input("Mahali Alipotoka", value=row_data['mahali_alipotoka'] if pd.notna(row_data['mahali_alipotoka']) else "")
            with c_e6:
                e_shule_anayokwenda = st.text_input("Shule Anayokwenda (Kama anahama)", value=row_data['shule_anayokwenda'] if pd.notna(row_data['shule_anayokwenda']) else "")
                current_exit_date = row_data['tarehe_kuondoka'] if pd.notna(row_data['tarehe_kuondoka']) else ""
                e_exit_date = st.text_input("Tarehe ya Kuondoka (YYYY-MM-DD)", value=str(current_exit_date))

            st.markdown("<h5 style='color:#1e3a8a;'>🧹 3. HALI YA VIFAA (LUGGAGE STATUS)</h5>", unsafe_allow_html=True)
            c_e7, c_e8, c_e9, c_e10 = st.columns(4)
            vifaa_list = ["pay_slip", "rim", "reki", "jembe", "graph_2", "hard_bloom", "kwanja", "squizer", "soft_broom", "file_2", "ndoo"]
            vifaa_edit_inputs = {}
            
            all_edit_cols = [c_e7, c_e8, c_e9, c_e10]
            status_options_vifaa = ["Imeletwa", "Haijaletwa", "Haleti", "1", "2", "3"]
            
            for i, kifaa in enumerate(vifaa_list):
                with all_edit_cols[i % 4]:
                    curr_vifaa_val = str(row_data[kifaa]).strip().capitalize() if pd.notna(row_data[kifaa]) else "Haijaletwa"
                    if curr_vifaa_val not in status_options_vifaa:
                        if str(row_data[kifaa]).strip() in ["1", "2", "3"]:
                            curr_vifaa_val = str(row_data[kifaa]).strip()
                        else:
                            curr_vifaa_val = "Haijaletwa"
                    vifaa_edit_inputs[kifaa] = st.selectbox(f"{kifaa.upper().replace('_2','')}", status_options_vifaa, index=status_options_vifaa.index(curr_vifaa_val), key=f"edit_{kifaa}")

            save_btn = st.form_submit_button("💾 Hifadhi Mabadiliko Zote (Save All Student Data)", use_container_width=True)
            if save_btn:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute('''
                    UPDATE students 
                    SET jina_mwanafunzi=?, class_form=?, status=?, tarehe_kuondoka=?, bweni_id=?, comb=?,
                        tarehe_kuripoti=?, tarehe_kuzaliwa=?, uraia=?, shule_aliyotoka=?, jina_baba_mlezi=?,
                        kazi_yake=?, simu=?, mahali_alipotoka=?, shule_anayokwenda=?,
                        pay_slip=?, rim=?, reki=?, jembe=?, graph_2=?, hard_bloom=?, kwanja=?, squizer=?, soft_broom=?, file_2=?, ndoo=?
                    WHERE admno=?
                ''', (e_name, e_form, e_status, e_exit_date if e_exit_date.strip() != "" else None, d_map[e_dorm], e_comb,
                      str(e_tarehe_kuripoti), str(e_tarehe_kuzaliwa), e_uraia, e_shule_aliyotoka, e_jina_baba,
                      e_kazi_yake, e_simu, e_mahali_alipotoka, e_shule_anayokwenda,
                      vifaa_edit_inputs['pay_slip'], vifaa_edit_inputs['rim'], vifaa_edit_inputs['reki'], vifaa_edit_inputs['jembe'],
                      vifaa_edit_inputs['graph_2'], vifaa_edit_inputs['hard_bloom'], vifaa_edit_inputs['kwanja'], vifaa_edit_inputs['squizer'],
                      vifaa_edit_inputs['soft_broom'], vifaa_edit_inputs['file_2'], vifaa_edit_inputs['ndoo'], selected_adm))
                conn.commit()
                conn.close()
                st.success("🟢 database imesasishwa! Taarifa zote mpya zimehifadhiwa kikamilifu.")
                time.sleep(1.5)
                st.rerun()

# --- MENU 5: ADMIN DORM MANAGEMENT ---
elif choice == "🛏️ Admin: Manage Dorm Capacity":
    st.subheader("⚙️ Badili Uwezo (Capacity) wa Mabweni")
    df_d = get_all_dorms()
    st.dataframe(df_d, hide_index=True)
    
    with st.form("update_cap"):
        b_name = st.selectbox("Chagua Bweni la kubadilisha uwezo wake:", df_d['dorm_name'].tolist())
        n_cap = st.number_input("Weka Idadi Mpya ya Nafasi (Capacity):", min_value=1, value=60)
        u_btn = st.form_submit_button("Sasisha")
        if u_btn:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("UPDATE dorms SET capacity=? WHERE dorm_name=?", (n_cap, b_name))
            conn.commit()
            conn.close()
            st.success(f"🟢 Uwezo wa Bweni la {b_name} umesasishwa kuwa vitanda {n_cap} na kuhifadhiwa!")
            time.sleep(1.5)
            st.rerun()

# --- MENU 6: USER MANAGEMENT & SCHOOL SETTINGS ---
elif choice == "⚙️ User Management & Settings":
    st.subheader("⚙️ Mipangilio ya Mfumo na Usimamizi (Admin Settings)")
    
    if st.session_state['role'] != 'Admin':
        st.error("⚠️ Hauruhusiwi kuona ukurasa huu. Ni kwa ajili ya Admin Mkuu tu.")
    else:
        # TUMEONGEZA TAB YA TANO: "🚨 Reset System"
        tab_settings, tab_add_user, tab_manage_users, tab_export_backup, tab_import_backup, tab_reset_system = st.tabs([
            "🏢 Mipangilio ya Shule & Logo", 
            "➕ Sajili Mtumiaji Mpya", 
            "🔍 Tafuta & Hariri Watumiaji",
            "💾 Export Backup",
            "📥 Import Backup",
            "🚨 Reset System"
        ])
        
        # --- TAB 1: SCHOOL SETTINGS ---
        with tab_settings:
            st.markdown("### Mipangilio ya Shule na Mfumo")
            with st.form("school_settings_form"):
                current_sc_name = get_school_name()
                current_sc_expiry = get_setting('expiry_date', '2030-12-31')
                
                new_school_name_input = st.text_input("Jina la Shule la Sasa:", value=current_sc_name)
                logo_file = st.file_uploader("Pakia Nembo (Logo) ya Shule:", type=["png", "jpg", "jpeg"])
                
                try:
                    parsed_expiry = datetime.strptime(current_sc_expiry, "%Y-%m-%d").date()
                except:
                    parsed_expiry = date(2030, 12, 31)
                new_expiry_input = st.date_input("Mwisho wa Matumizi ya Mfumo (Expiry Date):", value=parsed_expiry)
                
                update_settings_btn = st.form_submit_button("💾 Hifadhi Mipangilio Zote")
                
                if update_settings_btn:
                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    c.execute("UPDATE settings SET value = ? WHERE key = 'school_name'", (new_school_name_input,))
                    c.execute("UPDATE settings SET value = ? WHERE key = 'expiry_date'", (str(new_expiry_input),))
                    
                    if logo_file is not None:
                        file_bytes = logo_file.read()
                        base64_logo = base64.b64encode(file_bytes).decode('utf-8')
                        c.execute("UPDATE settings SET value = ? WHERE key = 'school_logo'", (base64_logo,))
                    
                    conn.commit()
                    conn.close()
                    st.success("🟢 Mipangilio yote ya shule na Logo zimehifadhiwa kikamilifu!")
                    time.sleep(1.5)
                    st.rerun()

        # --- TAB 2: REGISTER NEW USER ---
        with tab_add_user:
            st.markdown("### Usajili wa Akaunti Mpya")
            with st.form("add_user_form", clear_on_submit=True):
                new_user = st.text_input("Username Mpya")
                new_pass = st.text_input("Password Mpya", type='password')
                new_role = st.selectbox("Nafasi yake (Role)", ["User", "Admin"])
                add_user_btn = st.form_submit_button("Sajili Mtumiaji")
                
                if add_user_btn and new_user and new_pass:
                    hashed_p = make_hashes(new_pass)
                    try:
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (new_user, hashed_p, new_role))
                        conn.commit()
                        conn.close()
                        st.success(f"🟢 Mtumiaji '{new_user}' amesajiliwa na kuhifadhiwa kikamilifu!")
                        time.sleep(1.5)
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("⚠️ Username hii tayari ipo!")

        # --- TAB 3: SEARCH & EDIT USERS ---
        with tab_manage_users:
            st.markdown("### Usimamizi, Uhariri na Kufuta Watumiaji")
            
            conn = sqlite3.connect(DB_NAME)
            df_users = pd.read_sql_query("SELECT id, username, role FROM users", conn)
            conn.close()
            
            search_user = st.text_input("Tafuta Mtumiaji kwa Username (Mfano: admin):")
            if search_user:
                df_users = df_users[df_users['username'].str.contains(search_user, case=False, na=False)]
                
            st.write("#### Orodha ya Watumiaji Waliopatikana")
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("⚙️ Action Center: Edit au Futa (Delete) Mtumiaji")
            
            user_list_options = df_users['username'].tolist()
            
            if not user_list_options:
                st.info("Hakuna mtumiaji aliyepatikana kwa jina hilo.")
            else:
                selected_user = st.selectbox("Chagua Username ya kufanya ACTION (Edit/Delete):", user_list_options)
                user_row_data = df_users[df_users['username'] == selected_user].iloc[0]
                
                col_u_act1, col_u_act2 = st.columns(2)
                with col_u_act1:
                    st.markdown(f"<div style='background-color:#fee2e2; padding:15px; border-radius:5px;'><strong>Eneo la Hatari:</strong> Kufuta kabisa akaunti ya mtumiaji kwenye mfumo.</div>", unsafe_allow_html=True)
                    if st.button(f"🗑️ FUTA KABISA AKAUNTI YA '{selected_user}'", use_container_width=True):
                        if selected_user.lower() == "admin":
                            st.error("❌ Huwezi kuifuta akaunti kuu ya 'admin' ya mfumo!")
                        else:
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("DELETE FROM users WHERE id=?", (int(user_row_data['id']),))
                            conn.commit()
                            conn.close()
                            st.success(f"🟢 Akaunti ya '{selected_user}' imefutwa na kuhifadhiwa kikamilifu!")
                            time.sleep(1.5)
                            st.rerun()
                
                with col_u_act2:
                    st.info(f"ℹ️ **Mtumiaji aliyechaguliwa:** {selected_user} | **Role ya sasa:** {user_row_data['role']}")
                    
                st.markdown("#### ✏️ Hariri Akaunti Hapa chini")
                with st.form("edit_user_form_tab_final"):
                    edit_username = st.text_input("Badili Username", value=user_row_data['username'])
                    edit_password = st.text_input("Weka Password Mpya (Acha wazi kama hubadili)", type='password', placeholder="Acha wazi kama hubadili neno la siri")
                    
                    role_options = ["User", "Admin"]
                    edit_role = st.selectbox("Badili Role", role_options, index=role_options.index(user_row_data['role']))
                    
                    save_user_changes = st.form_submit_button("💾 Hifadhi Mabadiliko ya Mtumiaji (Save Changes)", use_container_width=True)
                    
                    if save_user_changes:
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        if edit_password.strip() != "":
                            new_hashed_p = make_hashes(edit_password)
                            c.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?", (edit_username, new_hashed_p, edit_role, int(user_row_data['id'])))
                        else:
                            c.execute("UPDATE users SET username=?, role=? WHERE id=?", (edit_username, edit_role, int(user_row_data['id'])))
                        conn.commit()
                        conn.close()
                        st.success("🟢 Taarifa za akaunti zimesasishwa vizuri na kuhifadhiwa!")
                        time.sleep(1.5)
                        st.rerun()

        # --- TAB 4: EXPORT BACKUP ---
        with tab_export_backup:
            st.markdown("### 💾 Pakua Faili la Mfumo la Backup (Backup Database)")
            st.info("Kipengele hiki kinakuruhusu kupakua database yote ya mfumo kwa usalama kama backup.")
            
            if os.path.exists(DB_NAME):
                with open(DB_NAME, "rb") as f:
                    db_bytes = f.read()
                st.download_button(
                    label="💾 Download Mfumo wa Database Sasa (.db File)",
                    data=db_bytes,
                    file_name=f"Backup_Admission_System_{date.today().strftime('%Y-%m-%d')}.db",
                    mime="application/octet-stream",
                    use_container_width=True
                )
            else:
                st.error("Database haijapatikana kwa sasa hivi.")

        # --- TAB 5: IMPORT BACKUP ---
        with tab_import_backup:
            st.markdown("### 📥 Pandisha Faili la Mfumo la Backup (Restore Database)")
            st.warning("⚠️ Tahadhari: Kupandisha database mpya kutafuta kabisa taarifa zote zilizopo sasa hivi na kuweka za backup ile uliyoipandisha.")
            
            uploaded_db = st.file_uploader("Chagua faili la Database ya zamani (.db)", type=["db"])
            if uploaded_db is not None:
                if st.button("📥 Rudisha Taarifa Zote (Restore/Import Backup Sasa)", use_container_width=True):
                    with open(DB_NAME, "wb") as f:
                        f.write(uploaded_db.getbuffer())
                    st.success("🟢 Mfumo wa Database umerudishwa kikamilifu kutoka kwenye Backup!")
                    time.sleep(1.5)
                    st.rerun()

        # --- TAB 6: 🚨 RESET SYSTEM (MPYA) ---
        with tab_reset_system:
            st.markdown("### 🚨 Reset Mfumo Mzima (Futa Data Zote za Wanafunzi)")
            st.error("⚠️ TAHADHARI KUBWA: Kitendo hiki kitafuta wanafunzi wote kabisa kwenye mfumo na kurudisha uwezo wa mabweni kuwa 60. Hakitafuta akaunti za watumiaji.")
            st.info("Inashauriwa kupakua kwanza Backup (kwenye tab ya 'Export Backup') kabla ya kufanya reset.")
            
            with st.form("reset_system_secure_form"):
                confirm_word = st.text_input("Andika neno la ushirikiano 'RESET' (kwa herufi kubwa):")
                admin_password_check = st.text_input("Weka Password yako ya sasa ya Admin ili kuthibitishe:", type="password")
                
                reset_action_btn = st.form_submit_button("💥 ANZA RESET YA MFUMO")
                
                if reset_action_btn:
                    if confirm_word != "RESET":
                        st.error("❌ Haujaandika neno 'RESET' kwa usahihi!")
                    elif not admin_password_check:
                        st.error("❌ Tafadhali weka neno lako la siri (Password) ili kuendelea.")
                    else:
                        # Thibitisha kama password ya sasa ni sahihi
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute('SELECT password FROM users WHERE username = ?', (st.session_state['username'],))
                        admin_data = c.fetchone()
                        
                        if admin_data and check_hashes(admin_password_check, admin_data[0]):
                            try:
                                # 1. Futa wanafunzi wote
                                c.execute("DELETE FROM students")
                                # 2. Set capacity ya mabweni kuwa default (60)
                                c.execute("UPDATE dorms SET capacity = 60")
                                conn.commit()
                                st.success("💥 Mfumo umefutwa na kuanzishwa upya kikamilifu! Data zote za wanafunzi zimeondolewa.")
                                time.sleep(2.0)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Imeshindikana kufanya reset: {e}")
                            finally:
                                conn.close()
                        else:
                            conn.close()
                            st.error("❌ Password uliyoweka sio sahihi! Reset imesitishwa.")