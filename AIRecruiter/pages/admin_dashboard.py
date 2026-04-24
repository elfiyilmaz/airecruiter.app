import streamlit as st
import pandas as pd
import sqlite3
import os
import uuid
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

st.set_page_config(page_title="TalentLens HR Admin", page_icon="📈", layout="wide")

# ==========================================================
# 🎨 COMPLETE REDESIGN (ENGLISH CSS)
# ==========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;600;700&display=swap');
.stApp { background: linear-gradient(-45deg, #050b14, #0a192f, #020c1b, #112240); background-size: 400% 400%; animation: gradientBG 15s ease infinite; color: #e6f1ff; font-family: 'Rajdhani', sans-serif;}
@keyframes gradientBG { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

.glass-card { background: rgba(2, 12, 27, 0.7); padding: 30px; border-radius: 15px; border: 1px solid rgba(100, 255, 218, 0.2); box-shadow: 0 0 20px rgba(0, 0, 0, 0.5); backdrop-filter: blur(10px); margin-bottom: 20px;}
.metric-card { background: rgba(100, 255, 218, 0.05); border-left: 4px solid #64ffda; padding: 20px; border-radius: 10px; text-align: center; transition: transform 0.3s ease;}
.metric-card:hover { transform: translateY(-5px); background: rgba(100, 255, 218, 0.1); }
.text-cyan { color: #64ffda; font-family: 'Orbitron', sans-serif; }
.text-purple { color: #b392f0; font-family: 'Orbitron', sans-serif; }

/* =========================================
   🔥 SIDEBAR (SOL MENÜ) MODERN REDESIGN 🔥
   ========================================= */
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020c1b 0%, #050b14 100%) !important;
    border-right: 1px solid rgba(100, 255, 218, 0.1) !important;
}

.sidebar-header {
    text-align: center;
    padding: 30px 15px 20px 15px;
    background: rgba(100, 255, 218, 0.02);
    border-radius: 15px;
    border: 1px solid rgba(100, 255, 218, 0.08);
    margin: -10px -10px 30px -10px;
}
.sidebar-logo {
    font-family: 'Orbitron', sans-serif;
    color: #64ffda;
    margin: 0;
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: 2px;
}
.sidebar-user-card {
    display: inline-block;
    background: rgba(179, 146, 240, 0.08);
    border: 1px solid rgba(179, 146, 240, 0.4);
    padding: 7px 25px;
    border-radius: 30px;
    margin-top: 15px;
}
.sidebar-username {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.95rem;
    color: #b392f0;
    font-weight: 700;
}

.stRadio > div[role="radiogroup"] { gap: 15px; }
.stRadio > div[role="radiogroup"] > label {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 15px 20px !important;
    border-radius: 12px !important;
    cursor: pointer;
    transition: all 0.3s ease !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #cbd5e1 !important;
    margin: 0 !important;
}
.stRadio > div[role="radiogroup"] > label:hover {
    background: rgba(100, 255, 218, 0.08);
    border-color: #64ffda;
    transform: translateX(8px);
    box-shadow: 0 0 15px rgba(100, 255, 218, 0.15);
}

[data-testid="stSidebar"] div.stButton > button {
    border: 1px solid #ef4444 !important;
    color: #ef4444 !important;
    background: transparent !important;
    border-radius: 12px !important;
    padding: 12px !important;
    transition: all 0.3s ease !important;
    font-family: 'Orbitron', sans-serif;
    font-weight: bold;
    letter-spacing: 1px;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: rgba(239, 68, 68, 0.1) !important;
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.3) !important;
    transform: translateY(-2px);
}

.stTabs [data-baseweb="tab-list"] { background-color: transparent; gap: 10px; }
.stTabs [data-baseweb="tab"] { font-family: 'Orbitron', sans-serif; color: #cbd5e1; border-radius: 8px 8px 0 0; padding: 10px 20px; }
.stTabs [aria-selected="true"] { background-color: rgba(100, 255, 218, 0.1) !important; color: #64ffda !important; border-bottom: 2px solid #64ffda !important; }

.css-1ht1j4w p, .css-1ht1j4w h3 { color: #cbd5e1 !important; }
.stSuccess { color: #10b981 !important; background-color: rgba(16, 185, 129, 0.1) !important; }
.stSuccess a { color: #10b981 !important; text-decoration: underline; }

/* 📝 YENİ: AI Rapor Kutusu Tasarımı */
.ai-report-box { 
    background: rgba(179, 146, 240, 0.08); 
    border-left: 4px solid #b392f0; 
    padding: 20px; 
    border-radius: 0 10px 10px 0; 
    margin-top: 10px; 
    font-size: 1.1rem; 
    color: #e2e8f0; 
    line-height: 1.6; 
}
</style>
""", unsafe_allow_html=True)


# ---------------- 📧 MAIL GÖNDERME FONKSİYONU ----------------
def send_interview_email(candidate_email, candidate_name, token, role, language):
    sender_email = "elif34yzl@gmail.com"
    sender_password = "qoce cpab hmue uqlz"
    link = f"http://localhost:8501/?token={token}"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'TalentLens AI - Video Interview Invitation: {role}'
    msg['From'] = sender_email
    msg['To'] = candidate_email

    html = f"""
    <html>
    <head></head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333333; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f7f6;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="background-color: #0a192f; padding: 30px; text-align: center;">
                <h1 style="color: #64ffda; margin: 0; font-family: 'Courier New', Courier, monospace; letter-spacing: 2px;">TALENTLENS AI</h1>
            </div>
            <div style="padding: 40px 30px;">
                <p style="font-size: 16px; margin-top: 0;">Dear <strong>{candidate_name}</strong>,</p>
                <p style="font-size: 15px; color: #555555;">Your application for the position at our company has been positively evaluated.</p>
                <p style="font-size: 15px; color: #555555;">You are invited to the next stage of our recruitment process: an AI-powered video interview.</p>

                <div style="background-color: #f8f9fa; border-left: 4px solid #b392f0; padding: 15px 20px; margin: 30px 0; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0 0 10px 0; font-weight: bold; color: #112240;">📌 Important Pre-Interview Reminders:</p>
                    <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #555555;">
                        <li style="margin-bottom: 5px;">Your interview will be conducted in: <strong>{language}</strong></li>
                        <li style="margin-bottom: 5px;">Please ensure you are in a quiet and well-lit environment.</li>
                        <li style="margin-bottom: 5px;">Make sure to allow your browser camera access.</li>
                        <li><strong>ATTENTION:</strong> Exam security is active. Switching tabs during the interview will automatically terminate your session.</li>
                    </ul>
                </div>

                <div style="text-align: center; margin: 40px 0;">
                    <a href="{link}" style="background-color: #64ffda; color: #0a192f; padding: 14px 30px; text-decoration: none; font-weight: bold; border-radius: 6px; font-size: 16px; display: inline-block;">Start Interview</a>
                </div>

                <hr style="border: none; border-top: 1px solid #eeeeee; margin: 30px 0;">
                <p style="font-size: 14px; color: #555555; margin: 0;">We wish you success,<br><strong>Human Resources Department</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, candidate_email, msg.as_string())
        return True
    except Exception as e:
        print("Mail Error:", e)
        return False


# --- AUTHORIZED USERS ---
ADMIN_USERS = {"elif": "elif2204"}

if "admin_logged_in" not in st.session_state: st.session_state.admin_logged_in = False
if "current_admin" not in st.session_state: st.session_state.current_admin = ""

# ==========================================================
# 1. LOGIN SCREEN
# ==========================================================
if not st.session_state.admin_logged_in:
    st.write("<br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(
            "<div class='glass-card'><h1 style='margin:0; text-align:center;'><span class='text-cyan'>TALENTLENS</span> HR LOGIN</h1><p style='color:#cbd5e1; text-align:center; margin-bottom:30px;'>Please enter your admin credentials.</p>",
            unsafe_allow_html=True)
        with st.form("admin_login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log In to System", use_container_width=True)
            if submit:
                if u in ADMIN_USERS and ADMIN_USERS[u] == p:
                    st.session_state.admin_logged_in = True
                    st.session_state.current_admin = u
                    st.rerun()
                else:
                    st.error("❌ Incorrect username or password!")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================================
# 2. ADMIN PORTAL
# ==========================================================
else:
    st.sidebar.markdown(f"""
    <div class='sidebar-header'>
        <h1 class='sidebar-logo'>TALENTLENS</h1>
        <p style='color: #8892b0; margin: 5px 0 0 0; font-size: 0.9rem; letter-spacing: 2px;'>ADMIN PORTAL</p>
        <div class='sidebar-user-card'>
            <span class='sidebar-username'>👤 Authorized: {st.session_state.current_admin.upper()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    admin_menu = st.sidebar.radio("NAVİGASYON", ["🏠 Overview", "✉️ Invite Candidate", "👥 Candidate Review Center"],
                                  label_visibility="hidden")

    st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Sistemi Kapat", use_container_width=True):
        st.session_state.admin_logged_in = False
        st.session_state.current_admin = ""
        st.rerun()

    # --- VERİTABANI BAĞLANTISI ---
    df_results = pd.DataFrame()
    df_candidates = pd.DataFrame()

    current_admin_dir_db = os.path.dirname(os.path.abspath(__file__))
    project_root_dir_db = os.path.dirname(current_admin_dir_db)
    db_path = os.path.join(project_root_dir_db, "interview.db")

    if not os.path.exists(db_path):
        db_path = "interview.db"

    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        try:
            c.execute("ALTER TABLE candidates ADD COLUMN language TEXT DEFAULT 'English'")
            conn.commit()
        except:
            pass

        try:
            c.execute("ALTER TABLE candidates ADD COLUMN ai_summary TEXT DEFAULT ''")
            conn.commit()
        except:
            pass

        try:
            df_results = pd.read_sql_query("SELECT * FROM results", conn)
        except:
            pass
        try:
            df_candidates = pd.read_sql_query("SELECT * FROM candidates", conn)
        except:
            pass
        conn.close()

    # ---------------- MENÜ 1: GENEL BAKIŞ (OVERVIEW) ----------------
    if admin_menu == "🏠 Overview":
        st.markdown("<h1 class='text-cyan'>OVERVIEW</h1>", unsafe_allow_html=True)
        st.write("Below is a summary of the current recruitment statistics in your system.")

        total_c = len(df_candidates)
        completed_c = len(df_candidates[df_candidates['status'] == 'Completed']) if not df_candidates.empty else 0
        disqualified_c = len(df_candidates[df_candidates['status'] == 'Disqualified']) if not df_candidates.empty else 0
        pending_c = len(df_candidates[df_candidates['status'] == 'Pending']) if not df_candidates.empty else 0
        avg_score = df_results['score'].mean() if not df_results.empty else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown(
            f"<div class='metric-card'><h4 style='margin:0; color:#cbd5e1;'>Total Candidates</h4><h1 class='text-cyan' style='margin:0;'>{total_c}</h1></div>",
            unsafe_allow_html=True)
        c2.markdown(
            f"<div class='metric-card' style='border-color:#10b981;'><h4 style='margin:0; color:#cbd5e1;'>Completed</h4><h1 style='margin:0; color:#10b981;'>{completed_c}</h1></div>",
            unsafe_allow_html=True)
        c3.markdown(
            f"<div class='metric-card' style='border-color:#f59e0b;'><h4 style='margin:0; color:#cbd5e1;'>Pending</h4><h1 style='margin:0; color:#f59e0b;'>{pending_c}</h1></div>",
            unsafe_allow_html=True)
        c4.markdown(
            f"<div class='metric-card' style='border-color:#ef4444; background: rgba(239, 68, 68, 0.05);'><h4 style='margin:0; color:#cbd5e1;'>Disqualified</h4><h1 style='margin:0; color:#ef4444;'>{disqualified_c}</h1></div>",
            unsafe_allow_html=True)
        c5.markdown(
            f"<div class='metric-card' style='border-color:#b392f0;'><h4 style='margin:0; color:#cbd5e1;'>Avg. AI Score</h4><h1 style='margin:0; color:#b392f0;'>{avg_score:.1f}</h1></div>",
            unsafe_allow_html=True)

    # ---------------- MENÜ 2: ADAY DAVET ET (INVITE CANDIDATE) ----------------
    elif admin_menu == "✉️ Invite Candidate":
        st.markdown("<h1 class='text-cyan'>NEW CANDIDATE INVITATION</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.write("Enter the candidate's details to create a unique single-use interview link and send it via email.")

        with st.form("invite_form_admin"):
            col1, col2 = st.columns(2)
            with col1:
                inv_name = st.text_input("Candidate Full Name")
            with col2:
                inv_email = st.text_input("Candidate Email Address")

            col3, col4 = st.columns(2)
            with col3:
                inv_role = st.selectbox("Position Applied For", ["Computer Engineer", "Human Resources", "General"])
            with col4:
                inv_language = st.selectbox("Interview Language (AI Prompts will use this)",
                                            ["English", "Türkçe", "Deutsch", "Español", "Français"])

            st.write("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("📩 Send Interview Invitation", type="primary")

            if submitted:
                if inv_name and inv_email:
                    new_token = str(uuid.uuid4())

                    conn = sqlite3.connect(db_path)
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO candidates (token, name, email, role, status, language, ai_summary) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (new_token, inv_name, inv_email, inv_role, "Pending", inv_language, ""))
                    conn.commit()
                    conn.close()

                    with st.spinner("Email sending... Please wait."):
                        if send_interview_email(inv_email, inv_name, new_token, inv_role, inv_language):
                            st.success(f"✅ Success! An interview invitation has been sent to {inv_name}.")
                            st.info(f"Manual System Connection Link: http://localhost:8501/?token={new_token}")
                        else:
                            st.error(
                                "⚠️ Email could not be sent. Please check your secure password or connection. Link created.")
                else:
                    st.warning("Please fill in the name and email fields.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- MENÜ 3: ADAY İNCELEME MERKEZİ (REVIEW CENTER) ----------------
    elif admin_menu == "👥 Candidate Review Center":
        st.markdown("<h1 class='text-purple'>CANDIDATE REVIEW CENTER</h1>", unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(
            ["🟢 Completed Interviews (Report & Video)", "🟡 Pending Candidates", "🔴 Disqualified 🚨"])

        with tab1:
            if not df_candidates.empty:
                completed_list = df_candidates[df_candidates['status'] == 'Completed']
                if not completed_list.empty:
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)

                    selected_cand_name = st.selectbox("Select Candidate to Review:", completed_list['name'].tolist())
                    cand_info = completed_list[completed_list['name'] == selected_cand_name].iloc[0]

                    cand_token = cand_info['token']
                    cand_role = cand_info['role']
                    cand_email = cand_info['email']

                    cand_language = cand_info.get('language', 'English')
                    if pd.isna(cand_language): cand_language = "English"

                    cand_summary = cand_info.get('ai_summary', '')
                    if pd.isna(cand_summary) or cand_summary == "":
                        cand_summary = "AI Assessment Report is pending or could not be generated."

                    c_results = df_results[df_results[
                                               'candidate_token'] == cand_token] if 'candidate_token' in df_results.columns else pd.DataFrame()

                    # 🚨 DÜZELTME: Hem MP4 hem de WEBM araması yapıyoruz ki hiçbir video kaçmasın!
                    expected_filename_webm = f"vid_{cand_token}.webm"
                    expected_filename_mp4 = f"vid_{cand_token}.mp4"

                    current_admin_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root_dir = os.path.dirname(current_admin_dir)

                    paths_to_check = [
                        os.path.join(project_root_dir, "recorded_videos", expected_filename_webm),
                        os.path.join(project_root_dir, "recorded_videos", expected_filename_mp4),
                        os.path.join(os.getcwd(), "recorded_videos", expected_filename_webm),
                        os.path.join(os.getcwd(), "recorded_videos", expected_filename_mp4)
                    ]

                    video_file = None
                    for p in paths_to_check:
                        if os.path.exists(p):
                            video_file = p
                            break

                    avg_tech = c_results['score'].mean() if not c_results.empty else 0
                    avg_emo = c_results['emotion'].mean() if not c_results.empty else 0

                    st.markdown("---")
                    st.write(f"### 📋 Candidate Profile: {selected_cand_name}")
                    st.write(
                        f"**Position:** {cand_role} | **Language:** {cand_language} | **Email:** {cand_email} | **Avg. Score:** {avg_tech:.1f}")
                    st.write("<br>", unsafe_allow_html=True)

                    col_vid, col_ai = st.columns([1, 1], gap="large")

                    with col_vid:
                        st.markdown("<h4 class='text-cyan'>🎬 Interview Video Recording</h4>", unsafe_allow_html=True)

                        if video_file:
                            try:
                                with open(video_file, "rb") as vf:
                                    video_bytes = vf.read()

                                # Formatı dosyanın uzantısına göre otomatik belirliyoruz
                                v_format = "video/mp4" if video_file.endswith(".mp4") else "video/webm"
                                st.video(video_bytes, format=v_format)
                            except Exception as e:
                                st.error(f"Video okuma hatası: {e}")
                        else:
                            st.warning(
                                f"⚠️ This candidate's video file could not be found physically on the server. (It might not have been recorded due to a camera issue).")
                            st.info(f"Debug Info - Evaluated paths:\n1. {paths_to_check[0]}\n2. {paths_to_check[1]}")

                        st.markdown("<br><h4 class='text-purple'>📝 AI Executive Summary</h4>", unsafe_allow_html=True)
                        st.markdown(f"<div class='ai-report-box'>{cand_summary}</div>", unsafe_allow_html=True)

                    with col_ai:
                        st.markdown("<h4 class='text-purple'>🤖 AI Technical Analysis</h4>", unsafe_allow_html=True)
                        if not c_results.empty:
                            st.line_chart(c_results.set_index("question")["score"], color="#64ffda")
                            st.markdown("<h4 class='text-purple'>🧘 Stress & Emotion Stability Analysis</h4>",
                                        unsafe_allow_html=True)
                            st.bar_chart(c_results.set_index("question")["emotion"], color="#b392f0")
                        else:
                            st.info("No AI data found for this candidate.")

                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("No candidates have completed their interview yet.")
            else:
                st.info("No candidates are currently registered in the system.")

        with tab2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.write("### Candidates Invited But Have Not Yet Completed Interview")
            if not df_candidates.empty:
                pending_list = df_candidates[df_candidates['status'] == 'Pending']
                if not pending_list.empty:
                    display_cols = ['name', 'email', 'role']
                    if 'language' in pending_list.columns: display_cols.append('language')
                    st.dataframe(pending_list[display_cols], use_container_width=True, hide_index=True)
                else:
                    st.success("You have no pending candidates! Everyone has completed their interview.")
            else:
                st.info("No candidates are currently registered in the system.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab3:
            st.markdown("<div class='glass-card' style='border-color: #ef4444;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #ef4444;'>🚨 Disqualified Candidates (Rule Violations)</h3>",
                        unsafe_allow_html=True)
            st.write(
                "Candidates listed below have been disqualified from the interview process due to cheating or violating exam protocols (e.g., switching browser tabs).")
            if not df_candidates.empty:
                disq_list = df_candidates[df_candidates['status'] == 'Disqualified']
                if not disq_list.empty:
                    display_cols = ['name', 'email', 'role']
                    if 'language' in disq_list.columns: display_cols.append('language')
                    st.dataframe(disq_list[display_cols], use_container_width=True, hide_index=True)
                else:
                    st.success("Great! No candidates have been disqualified for rule violations.")
            else:
                st.info("No candidates are currently registered in the system.")
            st.markdown("</div>", unsafe_allow_html=True)