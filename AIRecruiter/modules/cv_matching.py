from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")


def calculate_similarity(cv_text, job_description):
    embeddings = model.encode([cv_text, job_description])

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return round(float(similarity) * 100, 2)
def find_missing_skills(cv_text, job_description):
    # Basit skill extraction (kelime bazlı)
    jd_words = set(job_description.lower().split())
    cv_words = set(cv_text.lower().split())

    missing = []

    for word in jd_words:
        if word.isalpha() and len(word) > 3:
            if word not in cv_words:
                missing.append(word)

    return missing[:10]  # çok uzun olmaması için ilk 10