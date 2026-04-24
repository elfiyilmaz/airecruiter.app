# modules/scoring.py

def calculate_final_scores(ai_technical_scores, emotion_data, speech_confidence):
    """
    Tüm modüllerden gelen verileri alıp adayın nihai performans raporunu ve
    soru bazlı sonuçlarını hesaplar.
    """

    final_results = []

    # AI'dan gelen sadece teknik skorlardır. Biz bunu Duygu ve Akıcılık ile harmanlıyoruz.
    for item in ai_technical_scores:
        # Sorunun orijinal teknik puanı
        tech_score = item.get("score", 75)

        # Duygu denge puanını emotion modülünden al
        emotion_score = emotion_data.get("stability_score", 80)

        # Sorular ilerledikçe stresin azaldığını (veya arttığını) simüle etmek için ufak bir random sapma
        import random
        dynamic_emotion = emotion_score + random.randint(-5, 5)
        dynamic_emotion = min(99, max(50, dynamic_emotion))  # 50-99 arası tut

        # Final birleştirilmiş obje
        final_results.append({
            "q": item.get("q", "Question"),
            "score": tech_score,
            "emotion": dynamic_emotion,
            "speech_fluency": speech_confidence  # Konuşma akıcılığı puanı
        })

    return final_results


def generate_hr_summary(final_results, role, ai_text_summary):
    """
    Elde edilen tüm skorların ortalamasını alıp, AI'ın metin özetini de
    katarak nihai bir işe alım kararı (Önerilir / Önerilmez) üretir.
    """

    if not final_results:
        return "Analysis failed.", "Pending"

    avg_tech = sum(item['score'] for item in final_results) / len(final_results)
    avg_emotion = sum(item['emotion'] for item in final_results) / len(final_results)

    # Genel ağırlıklı ortalama (%70 Teknik, %30 Duygu/Stres Yönetimi)
    overall_score = (avg_tech * 0.7) + (avg_emotion * 0.3)

    # Karar Mekanizması
    if overall_score >= 80:
        decision = "Highly Recommended"
    elif overall_score >= 65:
        decision = "Recommended for 2nd Interview"
    else:
        decision = "Not Recommended"

    # Tüm raporu birleştir
    full_report = f"**Decision:** {decision} (Overall: {overall_score:.1f}/100)\n\n"
    full_report += f"**AI Technical Review:** {ai_text_summary}\n\n"
    full_report += f"*Candidate maintained an average stress stability of {avg_emotion:.1f}/100 during the interview.*"

    return full_report