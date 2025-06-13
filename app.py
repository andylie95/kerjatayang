import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from collections import defaultdict

# -----------------------------
# Azure Language Service Config
# -----------------------------
AZURE_LANGUAGE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"
AZURE_LANGUAGE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"  # ⚠️ For testing only

def analyze_with_azure_language(text):
    endpoint = f"{AZURE_LANGUAGE_ENDPOINT}language/:analyze-text?api-version=2022-05-01"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_LANGUAGE_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "kind": "SentimentAnalysis",
        "parameters": {
            "modelVersion": "latest"
        },
        "analysisInput": {
            "documents": [
                {
                    "id": "1",
                    "language": "id",
                    "text": text
                }
            ]
        }
    }

    try:
        response = requests.post(endpoint, headers=headers, json=body)
        result = response.json()
        sentiment = result["results"]["documents"][0]["sentiment"]
        return sentiment
    except:
        return "neutral"

# -----------------------------
# Streamlit Page Setup
# -----------------------------
st.set_page_config(page_title="KerjaTayang", page_icon="🎯", layout="centered")

st.markdown("""
    <h1 style='text-align: center;'>🎯 KerjaTayang</h1>
    <p style='text-align: center;'>Simulasi interaktif untuk cek kesiapan soft skill berdasarkan peran kerja</p>
""", unsafe_allow_html=True)

# -----------------------------
# Load CSV
# -----------------------------
questions_df = pd.read_csv("questions.csv")
questions_df.columns = questions_df.columns.str.strip()

# -----------------------------
# User Info
# -----------------------------
with st.form("user_form"):
    name = st.text_input("Nama kamu:")
    age = st.number_input("Usia kamu:", min_value=12, max_value=60, value=21)
    submitted = st.form_submit_button("Mulai Simulasi")

if not submitted:
    st.stop()

# -----------------------------
# Role Selection
# -----------------------------
roles = sorted(questions_df['Role'].unique())
role = st.selectbox("Pilih peran kerja:", [""] + roles)

if not role:
    st.warning("Silakan pilih peran kerja untuk melanjutkan simulasi.")
    st.stop()

# -----------------------------
# Show Required Skills
# -----------------------------
skills_for_role = questions_df[questions_df['Role'] == role]['Skills'].dropna().unique()
st.info(f"🔍 Untuk menjadi **{role}**, kamu perlu memiliki: **{', '.join(skills_for_role)}**")

# -----------------------------
# Q&A Simulation
# -----------------------------
role_questions = questions_df[questions_df['Role'] == role].reset_index(drop=True)
responses = []
skill_scores = defaultdict(int)

st.subheader("💬 Simulasi Tanya Jawab")

for idx, row in role_questions.iterrows():
    st.markdown(f"👤 **Simulasi {idx+1}**")
    st.markdown(f"🗂️ _{row['Background']}_")
    st.markdown(f"🧑‍💼 Pertanyaan: **{row['Question']}**")
    
    user_input = st.text_area(f"🧑 Kamu:", key=f"answer_{idx}")

    if user_input:
        sentiment = analyze_with_azure_language(user_input)
        score = {"positive": 2, "neutral": 1, "negative": 0}.get(sentiment, 1)

        feedback_text = {
            "positive": "✅ Jawaban kamu menunjukkan soft skill yang kuat!",
            "neutral": "➖ Jawaban kamu cukup netral, bisa dikembangkan lebih lanjut.",
            "negative": "⚠️ Jawaban kamu menunjukkan pendekatan yang kurang tepat."
        }.get(sentiment, "➖ Jawaban kamu cukup netral.")

        responses.append({
            "Skill": row["Skills"],
            "Score": score,
            "Sentiment": sentiment
        })
        skill_scores[row["Skills"]] += score
        st.markdown(f"🧠 {feedback_text}")
        st.markdown("---")
    else:
        st.stop()

# -----------------------------
# Radar Chart Soft Skill
# -----------------------------
st.subheader("📊 Pemetaan Soft Skill")

skills = list(skill_scores.keys())
scores = [v for v in skill_scores.values()]
max_score = len(role_questions) * 2
total_score = sum(scores)

# Remove zero-score skills
skills_filtered = [s for s in skills if skill_scores[s] > 0]
scores_filtered = [skill_scores[s] for s in skills_filtered]

if scores_filtered:
    angles = np.linspace(0, 2 * np.pi, len(skills_filtered), endpoint=False).tolist()
    scores_adjusted = scores_filtered + [scores_filtered[0]]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, scores_adjusted, color='green', linewidth=2)
    ax.fill(angles, scores_adjusted, color='lightgreen', alpha=0.5)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(skills_filtered)
    ax.set_title("Radar Soft Skill")
    st.pyplot(fig)
else:
    st.info("Belum ada skill positif yang terdeteksi dari jawaban kamu.")

# -----------------------------
# Final Evaluation
# -----------------------------
st.subheader("📌 Evaluasi Akhir")

threshold = len(role_questions) * 2 * 0.5

if total_score > threshold:
    st.success(f"🎉 Selamat, kamu telah memiliki skill dasar untuk peran **{role}**!")
else:
    lacking_skills = [r["Skill"] for r in responses if r["Score"] < 2]
    st.warning(f"💡 Semangat! Kamu masih perlu mengembangkan skill berikut:\n👉 {', '.join(set(lacking_skills))}")
