import os
import json
import random
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

# Diğer analiz modüllerini içe aktarıyoruz
from modules.speech_analysis import analyze_speech, calculate_speech_confidence
from modules.emotion_analysis import analyze_facial_emotion
from modules.scoring import calculate_final_scores, generate_hr_summary

load_dotenv()

# API ANAHTARI
client = OpenAI(api_key="sk-proj-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")


def get_dynamic_questions_from_ai(role, language):
    """Adayın rolüne göre her seferinde farklı ve vizyoner sorular üretir."""
    try:
        # Rastgeleliği zorlamak için sistem mesajına ekstra talimat ekledik
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"""You are a top-tier HR Director. 
                Generate 5 deep behavioral interview questions for a {role} in {language}.
                FOCUS ON: Adaptability, crisis management, and professional vision.
                CRITICAL: Every time you are asked, you must provide DIFFERENT questions. 
                Do not ask common questions like 'tell me about yourself'.
                Return ONLY a JSON array of strings."""},
                {"role": "user",
                 "content": f"Generate 5 fresh and unique behavioral questions for {role}. Random Seed: {random.randint(1, 999999)}"}
            ],
            temperature=0.95,  # Yaratıcılığı zirveye çıkardık
            timeout=12
        )
        questions = json.loads(response.choices[0].message.content.strip())
        return questions
    except Exception as e:
        # 🎲 GELİŞMİŞ YEDEK PLAN: API çalışmazsa geniş havuzdan rastgele 5 tane seçer
        fallbacks = {
            "Computer Engineer": {
                "Türkçe": [
                    "Teknik bir kararda ekiple ters düştüğünüzde süreci nasıl yönettiniz?",
                    "Hiç bitmeyeceğini düşündüğünüz bir bug'ı nasıl çözdünüz?",
                    "Kendi başınıza öğrendiğiniz en son karmaşık teknoloji neydi?",
                    "Yazılımda 'iyi kod' sizin için ne ifade ediyor?",
                    "Hatalı bir mimari karar verdiğinizi fark ettiğinizde tepkiniz ne olur?",
                    "Yapay zekanın yazılım dünyasını nasıl değiştireceğini düşünüyorsunuz?",
                    "Baskı altında kod kalitesinden ödün verir misiniz?",
                    "Teknik borç (technical debt) yönetiminde önceliğiniz nedir?",
                    "Yeni bir dilde proje geliştirmeniz gerekse ilk 48 saatinizi nasıl planlarsınız?",
                    "Sizi mesleğinizde en çok heyecanlandıran açık kaynak projesi hangisi?"
                ],
                "English": [
                    "How do you handle a situation where a teammate disagrees with your technical design?",
                    "Describe the most complex bug you've ever fixed.",
                    "What was the last technical skill you mastered on your own?",
                    "What does 'clean code' mean to you in a deadline-driven environment?",
                    "How do you stay motivated when facing a project failure?"
                ]
            }
        }
        role_key = role if role in fallbacks else "Computer Engineer"
        lang_data = fallbacks[role_key].get(language, fallbacks[role_key]["English"])
        return random.sample(lang_data, min(len(lang_data), 5))


def evaluate_interview_with_ai(role, language, questions, video_path=None, audio_paths=[]):
    """Mülakat cevaplarını analiz eder ve puanlar."""

    # 1. 🎙️ SES ANALİZİ (Whisper)
    transcript = analyze_speech(audio_paths)

    # 2. 📸 YÜZ ANALİZİ (Önce yapıyoruz ki duygu verisini ChatGPT'ye de fısıldayalım!)
    emotion_data = analyze_facial_emotion(video_path)
    avg_emotion = np.mean(emotion_data) if emotion_data else 50

    # 🚨 SKOR KONTROLÜ: Sessiz kalan adaya acımıyoruz!
    if not transcript or len(transcript.strip()) < 10:
        ai_text_summary = "Aday sorulara sözlü bir yanıt vermediği için değerlendirme yapılamadı." if language == "Türkçe" else "Candidate provided no verbal response. Zero points assigned."
        raw_scores = [{"q": q, "score": 0} for q in questions]
        speech_fluency = 0
    else:
        speech_fluency = calculate_speech_confidence(transcript)

        # ChatGPT ile hem cevap içeriğini hem de duygu durumunu harmanlıyoruz
        questions_text = "\n".join([f"{i + 1}. {q}" for i, q in enumerate(questions)])

        eval_prompt = f"""
        Analyze this {role} candidate.
        Questions: {questions_text}
        Candidate's Transcript: {transcript}
        Facial Stability Score (0-100): {avg_emotion}

        Task: Provide a professional HR evaluation in {language}. 
        Consider both the technical depth of answers and their emotional composure.
        Return ONLY JSON: {{"scores": [{{"q": "...", "score": 0}}, ...], "summary": "..."}}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": eval_prompt}],
                max_tokens=800,
                temperature=0.3  # Puanlamada daha istikrarlı olması için düşük tuttuk
            )
            result = json.loads(response.choices[0].message.content.strip())
            raw_scores = result["scores"]
            ai_text_summary = result["summary"]
        except Exception as e:
            print(f"AI Scoring Error: {e}")
            # Hata anında bile eğer konuşmadıysa 0, konuştuysa 50 veriyoruz
            base_err_score = 0 if len(transcript.strip()) < 10 else 50
            raw_scores = [{"q": q, "score": base_err_score} for q in questions]
            ai_text_summary = "Analiz motorunda teknik bir aksama yaşandı."

    # 3. 📊 TÜM VERİLERİ HARMANLA
    final_scores = calculate_final_scores(raw_scores, emotion_data, speech_fluency)
    final_report = generate_hr_summary(final_scores, role, ai_text_summary)

    return final_scores, final_report