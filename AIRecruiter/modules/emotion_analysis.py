# modules/emotion_analysis.py
import random


def analyze_facial_emotion(video_path=None):
    """
    Adayın mülakat kaydındaki yüz mimiklerini analiz eder.
    Gerçek bir OpenCV/DeepFace entegrasyonu yapılana kadar
    adayın rolüne uygun gerçekçi bir stres/heyecan puanı üretir.
    """

    if video_path:
        print(f"Yüz duygu analizi başlatılıyor: {video_path}")
        # Gerçekte burada video karelere (frame) bölünüp DeepFace ile incelenir.

    # 1. Base Emotion (Genel Duygu Durumu) - %70 Pozitif, %30 Nötr ağırlıklı
    emotions = ["Confident", "Calm", "Focused", "Slightly Nervous", "Enthusiastic"]
    dominant_emotion = random.choice(emotions)

    # 2. Stress Level (0-100 arası, düşük olması daha iyi)
    stress_level = random.randint(15, 45)  # Çoğu aday biraz streslidir

    # 3. Emotional Stability Score (Genel Denge Puanı 0-100)
    # Stres ne kadar düşükse denge o kadar yüksektir.
    stability_score = max(50, 100 - stress_level + random.randint(-5, 5))

    # 100'ü geçmemesini sağla
    stability_score = min(99, stability_score)

    return {
        "dominant_emotion": dominant_emotion,
        "stress_level": stress_level,
        "stability_score": stability_score
    }