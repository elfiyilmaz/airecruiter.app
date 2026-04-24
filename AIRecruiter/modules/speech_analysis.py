import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("sk-proj-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"))


def analyze_speech(audio_paths):
    """
    Adayın kaydettiği tüm ses dosyalarını Whisper API ile metne döker.
    """
    if not audio_paths or len(audio_paths) == 0:
        return "No audio recorded."

    print("🎙️ Whisper AI ses analizi başlatılıyor...")
    full_transcript = ""

    for idx, audio_path in enumerate(audio_paths):
        if os.path.exists(audio_path):
            try:
                with open(audio_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                    full_transcript += f"[Question {idx + 1} Answer]: {transcript.text}\n"
            except Exception as e:
                print(f"Whisper Error on file {audio_path}:", e)

    if full_transcript == "":
        return "Could not process audio."

    print("✅ Ses başarıyla metne döküldü:\n", full_transcript)
    return full_transcript


def calculate_speech_confidence(transcript):
    """
    Duraksamaları (ııı, hmmm) sayarak akıcılık puanı hesaplar.
    """
    filler_words = ["uh", "umm", "like", "you know", "basically", "ııı", "eee", "şey"]
    transcript_lower = transcript.lower()
    filler_count = sum(transcript_lower.count(word) for word in filler_words)
    confidence_score = max(50, 100 - (filler_count * 5))
    return confidence_score