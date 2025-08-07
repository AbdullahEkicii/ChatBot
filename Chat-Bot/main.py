# -*- coding: utf-8 -*-
import json
import gzip
import os
import random
import sqlite3
import tkinter as tk
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
from TurkishStemmer import TurkishStemmer
from chat_screen import ModernChatScreen
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# NLTK indir
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('stopwords', download_dir='nltk_data')
    nltk.download('punkt', download_dir='nltk_data')
except:
    pass

model = SentenceTransformer("distiluse-base-multilingual-cased-v1")

DB_PATH = "veritabani.db"
INDEX_PATH = "faiss.index"

# ------------------------------
# Soru ön işleme
# ------------------------------
def soru_on_isleme(soru):
    stop_words = set(stopwords.words("turkish"))
    stemmer = TurkishStemmer()
    soru = soru.lower()
    kelimeler = word_tokenize(soru)
    kelimeler = [k for k in kelimeler if k not in stop_words and k.isalnum()]
    kelimeler = [stemmer.stem(k) for k in kelimeler]
    return " ".join(kelimeler)

# ------------------------------
# Veritabanı işlemleri
# ------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS veriseti (
            id INTEGER PRIMARY KEY,
            soru TEXT NOT NULL,
            cevap TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def json_to_sqlite(json_path):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

        for item in data["sorular"]:  # 🔁 DİKKAT: data değil, data["sorular"]
            soru = item.get("soru")
            cevap = json.dumps(item.get("cevap"))  # Liste olduğu için JSON string'e çeviriyoruz
            cur.execute("INSERT INTO veriseti (soru, cevap) VALUES (?, ?)", (soru, cevap))

    conn.commit()
    conn.close()


# Vektör ve FAISS index
# ------------------------------
def build_faiss_index():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, soru FROM veriseti")
    veriler = cur.fetchall()
    conn.close()

    vektörler = []
    idler = []

    for row_id, soru in veriler:
        temiz = soru_on_isleme(soru)
        vec = model.encode([temiz], convert_to_tensor=False)[0]
        vektörler.append(vec)
        idler.append(row_id)
    
    if not vektörler:
        raise ValueError("Hiç geçerli vektör bulunamadı. Veritabanında yeterli veri olmayabilir.")
    
    
    mat = np.array(vektörler).astype('float32')
    index = faiss.IndexFlatL2(mat.shape[1])
    index.add(mat)

    faiss.write_index(index, INDEX_PATH)
    with open("id_map.pkl", "wb") as f:
        import pickle
        pickle.dump(idler, f)

# ------------------------------
# Cevap bulucu
# ------------------------------
def en_yakin_cevap(soru):
    temiz = soru_on_isleme(soru)
    user_vec = model.encode([temiz], convert_to_tensor=False).astype('float32')

    index = faiss.read_index(INDEX_PATH)
    with open("id_map.pkl", "rb") as f:
        import pickle
        id_map = pickle.load(f)

    D, I = index.search(user_vec, k=1)
    en_yakin_id = id_map[I[0][0]]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT cevap FROM veriseti WHERE id = ?", (en_yakin_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        cevaplar = json.loads(row[0])
        return random.choice(cevaplar) if isinstance(cevaplar, list) else cevaplar
    return "Bu soruya dair bilgim yok."

# ------------------------------
# Yeni soru ekleme
# ------------------------------
def yeni_cevap_ekle(soru, cevap):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, cevap FROM veriseti WHERE soru = ?", (soru,))
    row = cur.fetchone()

    if row:
        mevcut_id, eski_cevap = row
        cevaplar = json.loads(eski_cevap)
        if cevap not in cevaplar:
            cevaplar.append(cevap)
            cur.execute("UPDATE veriseti SET cevap = ? WHERE id = ?", (json.dumps(cevaplar), mevcut_id))
    else:
        cur.execute("INSERT INTO veriseti (soru, cevap) VALUES (?, ?)", (soru, json.dumps([cevap])))

    conn.commit()
    conn.close()
    build_faiss_index()

# ------------------------------
# GUI entegrasyonu
# ------------------------------
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Veritabanı kuruluyor...")
        init_db()
        json_to_sqlite("veritabani.json")
        build_faiss_index()
    elif not os.path.exists(INDEX_PATH):
        build_faiss_index()

    def get_response_for_gui(text):
        return en_yakin_cevap(text)

    def add_answer_for_gui(soru, cevap):
        yeni_cevap_ekle(soru, cevap)
        

    try:
        root = tk.Tk()
        app = ModernChatScreen(
            root,
            get_response_func=get_response_for_gui,
            add_new_answer_func=add_answer_for_gui
        )
        root.mainloop()
    except Exception as e:
        print("GUI hatası:", e)
