import streamlit as st
import streamlit.components.v1 as components
import os
import time
import cv2
import pandas as pd
import base64
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
from audio_recorder_streamlit import audio_recorder

# ==========================================================
# 🧩 KENDİ MODÜLLERİMİZİ İÇERİ AKTARIYORUZ
# ==========================================================
from database.db import init_db
from modules.interview_ai import get_dynamic_questions_from_ai, evaluate_interview_with_ai

# ---------------- SETUP & DIRECTORY CHECK ----------------
load_dotenv()
st.set_page_config(page_title="TalentLens AI | Interview", page_icon="🧿", layout="wide")

# 🚨 DÜZELTME: Mutlak Yol (Absolute Path) ile klasör garantisi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, "recorded_videos"), exist_ok=True)
init_db()


# ---------------- 🖼️ SYSTEM LOGO ----------------
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""


LOGO_URL = f"data:image/png;base64,{get_base64_of_bin_file('logo.png')}" if get_base64_of_bin_file(
    'logo.png') else "https://resmim.net/cdn/2026/04/05/CCQO5o.png"

# ==========================================================
# 🔑 TOKEN VALIDATION & CANDIDATE SETUP
# ==========================================================
url_token = st.query_params.get("token")

if not url_token:
    st.markdown(
        "<style>[data-testid='stSidebarNav'] {display: none !important;}</style><div style='display:flex; justify-content:center; align-items:center; height:80vh;'><div style='background: rgba(239, 68, 68, 0.1); padding: 50px; border-radius: 20px; border: 2px solid #ef4444; text-align:center;'><h1 style='color: #ef4444; margin: 0;'>🚫 ACCESS DENIED</h1><p style='color: #cbd5e1; margin-top: 20px;'>No valid interview link found.</p></div></div>",
        unsafe_allow_html=True)
    st.stop()

db_path = os.path.join(BASE_DIR, 'interview.db')
conn = sqlite3.connect(db_path)
candidate_row = pd.read_sql_query(f"SELECT * FROM candidates WHERE token='{url_token}'", conn)
conn.close()

if candidate_row.empty:
    st.markdown(
        "<style>[data-testid='stSidebarNav'] {display: none !important;}</style><div style='display:flex; justify-content:center; align-items:center; height:80vh;'><div style='background: rgba(239, 68, 68, 0.1); padding: 50px; border-radius: 20px; border: 2px solid #ef4444; text-align:center;'><h1 style='color: #ef4444; margin: 0;'>🚫 INVALID LINK</h1><p style='color: #cbd5e1; margin-top: 20px;'>This link is incorrect or removed.</p></div></div>",
        unsafe_allow_html=True)
    st.stop()

c_lang = candidate_row.iloc[0]['language'] if 'language' in candidate_row.columns else 'English'

candidate_info = {
    "token": candidate_row.iloc[0]['token'],
    "name": candidate_row.iloc[0]['name'],
    "role": candidate_row.iloc[0]['role'],
    "status": candidate_row.iloc[0]['status'],
    "language": c_lang
}

if candidate_info['status'] == "Completed":
    st.markdown(
        "<style>[data-testid='stSidebarNav'] {display: none !important;}</style><div style='display:flex; justify-content:center; align-items:center; height:80vh;'><div style='background: rgba(16, 185, 129, 0.1); padding: 60px; border-radius: 20px; border: 2px solid #10b981; text-align:center; box-shadow: 0 0 30px rgba(16, 185, 129, 0.2); width: 80%;'><h1 style='color: #10b981; font-size: 3rem; margin: 0;'>✅ INTERVIEW COMPLETED</h1><p style='color: #cbd5e1; font-size: 1.2rem; margin-top: 20px;'>You have already completed this interview. Your results have been sent to the HR department.</p></div></div>",
        unsafe_allow_html=True)
    st.stop()

if candidate_info['status'] == "Disqualified":
    st.markdown(
        "<style>[data-testid='stSidebarNav'] {display: none !important;}</style><div style='display:flex; justify-content:center; align-items:center; height:80vh;'><div style='background: rgba(239, 68, 68, 0.1); padding: 60px; border-radius: 20px; border: 2px solid #ef4444; text-align:center; width: 80%;'><h1 style='color: #ef4444; font-size: 3rem; margin: 0;'>🚨 SESSION LOCKED</h1><p style='color: #cbd5e1; font-size: 1.2rem; margin-top: 20px;'>You have been disqualified for violating exam rules. Please contact HR.</p></div></div>",
        unsafe_allow_html=True)
    st.stop()

# 🚨 DÜZELTME: Tarayıcıların en sevdiği WEBM formatına dönüyoruz.
CANDIDATE_VIDEO_PATH = os.path.join(BASE_DIR, "recorded_videos", f"vid_{candidate_info['token']}.webm")

# ==========================================================
# 🚀 CAMERA CLASS (HD VIDEO & MULTI-FACE DETECTION)
# ==========================================================
if 'CAMERA_STATUS' not in globals():
    global CAMERA_STATUS
    CAMERA_STATUS = {"stage": "camera_test"}


class ContinuousFaceTracker(VideoTransformerBase):
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.filename = CANDIDATE_VIDEO_PATH
        self.writer = None

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
        status = CAMERA_STATUS.get("stage", "camera_test")

        if len(faces) == 0:
            cv2.rectangle(img, (0, 0), (img.shape[1], img.shape[0]), (0, 0, 255), 10)
            cv2.putText(img, "WARNING: NO FACE DETECTED!", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        elif len(faces) > 1:
            cv2.rectangle(img, (0, 0), (img.shape[1], img.shape[0]), (0, 0, 255), 10)
            cv2.putText(img, "WARNING: MULTIPLE FACES!", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)
        else:
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (100, 255, 218), 2)

        if status in ["prep", "record"]:
            if self.writer is None:
                h, w = img.shape[:2]
                # 🚨 DÜZELTME: vp80 Codec Streamlit için en stabil olandır.
                self.writer = cv2.VideoWriter(self.filename, cv2.VideoWriter_fourcc(*'vp80'), 20.0, (w, h))
            self.writer.write(img)
        else:
            if self.writer is not None:
                self.writer.release()
                self.writer = None

        return img

    # 🚨 DÜZELTME: Kamerayı zorla kapatıp dosyayı güvence altına alan yıkıcı metotlar
    def on_ended(self):
        if self.writer is not None:
            self.writer.release()
            self.writer = None

    def __del__(self):
        if self.writer is not None:
            self.writer.release()
            self.writer = None


# ==========================================================
# 🎨 GLOBAL UI STYLES
# ==========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;600;700&display=swap');
.stApp { background: linear-gradient(-45deg, #050b14, #0a192f, #020c1b, #112240); background-size: 400% 400%; animation: gradientBG 15s ease infinite; color: #e6f1ff; font-family: 'Rajdhani', sans-serif;}
@keyframes gradientBG { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

[data-testid="stSidebarNav"] { display: none !important; }
.glass-card { background: rgba(2, 12, 27, 0.7); padding: 40px; border-radius: 20px; border: 1px solid rgba(100, 255, 218, 0.2); text-align: center; margin-bottom: 20px; box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);}
.text-cyan { color: #64ffda; font-family: 'Orbitron', sans-serif; }
.text-purple { color: #b392f0; font-family: 'Orbitron', sans-serif; }

.center-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; padding-top: 8vh; min-height: 80vh; }
.question-container { min-height: 260px; display: flex; flex-direction: column; justify-content: center; }
.action-container { height: 180px; display: flex; flex-direction: column; justify-content: flex-start; align-items: center; width: 100%; }

section[data-testid="stSidebar"] { background: linear-gradient(180deg, #020c1b 0%, #050b14 100%) !important; border-right: 1px solid rgba(100, 255, 218, 0.1) !important; }
.stRadio > div[role="radiogroup"] { gap: 15px; margin-top: 20px; }
.stRadio > div[role="radiogroup"] > label { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(100, 255, 218, 0.1); padding: 15px 20px !important; border-radius: 12px !important; cursor: pointer; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important; }
.stRadio > div[role="radiogroup"] > label:hover { background: linear-gradient(90deg, rgba(100, 255, 218, 0.1) 0%, rgba(179, 146, 240, 0.1) 100%); border-color: #b392f0; transform: translateX(10px); box-shadow: -5px 0px 15px rgba(179, 146, 240, 0.2); }
.stRadio p { font-size: 1.2rem !important; font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important; color: #cbd5e1 !important; margin: 0 !important; letter-spacing: 1px;}
div.stButton > button:first-child { background: transparent !important; color: #64ffda !important; border: 2px solid #64ffda !important; border-radius: 8px !important; font-family: 'Orbitron', sans-serif !important; font-weight: 700 !important; padding: 1rem !important; letter-spacing: 1px;}
div.stButton > button:first-child:hover { background: rgba(100, 255, 218, 0.1) !important; transform: scale(1.02); transition: all 0.3s ease; box-shadow: 0 0 15px rgba(100, 255, 218, 0.3);}

.neon-timer { font-size: 5rem; font-family: 'Orbitron', sans-serif; color: #64ffda; text-shadow: 0 0 20px rgba(100, 255, 218, 0.6), 0 0 40px rgba(100, 255, 218, 0.4); line-height: 1; }
.timer-warning { color: #ef4444 !important; text-shadow: 0 0 20px rgba(239, 68, 68, 0.6) !important; }

.recording-indicator { background: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444; padding: 15px 40px; border-radius: 50px; color: #ef4444; font-family: 'Orbitron', sans-serif; font-weight: bold; letter-spacing: 3px; font-size: 1.2rem; animation: pulseRed 1.5s infinite; text-align: center; margin-bottom: 20px; }
@keyframes pulseRed { 0% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.2); border-color: rgba(239, 68, 68, 0.5); } 50% { box-shadow: 0 0 30px rgba(239, 68, 68, 0.7); border-color: rgba(239, 68, 68, 1); } 100% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.2); border-color: rgba(239, 68, 68, 0.5); } }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown(
    f"<div style='text-align: center; margin-bottom: 30px;'><img src='{LOGO_URL}' width='200' style='border-radius: 50%; border: 2px solid #b392f0; margin-bottom: 20px; box-shadow: 0 0 20px rgba(179, 146, 240, 0.4);'><h2 style='color: #64ffda; margin: 0; font-family: \"Orbitron\", sans-serif; letter-spacing: 2px;'>TALENTLENS</h2><p style='color: #8892b0; margin: 5px 0 0 0; font-size: 0.9rem; letter-spacing: 3px;'>CANDIDATE PORTAL</p></div>",
    unsafe_allow_html=True)
menu = st.sidebar.radio("NAVIGATION", ["🏠 Home", "🎥 Interview Chamber"], label_visibility="hidden")

# ==========================================================
# 🚨 TROJAN HORSE: ANTI-CHEAT SİSTEMİ
# ==========================================================
is_interview_active = "true" if (
        menu == "🎥 Interview Chamber" and st.session_state.get("stage") in ["prep", "record"]) else "false"

if st.button("🚨TRIGGER_DISQUALIFY🚨"):
    if st.session_state.get("stage") in ["prep", "record"]:
        st.session_state.disqualified = True
        st.rerun()

components.html(f"""
<script>
try {{ window.parent.talentLensActive = "{is_interview_active}" === "true"; }} catch(e) {{}}

let strikeBtn = null;

function armTrap() {{
    try {{
        const btns = window.parent.document.querySelectorAll("button");
        btns.forEach(b => {{
            if (b.innerText.includes("🚨TRIGGER_DISQUALIFY🚨")) {{
                strikeBtn = b;
                b.closest('div[data-testid="stButton"]').style.display = "none";
            }}
        }});
    }} catch(e) {{}}
}}

armTrap();
setTimeout(armTrap, 500);

function strike() {{
    let isActive = false;
    try {{ isActive = window.parent.talentLensActive; }} catch(e) {{ isActive = "{is_interview_active}" === "true"; }}
    if (isActive && strikeBtn) {{
        strikeBtn.click();
    }}
}}

document.addEventListener("visibilitychange", () => {{ if (document.hidden) strike(); }});
try {{ window.parent.document.addEventListener("visibilitychange", () => {{ if (window.parent.document.hidden) strike(); }}); }} catch(e) {{}}
</script>
""", height=0, width=0)

# 🚨 KOPYA ÇEKİLDİYSE DB'YE KAYDET VE KİLİTLE
if st.query_params.get("disqualified") == "true" or st.session_state.get("disqualified") == True:
    if candidate_info and candidate_info.get('token'):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("UPDATE candidates SET status='Disqualified' WHERE token=?", (candidate_info['token'],))
            conn.commit()
            conn.close()
        except:
            pass

    st.markdown(
        "<div class='center-wrapper'><div class='glass-card' style='border-color:#ef4444; width:80%; max-width:800px;'><h1 style='color:#ef4444; font-size:4rem;'>🚨 DISQUALIFIED 🚨</h1><p style='font-size:1.2rem;'>Your session has been terminated due to tab switching. System locked.</p></div></div>",
        unsafe_allow_html=True);
    st.stop()

if st.session_state.get("stage") in ["camera_test", "prep", "record", "evaluate"] and menu != "🎥 Interview Chamber":
    st.session_state.disqualified = True;
    st.rerun()

# --- 1. HOME ---
if menu == "🏠 Home":
    st.markdown(
        f"<div class='center-wrapper'><img src='{LOGO_URL}' width='250' style='border-radius:50%; box-shadow: 0 0 40px rgba(100, 255, 218, 0.4); margin-bottom:30px;'><div class='glass-card' style='width: 80%; max-width: 800px;'><h1 style='font-size: 3.5rem; margin:0;'><span class='text-cyan'>TALENT</span>LENS AI</h1><h3 style='margin-top: 10px;'>Welcome, {candidate_info['name']}</h3><p style='color:#cbd5e1; font-size:1.2rem; margin-top: 15px;'>Position Applied For: <b style='color:#b392f0;'>{candidate_info['role']}</b></p><p style='color:#cbd5e1; font-size:1.2rem;'>Interview Language: <b style='color:#b392f0;'>{candidate_info['language']}</b></p><hr style='border-color: rgba(100,255,218,0.2); margin: 20px 0;'><p style='color:#8892b0; font-size: 1.1rem;'>Please navigate to the <b>'Interview Chamber'</b> tab from the left menu to begin your session.</p></div></div>",
        unsafe_allow_html=True)

# --- 2. INTERVIEW CHAMBER ---
elif menu == "🎥 Interview Chamber":
    if "stage" not in st.session_state: st.session_state.stage = "intro"
    if "q_idx" not in st.session_state: st.session_state.q_idx = 0
    if "audio_paths" not in st.session_state: st.session_state.audio_paths = {}

    if "questions" not in st.session_state:
        with st.spinner(f"AI is generating dynamic questions in {candidate_info['language']}..."):
            st.session_state.questions = get_dynamic_questions_from_ai(candidate_info['role'],
                                                                       candidate_info['language'])

    st.progress(int((st.session_state.q_idx / len(st.session_state.questions)) * 100))

    if st.session_state.stage == "intro":
        st.markdown(f"""
        <div class='center-wrapper'>
            <div class='glass-card' style='width: 80%; max-width: 850px; text-align: left;'>
                <h2 class='text-cyan' style='text-align: center; margin-bottom: 20px;'>📋 INTERVIEW PROTOCOLS & RULES</h2>
                <hr style='border-color: rgba(100,255,218,0.2); margin-bottom: 20px;'>
                <ul style='font-size: 1.15rem; color: #cbd5e1; line-height: 1.8;'>
                    <li>🌐 <b>Language:</b> This interview will be conducted in <b>{candidate_info['language']}</b>.</li>
                    <li>⏱️ <b>Time Limit:</b> You have a maximum of <b>30 minutes</b> in total for 5 questions. Please pace your answers and manage your time effectively.</li>
                    <li>⏳ <b>Preparation Time:</b> You will have up to <b>45 seconds</b> to think before each question.</li>
                    <li>⏩ <b>Skip Timer:</b> If you are ready before the 45 seconds are up, you can click the <b>'START RECORDING NOW'</b> button to skip the wait and begin answering immediately.</li>
                    <li>🎙️ <b>Recording:</b> You MUST click the microphone icon to record your answer.</li>
                    <li>📸 <b>Camera Tracking:</b> Your camera must remain active. Once the interview starts, the video feed will minimize to the bottom right corner so you can focus on the questions.</li>
                    <li>🚨 <b>Anti-Cheat System:</b> Do <b>NOT</b> switch tabs, minimize your browser, or click outside the window. Any loss of focus will result in <b>instant disqualification</b>.</li>
                </ul>
                <p style='text-align: center; color: #b392f0; margin-top: 30px; font-size: 1.1rem; font-weight: bold;'>By clicking the button below, you agree to these terms and proceed to the camera test.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            if st.button("I AGREE - PROCEED TO CAMERA TEST", use_container_width=True):
                st.session_state.stage = "camera_test"
                st.rerun()

    elif st.session_state.stage in ["camera_test", "prep", "record"]:
        CAMERA_STATUS["stage"] = st.session_state.stage

        if st.session_state.stage == "camera_test":
            st.markdown(
                """<style>div.element-container:has(iframe[title*="webrtc"]) { display: flex; justify-content: center; margin: 0 auto; width: 600px !important; border: 3px solid #64ffda !important; border-radius: 15px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important; overflow: hidden !important; } iframe[title*="webrtc"] { width: 100% !important; border: none !important; }</style>""",
                unsafe_allow_html=True)
        elif st.session_state.stage == "prep":
            st.markdown(
                """<style>div.element-container:has(iframe[title*="webrtc"]) { position: fixed !important; bottom: 30px !important; right: 30px !important; width: 280px !important; height: 160px !important; border: 4px solid #b392f0 !important; border-radius: 15px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.8) !important; z-index: 999999 !important; overflow: hidden !important; pointer-events: none !important; background-color: #000 !important; } iframe[title*="webrtc"] { width: 280px !important; height: 250px !important; border: none !important; margin-top: -10px !important; }</style>""",
                unsafe_allow_html=True)
        elif st.session_state.stage == "record":
            st.markdown(
                """<style>div.element-container:has(iframe[title*="webrtc"]) { position: fixed !important; bottom: 30px !important; right: 30px !important; width: 280px !important; height: 160px !important; border: 4px solid #ef4444 !important; border-radius: 15px !important; box-shadow: 0 0 20px rgba(239,68,68,0.8) !important; z-index: 999999 !important; overflow: hidden !important; pointer-events: none !important; background-color: #000 !important; } iframe[title*="webrtc"] { width: 280px !important; height: 250px !important; border: none !important; margin-top: -10px !important; }</style>""",
                unsafe_allow_html=True)

        ctx = webrtc_streamer(key="cam", mode=WebRtcMode.SENDRECV, video_transformer_factory=ContinuousFaceTracker,
                              media_stream_constraints={"video": {"width": {"ideal": 1280}, "height": {"ideal": 720}},
                                                        "audio": False})

        if st.session_state.stage == "camera_test":
            st.markdown(
                "<div style='text-align:center; margin-top: 20px;'><h3 class='text-cyan'>🎥 CAMERA INITIALIZATION</h3><p style='color: #cbd5e1; font-size: 1.1rem;'>Please click 'START' on the video player above. Once you see yourself clearly, click the button below.</p></div>",
                unsafe_allow_html=True)
            st.write("<br>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                if ctx and ctx.state.playing:
                    if st.button("START INTERVIEW NOW", use_container_width=True):
                        st.session_state.stage = "prep";
                        st.session_state.timer = time.time();
                        st.rerun()
                else:
                    st.button("START INTERVIEW NOW", use_container_width=True, disabled=True)
                    st.markdown(
                        "<p style='text-align:center; color:#ef4444; font-size:1rem; font-weight:bold; margin-top:10px;'>⚠️ Please click 'START' on the camera first!</p>",
                        unsafe_allow_html=True)

        elif st.session_state.stage == "prep":
            current_question = st.session_state.questions[st.session_state.q_idx]

            components.html(
                f"""<script>if (window.parent.lastSpokenIndex !== {st.session_state.q_idx}) {{ const langMap = {{"English": "en-US", "Türkçe": "tr-TR", "Deutsch": "de-DE", "Español": "es-ES", "Français": "fr-FR"}}; const selectedLang = langMap["{candidate_info['language']}"] || "en-US"; const msg = new SpeechSynthesisUtterance("{current_question}"); msg.lang = selectedLang; window.parent.speechSynthesis.speak(msg); window.parent.lastSpokenIndex = {st.session_state.q_idx}; }}</script>""",
                height=0)

            rem_time = int(45 - (time.time() - st.session_state.timer))
            timer_class = "neon-timer timer-warning" if rem_time <= 10 else "neon-timer"

            st.markdown(f"""
            <div class='center-wrapper'>
                <div class='glass-card question-container' style='width: 90%; max-width: 1000px;'>
                    <h3 class='text-purple' style='margin-bottom: 15px; letter-spacing: 2px;'>QUESTION {st.session_state.q_idx + 1}</h3>
                    <h1 style='color: #e2e8f0; font-size: 2.2rem; line-height: 1.5; margin:0;'>{current_question}</h1>
                </div>
                <div class='action-container'>
                    <p style='color:#8892b0; font-size: 1.1rem; margin:0 0 5px 0; letter-spacing: 2px; font-weight:bold;'>PREPARATION TIME</p>
                    <div class='{timer_class}'>00:{rem_time:02d}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                if st.button("START RECORDING NOW", use_container_width=True):
                    st.session_state.stage = "record"
                    st.rerun()

            if rem_time <= 0: st.session_state.stage = "record"; st.rerun()
            time.sleep(1);
            st.rerun()

        elif st.session_state.stage == "record":
            current_question = st.session_state.questions[st.session_state.q_idx]

            st.markdown(f"""
            <div style='display: flex; flex-direction: column; align-items: center; margin-top: 30px; margin-bottom: 20px;'>
                <div class='glass-card' style='width: 90%; max-width: 1000px; padding: 30px; min-height: auto;'>
                    <h3 class='text-purple' style='margin-bottom: 10px; letter-spacing: 2px;'>QUESTION {st.session_state.q_idx + 1}</h3>
                    <h2 style='color: #e2e8f0; font-size: 1.8rem; line-height: 1.5; margin:0;'>{current_question}</h2>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                st.markdown(
                    "<div class='recording-indicator' style='padding: 10px 20px; font-size: 1.1rem; margin-bottom: 10px;'>🔴 RECORDING VIDEO...</div>",
                    unsafe_allow_html=True)
                st.markdown(
                    "<h4 style='color:#cbd5e1; text-align:center; margin-bottom:15px;'>🎙️ Click the Mic to Record Your Answer</h4>",
                    unsafe_allow_html=True)

                mic_spacer1, mic_col, mic_spacer2 = st.columns([4, 1, 4])
                with mic_col:
                    audio_bytes = audio_recorder(text="", recording_color="#ef4444", neutral_color="#64ffda",
                                                 icon_size="3x", pause_threshold=3600.0)

                st.write("<br>", unsafe_allow_html=True)

                if audio_bytes:
                    audio_filename = os.path.join(BASE_DIR, "recorded_videos",
                                                  f"ans_{candidate_info['token']}_q{st.session_state.q_idx}.wav")
                    if "audio_paths" not in st.session_state: st.session_state.audio_paths = {}

                    with open(audio_filename, "wb") as f:
                        f.write(audio_bytes)
                    st.session_state.audio_paths[st.session_state.q_idx] = audio_filename

                    st.success("✅ Voice saved!")
                    if st.button("Complete My Answer & Next", use_container_width=True):
                        st.session_state.q_idx += 1
                        if st.session_state.q_idx < len(st.session_state.questions):
                            st.session_state.stage = "prep"
                            st.session_state.timer = time.time()
                        else:
                            st.session_state.stage = "evaluate"
                        st.rerun()
                else:
                    st.info("👆 Please record your audio answer to proceed.")

    # =========================================================
    # 🧠 GERÇEK AI DEĞERLENDİRME MOTORU & DATABASE GÜVENLİK AĞI
    # =========================================================
    elif st.session_state.stage == "evaluate":
        st.markdown(f"""
        <div class='center-wrapper'>
            <div class='glass-card' style='width: 80%; max-width: 800px; border-top: 4px solid #b392f0; padding: 50px;'>
                <h1 class='text-cyan' style='font-size: 2.5rem; margin-bottom: 15px;'>⚙️ AI ANALYSIS IN PROGRESS</h1>
                <h3 style='color: #e2e8f0; margin-bottom: 25px;'>Please do not close or refresh this page.</h3>
                <div style='background: rgba(179, 146, 240, 0.1); border: 1px dashed rgba(179, 146, 240, 0.4); padding: 20px; border-radius: 12px; text-align: left;'>
                    <ul style='color: #cbd5e1; font-size: 1.1rem; line-height: 1.8; margin: 0;'>
                        <li>📥 Saving high-definition video and audio recordings...</li>
                        <li>🤖 Transcribing responses to text via AI...</li>
                        <li>📊 Evaluating technical skills and emotional stability...</li>
                        <li>📑 Generating Human Resources Executive Summary...</li>
                    </ul>
                </div>
                <p style='color: #ef4444; margin-top: 30px; font-weight: bold; font-size: 1.1rem; animation: pulseRed 2s infinite;'>
                    ⚠️ This process may take 1 to 3 minutes depending on the server load.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        status_msg = st.empty()
        status_msg.info("Securely processing your interview data... Please wait, do not close the page.")

        time.sleep(3)

        vid_path = CANDIDATE_VIDEO_PATH
        audio_list = [st.session_state.audio_paths[i] for i in range(len(st.session_state.questions)) if
                      i in st.session_state.audio_paths]

        try:
            scores, ai_summary = evaluate_interview_with_ai(
                role=candidate_info['role'],
                language=candidate_info['language'],
                questions=st.session_state.questions,
                video_path=vid_path,
                audio_paths=audio_list
            )

            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for item in scores:
                c.execute("INSERT INTO results VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
                    timestamp, candidate_info["token"], candidate_info["name"], candidate_info["role"], item["q"],
                    item["score"], item["emotion"], vid_path))

            c.execute(f"UPDATE candidates SET status='Completed', ai_summary=? WHERE token=?",
                      (ai_summary, candidate_info['token']))
            conn.commit()
            conn.close()

            st.session_state.scores = scores

        except Exception as e:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            fallback_summary = f"⚠️ AI Analysis could not be completed due to a timeout. Video is safely saved. Manual review required."

            c.execute(f"UPDATE candidates SET status='Completed', ai_summary=? WHERE token=?",
                      (fallback_summary, candidate_info['token']))
            conn.commit()
            conn.close()
            st.session_state.scores = []

        st.session_state.stage = "completed"
        st.rerun()

    # STAGE 6: COMPLETED
    elif st.session_state.stage == "completed":
        st.balloons()
        st.markdown(
            f"""
            <div class='center-wrapper'>
                <div class='glass-card' style='width: 80%; max-width: 850px; border-top: 4px solid #10b981; background: linear-gradient(180deg, rgba(16, 185, 129, 0.05) 0%, rgba(2, 12, 27, 0.8) 100%); text-align: left; padding: 50px;'>
                    <h1 style='color: #10b981; font-size: 3rem; margin-bottom: 20px; text-align: center;'>✅ INTERVIEW COMPLETED!</h1>
                    <hr style='border-color: rgba(16,185,129,0.2); margin-bottom: 30px;'>

                    <p style='font-size:1.25rem; color: #e2e8f0; line-height: 1.8;'>
                        Dear <b>{candidate_info['name']}</b>,<br><br>
                        Thank you for your time and effort. Your video interview has been successfully recorded and securely transmitted to our HR database.
                        <br><br>
                        Our recruitment team and AI assessment system will now review your responses in detail. <b>We will notify you of the results via email as soon as the evaluation process is complete.</b>
                        <br><br>
                        You may now safely close this window. We wish you the best of luck in your career journey!
                        <br><br>
                        <i>— Human Resources Department</i>
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True)