# Set page config FIRST
st.set_page_config(page_title="KerjaTayang", page_icon="🎤", layout="centered")

import streamlit as st
import pandas as pd
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import plotly.graph_objects as go
import time

# ---------------------
# CONFIGURATION SECTION
# ---------------------

# Azure setup
AZURE_LANGUAGE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"
AZURE_LANGUAGE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"

def authenticate_client():
    credential = AzureKeyCredential(AZURE_LANGUAGE_KEY)
    client = TextAnalyticsClient(endpoint=AZURE_LANGUAGE_ENDPOINT, credential=credential)
    return client

client = authenticate_client()

# Red flag & negative keyword lists
red_flags = [
    "tidak tahu", "bukan tanggung jawab", "tidak peduli", "saya menyerah",
    "urusan orang lain", "bukan saya", "tidak mau", "menolak", "membiarkan",
    "bukan masalah saya", "malas", "tidak tertarik", "tunggu saja", "tidak penting",
    "ikut-ikut", "terserah", "tidak bisa", "tidak yakin", "takut salah", "lebih baik diam"
]
negative_keywords = ["tidak", "malas", "enggan", "menolak", "gagal", "takut", "ragu", "salah", "lambat", "terlambat"]

# ---------------------
# HEADER + INSTRUCTIONS
# ---------------------
st.markdown("<h1 style='text-align: center;'>🎤 KerjaTayang</h1>", unsafe_allow_html=True)
st.markdown("📚 *Simulasi Soft Skill Karier untuk Talenta Masa Depan*")
st.markdown("🔹 Simulasi ini terdiri dari 5 pertanyaan berdasarkan peran karier yang kamu pilih. Setelah menjawab, kamu akan mendapatkan umpan balik serta pemetaan soft skill.")
st.markdown("---")

# ---------------------
# USER INFO FORM
# ---------------------
with st.form("user_info"):
    nama = st.text_input("Nama lengkap:")
    usia = st.number_input("Usia kamu:", min_value=13, max_value=99, step=1)
    aspirasi = st.text_input("Apa cita-cita atau karier impianmu?")
    submitted = st.form_submit_button("Mulai Simulasi 🚀")

# ---------------------
# MAIN SIMULATION
# ---------------------
if submitted and nama and aspirasi:
    st.markdown(f"👤 Halo **{nama}**, kamu ingin menjadi **{aspirasi}**. Yuk, kita mulai simulasi wawancara!")

    # Load CSV
    df = pd.read_csv("questions.csv")
    top_roles = df['Role'].unique().tolist()

    selected_role = st.selectbox("🔍 Pilih peran untuk simulasi:", top_roles)

    questions = df[df['Role'] == selected_role].reset_index()
    score = 0
    results = []
    category_scores = {}

    st.markdown("---")
    st.subheader("🎬 Simulasi Dimulai")

    for i in range(len(questions)):
        q = questions.loc[i, 'Question']
        skill = questions.loc[i, 'Intent']

        with st.chat_message("🧑", avatar="🧑"):
            st.markdown(f"**Pertanyaan {i+1}:** {q}")

        user_answer = st.text_input(f"✍️ Jawabanmu:", key=f"answer_{i}")

        if user_answer:
            sentiment = analyze_sentiment(user_answer)
            is_fit = evaluate_answer(user_answer, sentiment)

            if skill not in category_scores:
                category_scores[skill] = 0

            if is_fit:
                feedback = "✅ Jawabanmu menunjukkan sikap positif. Bagus!"
                score += 1
                category_scores[skill] += 1
            else:
                feedback = "⚠️ Jawabanmu perlu dikembangkan. Coba tunjukkan sikap proaktif dan solusi."

            results.append(is_fit)

            with st.chat_message("🤖", avatar="🤖"):
                st.markdown(f"{feedback} _(Sentimen: {sentiment})_")

            st.markdown("---")
            time.sleep(0.5)

    # ---------------------
    # FINAL RESULT & RADAR
    # ---------------------
    if len(results) == len(questions):
        st.subheader("📊 Rekap Simulasi")
        percent_fit = int((score / len(results)) * 100)
        st.markdown(f"**Jawaban positif:** {score} dari {len(results)} pertanyaan")
        st.markdown(f"**Kecocokan Soft Skill:** {percent_fit}%")

        if percent_fit >= 60:
            st.success("💼 Kamu cocok untuk peran ini! Lanjutkan tingkatkan keahlianmu!")
        else:
            st.warning("🔁 Perlu latihan lagi. Yuk coba lagi untuk mengasah kemampuanmu.")

        # Radar Chart
        st.subheader("📈 Pemetaan Soft Skill")
        labels = list(category_scores.keys())
        values = [category_scores[label] for label in labels]

        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=labels,
            fill='toself',
            name='Soft Skill'
        ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=False,
            margin=dict(t=20, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

# ---------------------
# HELPER FUNCTIONS
# ---------------------
def analyze_sentiment(text):
    try:
        result = client.analyze_sentiment([text])[0]
        return result.sentiment
    except Exception as e:
        return "neutral"

def evaluate_answer(response, sentiment):
    text = response.lower()
    for phrase in red_flags:
        if phrase in text:
            return False
    for word in negative_keywords:
        if word in text and sentiment == "negative":
            return False
    return sentiment in ['positive', 'neutral']
