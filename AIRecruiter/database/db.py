import sqlite3
import os


def init_db():
    # Video klasörünü oluştur
    if not os.path.exists("recorded_videos"):
        os.makedirs("recorded_videos")

    conn = sqlite3.connect('interview.db')
    c = conn.cursor()

    # Tabloları oluştur
    c.execute(
        '''CREATE TABLE IF NOT EXISTS candidates (token TEXT PRIMARY KEY, name TEXT, email TEXT, role TEXT, status TEXT)''')

    # Eksik sütunları güvenlice ekle (Sistemi çökertmez)
    try:
        c.execute("ALTER TABLE candidates ADD COLUMN language TEXT DEFAULT 'English'")
    except:
        pass
    try:
        c.execute("ALTER TABLE candidates ADD COLUMN ai_summary TEXT DEFAULT ''")
    except:
        pass

    c.execute(
        '''CREATE TABLE IF NOT EXISTS results (timestamp TEXT, candidate_token TEXT, candidate_name TEXT, role TEXT, question TEXT, score INT, emotion INT, video_path TEXT)''')

    # Örnek aday ekle
    c.execute("SELECT COUNT(*) FROM candidates")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO candidates (token, name, email, role, status, language) VALUES ('token_elif', 'Elif Yilmaz', 'elif34yzl@gmail.com', 'Computer Engineer', 'Pending', 'English')")

    conn.commit()
    conn.close()