import streamlit as st
import pandas as pd
import requests
import uuid
import json
from collections import Counter
import matplotlib.pyplot as plt

# Set up Azure keys and endpoints (replace with your actual values)
AZURE_LANGUAGE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"
AZURE_LANGUAGE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"
AZURE_LANGUAGE_REGION = "southeastasia"

# Load questions from CSV
questions_df = pd.read_csv("questions.csv")

# Ensure consistent column names
questions_df.columns = [col.strip() for col in questions_df.columns]

# Soft skill red flags list (partial)
red_flags = [
    "menolak", "menghindari", "tidak peduli", "menyerah", "mengabaikan", "membiarkan",
    "tidak penting", "salah orang lain", "terlalu sulit", "bukan tugas saya", "tidak yakin",
    "tidak bisa", "tidak mau", "tidak cocok", "tidak mungkin", "terserah", "malas", "tidak niat",
    "tidak tahu", "tidak paham"
]

# Analyze sentiment and flag risks
def analyze_sentiment(text):
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_LANGUAGE_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_LANGUAGE_REGION,
        "Content-Type": "application/json"
    }

    body = {
        "documents": [{
            "id": "1",
            "language": "id",
            "text": text
        }]
    }

    response = requests.post(
        AZURE_LANGUAGE_ENDPOINT + "/text/analytics/v3.1/sentiment",
        headers=headers,
        json=body
    )

    result = response.json()
    sentiment = result["documents"][0]["sentiment"]
    confidence = result["documents"][0]["confidenceScores"][sentiment]

    # Red flag detection
    text_lower = text.lower()
    red_flag_hit = any(flag in text_lower for flag in red_flags)

    return sentiment, confidence, red_flag_hit

# Start of Streamlit app
st.set_page_config(page_title="KerjaTayang", page_icon="🧑‍💻", layout="centered")

# Header with Dicoding meta tag note (for deployment)
st.markdown("""
    <head>
        <meta name="dicoding:email" content="andy.lie95@gmail.com">
    </head>
""", unsafe_allow_html=True)

st.title("🎯 KerjaTayang: Simulasi Kerja Interaktif")
st.markdown("Aplikasi ini membantu kamu melatih soft skill berdasarkan tantangan kerja nyata.")

# User info
name = st.text_input("Nama kamu:")
age = st.number_input("Usia kamu:", min_value=10, max_value=60, step=1)

# Dropdown to choose job role
available_roles = questions_df['Role'].dropna().unique()
role = st.selectbox("Pilih peran kerja:", available_roles)

if role:
    st.markdown(f"**Halo {name}, kamu memilih peran sebagai `{role}`.**")

    # Show required soft skills
    skills_for_role = questions_df[questions_df['Role'] == role]['Skills'].dropna().unique()
    if len(skills_for_role):
        st.markdown("💡 **Soft skill yang akan diuji:**")
        st.markdown(", ".join(skills_for_role))

    # Filter questions for role
    role_questions = questions_df[questions_df['Role'] == role]

    if len(role_questions):
        sentiments = []
        flags = 0

        st.markdown("---")
        st.subheader("🧪 Simulasi Kasus")

        for i, (_, row) in enumerate(role_questions.iterrows(), 1):
            st.markdown(f"👩‍💼 **Skenario {i}:** {row['Background']}")
            st.markdown(f"**Pertanyaan:** {row['Question']}")
            user_response = st.text_area(f"✍️ Jawaban kamu untuk Skenario {i}:", key=f"q{i}")

            if user_response:
                sentiment, confidence, red_flag = analyze_sentiment(user_response)
                sentiments.append(sentiment)
                if red_flag:
                    flags += 1

                emoji = "✅" if sentiment == "positive" and not red_flag else "⚠️"
                st.markdown(f"{emoji} **Analisis Sentimen:** `{sentiment}` (Keyakinan: {confidence:.2f})")

        if len(sentiments) == 5:
            # Summary
            st.markdown("---")
            st.subheader("📊 Hasil Evaluasi")

            sentiment_counts = Counter(sentiments)
            fit_score = sentiment_counts.get("positive", 0)
            fit_percentage = (fit_score / 5) * 100

            st.markdown(f"👍 **Kamu menjawab {fit_score} dari 5 dengan sentimen positif.**")
            st.markdown(f"🧠 Red Flag Terdeteksi: {flags}")

            # Radar chart
            st.markdown("### 🕸️ Pemetaan Soft Skill")

            labels = ['Positif', 'Netral', 'Negatif']
            scores = [sentiment_counts.get(label.lower(), 0) for label in labels]

            fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
            angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
            scores += scores[:1]
            angles += angles[:1]

            ax.plot(angles, scores, linewidth=2, linestyle='solid')
            ax.fill(angles, scores, 'skyblue', alpha=0.4)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels)
            ax.set_yticklabels([])
            st.pyplot(fig)

            # Final feedback
            st.markdown("---")
            if fit_score >= 3 and flags <= 1:
                st.success("🎉 Kamu dinilai **cocok** untuk peran ini! Pertahankan soft skill kamu.")
            else:
                st.warning("📈 Kamu perlu **berlatih lebih banyak** untuk meningkatkan kesiapan kerja kamu.")

        st.markdown("---")
        st.caption("⏱️ Setiap jawaban akan dinilai berdasarkan sentimen dan red flag tertentu. Maksimal 15 menit per sesi.")
