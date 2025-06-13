import streamlit as st
import pandas as pd
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import plotly.graph_objects as go

# --- Azure Credentials  ---
AZURE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"
AZURE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"
credential = AzureKeyCredential(AZURE_KEY)
text_client = TextAnalyticsClient(endpoint=AZURE_ENDPOINT, credential=credential)

# --- Red Flags & Negative Keywords ---
RED_FLAGS = [
    "tidak tahu", "bukan tanggung jawab", "tidak peduli", "saya menyerah", "urusan orang lain",
    "bukan saya", "tidak mau", "menolak", "membiarkan", "bukan masalah saya", "malas", "tidak tertarik",
    "tunggu saja", "tidak penting", "ikut-ikut", "terserah", "tidak bisa", "tidak yakin", "takut salah",
    "lebih baik diam"
]
NEGATIVE_KEYWORDS = ["tidak", "malas", "enggan", "menolak", "gagal", "takut", "ragu", "salah", "lambat", "terlambat"]

# --- Sentiment Evaluation ---
def analyze_sentiment(text: str) -> str:
    try:
        result = text_client.analyze_sentiment([text])[0]
        return result.sentiment  # 'positive', 'neutral', or 'negative'
    except:
        return "neutral"

def evaluate_answer(text: str, sentiment: str) -> bool:
    text = text.lower()
    if any(flag in text for flag in RED_FLAGS):
        return False
    if any(word in text for word in NEGATIVE_KEYWORDS) and sentiment == "negative":
        return False
    return sentiment in ["positive", "neutral"]

# --- Page Configuration ---
st.set_page_config(page_title="KerjaTayang", page_icon="🎤", layout="centered")

# --- Load Question Data ---
@st.cache_data
def load_questions():
    return pd.read_csv("questions.csv")

questions_df = load_questions()

# --- UI ---
st.markdown("<h1 style='text-align:center;'>🎤 KerjaTayang</h1>", unsafe_allow_html=True)
st.markdown("Simulasi percakapan interaktif untuk membangun soft skill dengan bantuan **Azure Language Service**.")

# --- User Input ---
name = st.text_input("Nama lengkap:")
age = st.number_input("Usia:", min_value=13, max_value=99, step=1)
aspiration = st.text_input("Apa karier impianmu?")

if name and age and aspiration:
    st.success(f"Halo {name}, kamu akan mencoba simulasi peran kerja dengan 5 pertanyaan situasional.")

    # --- Role Selection ---
    role = st.selectbox("Pilih peran kerja:", questions_df["Role"].unique())
    required_skills = {
        "Data Analyst": ["Problem Solving", "Communication", "Accountability", "Teamwork", "Time Management"],
        "Product Manager": ["Leadership", "Problem Solving", "Communication", "Accountability", "Time Management"],
        "Digital Marketer": ["Creativity", "Communication", "Accountability", "Teamwork", "Time Management"],
        "Security Administrator": ["Problem Solving", "Communication", "Accountability", "Time Management"],
        "Content Creator": ["Creativity", "Communication", "Accountability", "Time Management"]
    }

    st.markdown("**Soft Skill yang diuji:**")
    for skill in required_skills[role]:
        st.markdown(f"- ✅ {skill}")

    role_questions = questions_df[questions_df["Role"] == role].reset_index(drop=True)
    score = 0
    skill_scores = {s: 0 for s in required_skills[role]}

    for idx, row in role_questions.iterrows():
        st.markdown(f"---\n**📘 Kasus {idx+1}:** {row['Scenario']}")
        st.markdown(f"🧑‍💼 <b><i>Rekruter:</i></b> {row['Question']}", unsafe_allow_html=True)

        user_response = st.text_area("🧑 Kamu:", key=f"ans_{idx}")

        if user_response:
            sentiment = analyze_sentiment(user_response)
            is_positive = evaluate_answer(user_response, sentiment)

            feedback = "✅ Jawabanmu mencerminkan sikap positif." if is_positive else "⚠️ Jawabanmu mengandung red flag atau sikap negatif."
            st.markdown(f"**Feedback:** {feedback} _(Sentimen: {sentiment})_")

            if is_positive:
                score += 1
                for skill in required_skills[role]:
                    if skill.lower() in row["Intent"].lower():
                        skill_scores[skill] += 1

    total_q = len(role_questions)
    if score > 0:
        st.markdown("---")
        st.subheader("📊 Ringkasan Hasil")
        st.write(f"Skor: **{score}/{total_q}**")
        status = "✅ Cocok untuk peran ini" if score / total_q >= 0.6 else "🔁 Perlu latihan lagi"
        st.write(f"Status: **{status}**")

        # Radar chart
        radar_labels = required_skills[role]
        radar_values = [skill_scores[s]/total_q for s in radar_labels]
        radar_values += radar_values[:1]
        radar_labels += radar_labels[:1]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=radar_values,
            theta=radar_labels,
            fill='toself',
            name='Skor Soft Skill'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,1])),
            showlegend=False
        )
        st.plotly_chart(fig)

        # TXT Export
        summary = f"KerjaTayang Simulation\nName: {name}\nRole: {role}\nScore: {score}/{total_q}\nStatus: {status}\n"
        st.download_button("📥 Unduh Hasil Simulasi", summary, file_name="hasil_kerjatayang.txt")
