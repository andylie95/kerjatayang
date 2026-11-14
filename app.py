import os
import streamlit as st
import pandas as pd
import requests

# ====== Konfigurasi Azure Language Service ======
# Dibaca dari Streamlit secrets, dengan fallback ke environment variable.
def get_config(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)

AZURE_ENDPOINT = get_config("AZURE_ENDPOINT", "https://kerjatayang.cognitiveservices.azure.com/")
AZURE_KEY = get_config("AZURE_KEY")
AZURE_REGION = get_config("AZURE_REGION", "southeastasia")

# ====== Red Flag Keywords ======
red_flag_keywords = [
    "menolak", "menghindar", "tidak peduli", "acuh", "membiarkan",
    "tidak mau", "emosi", "menyerah", "tidak tertarik", "tidak ikut",
    "salahkan", "malas", "tidak mau berusaha", "tidak penting",
    "tidak mendukung", "tidak mau belajar", "pasrah", "tidak sopan",
    "tidak tanggung jawab", "tidak membantu"
]

# ====== Fungsi Sentimen ======
def analyze_sentiment(text):
    url = AZURE_ENDPOINT + "/text/analytics/v3.1/sentiment"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_REGION,
        "Content-Type": "application/json"
    }
    data = {
        "documents": [{
            "id": "1",
            "language": "id",
            "text": text
        }]
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    try:
        return result['documents'][0]['sentiment']
    except:
        return "neutral"

# ====== Setup Streamlit App ======
st.set_page_config(page_title="KerjaTayang", layout="centered")
st.title("🎯 KerjaTayang: Simulasi Soft Skill Berdasarkan Peran")

if not AZURE_KEY:
    st.error(
        "Azure Language Service key belum dikonfigurasi. "
        "Tambahkan AZURE_KEY di .streamlit/secrets.toml (atau di Secrets pada Streamlit Cloud), "
        "atau set environment variable AZURE_KEY."
    )
    st.stop()

# ====== Form Nama dan Umur ======
with st.form("user_info"):
    name = st.text_input("Nama lengkap")
    age = st.number_input("Umur", min_value=10, max_value=100, step=1)
    submitted = st.form_submit_button("Lanjutkan")

if submitted and name:
    st.session_state["name"] = name
    st.session_state["age"] = age
    st.session_state["ready"] = True

# ====== Load CSV dari file lokal ======
try:
    questions_df = pd.read_csv("questions.csv")
except FileNotFoundError:
    st.error("File questions.csv tidak ditemukan. Pastikan file berada di direktori yang sama.")
    st.stop()

# ====== Role Selection ======
if st.session_state.get("ready"):
    name = st.session_state["name"]
    age = st.session_state["age"]

    role_options = questions_df["Role"].dropna().unique().tolist()
    selected_role = st.selectbox("Pilih peran kerja:", [""] + role_options)

    if selected_role:
        st.session_state["role"] = selected_role
        st.markdown(f"👋 Halo **{name}** (umur {age}), kamu ingin menjadi **{selected_role}**.")
        required_skills = questions_df[questions_df["Role"] == selected_role]["Skills"].unique().tolist()
        st.markdown(f"🧠 Maka kamu perlu menguasai soft skills berikut:")
        for skill in required_skills:
            st.markdown(f"- {skill}")
        if st.button("🚀 Mulai Simulasi"):
            st.session_state["simulate"] = True
            st.session_state["answers"] = {}

# ====== Simulasi ======
if st.session_state.get("simulate"):
    st.header("🧪 Simulasi Soft Skill")
    role = st.session_state["role"]
    simulation_data = questions_df[questions_df["Role"] == role]

    for i, row in simulation_data.iterrows():
        st.subheader(f"Skenario {i+1}")
        st.markdown(row["Scenario"])
        response = st.text_area("Jawabanmu:", key=f"response_{i}")
        st.session_state["answers"][i] = {
            "response": response,
            "skill": row["Skills"]
        }

    if st.button("📊 Evaluasi Hasil"):
        st.session_state["evaluate"] = True

# ====== Evaluasi ======
if st.session_state.get("evaluate"):
    st.header("📋 Hasil Evaluasi")
    results = []
    for i, data in st.session_state["answers"].items():
        response = data["response"]
        skill = data["skill"]
        if not response:
            continue
        sentiment = analyze_sentiment(response)
        red_flags = [k for k in red_flag_keywords if k in response.lower()]
        score = 2 if sentiment == "positive" and not red_flags else 0 if sentiment == "negative" or red_flags else 1
        results.append({
            "skill": skill,
            "sentiment": sentiment,
            "red_flag": bool(red_flags),
            "score": score
        })

    if not results:
        st.warning("Belum ada jawaban yang diisi.")
        st.stop()

    df_result = pd.DataFrame(results)
    total = len(df_result)
    fit = len(df_result[df_result["score"] == 2])
    percentage = (fit / total) * 100

    st.markdown(f"### 🔍 Ringkasan:")
    st.markdown(f"- Jawaban fit (positif tanpa red flag): **{fit}/{total}**")
    st.markdown(f"- Persentase penguasaan soft skill: **{percentage:.1f}%**")

    if percentage >= 50:
        st.success(f"🎉 Selamat, **{name}**! Kamu telah menguasai soft skill dasar untuk peran **{role}**.")
    else:
        st.warning(f"📘 Semangat, **{name}**! Kamu masih bisa mengembangkan kemampuan berikut:")
        underdeveloped = df_result[df_result["score"] < 2]["skill"].unique()
        for s in underdeveloped:
            st.markdown(f"- 🔧 {s}")
