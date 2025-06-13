import streamlit as st
import pandas as pd
import requests
import json
import matplotlib.pyplot as plt
from math import pi

# ================= Azure Language Service Config ==================
AZURE_LANGUAGE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"
AZURE_LANGUAGE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"

# ================= Load Questions CSV ==================
@st.cache_data
def load_questions():
    return pd.read_csv("questions.csv")

questions_df = load_questions()

# ================= Sentiment Analysis ==================
def get_sentiment_score(text):
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_LANGUAGE_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "documents": [
            {"id": "1", "language": "id", "text": text}
        ]
    }

    response = requests.post(AZURE_LANGUAGE_API_URL, headers=headers, json=body)
    result = response.json()

    sentiment = result['documents'][0]['sentiment']
    if sentiment == "positive":
        return 2
    elif sentiment == "neutral":
        return 1
    else:
        return 0

# ================= Radar Chart ==================
def plot_radar_chart(scores_dict):
    labels = list(scores_dict.keys())
    values = list(scores_dict.values())

    # Remove zero scores
    labels, values = zip(*[(l, v) for l, v in zip(labels, values) if v > 0])
    if not values:
        st.write("Tidak ada keterampilan positif yang terdeteksi.")
        return

    angles = [n / float(len(labels)) * 2 * pi for n in range(len(labels))]
    values += values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.plot(angles, values, linewidth=2, linestyle='solid')
    ax.fill(angles, values, 'skyblue', alpha=0.4)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_yticklabels([])
    st.pyplot(fig)

# ================= Streamlit UI ==================
st.set_page_config(page_title="KerjaTayang", page_icon="🎙️", layout="centered")

st.markdown(
    """
    <meta name="dicoding:email" content="andy.lie95@gmail.com">
    """,
    unsafe_allow_html=True
)

st.title("🎙️ KerjaTayang: Simulasi Soft Skill")

st.markdown("Silakan pilih peran kerja dan ikuti simulasi interaktif untuk mengevaluasi kesiapanmu.")

# Pilih role
roles = questions_df["Role"].dropna().unique()
selected_role = st.selectbox("Pilih peran kerja:", options=[""] + list(roles))

if selected_role:
    role_questions = questions_df[questions_df["Role"] == selected_role].reset_index(drop=True)
    role_skills = role_questions["Skills"].unique()

    st.markdown("**Skill yang akan diuji:** " + ", ".join(role_skills))

    if st.button("🚀 Mulai Simulasi"):
        st.session_state.current_q = 0
        st.session_state.responses = []
        st.session_state.scores = {}

if "current_q" in st.session_state and selected_role:
    q_index = st.session_state.current_q

    if q_index < len(role_questions):
        st.markdown(f"**📘 Kasus:** {role_questions.iloc[q_index]['Background']}**")
        st.markdown(f"👩‍💼 **Pertanyaan {q_index+1}:** {role_questions.iloc[q_index]['Question']}")

        response = st.text_input("✍️ Jawabanmu:", key=f"response_{q_index}")

        if st.button("Kirim Jawaban"):
            skill = role_questions.iloc[q_index]["Skills"]
            score = get_sentiment_score(response)

            # Simpan skor
            if skill not in st.session_state.scores:
                st.session_state.scores[skill] = 0
            st.session_state.scores[skill] += score

            st.session_state.responses.append((response, score))
            st.session_state.current_q += 1
            st.experimental_rerun()

    else:
        st.subheader("📊 Hasil Evaluasi")

        plot_radar_chart(st.session_state.scores)

        total_score = sum(st.session_state.scores.values())
        max_possible = len(role_questions) * 2
        percentage = total_score / max_possible * 100

        if percentage >= 50:
            st.success(f"Selamat! Kamu telah memiliki keterampilan dasar untuk peran **{selected_role}**.")
        else:
            lacking_skills = [k for k, v in st.session_state.scores.items() if v < 2]
            st.warning(
                f"Semangat! Kamu masih perlu mengembangkan keterampilan berikut untuk peran **{selected_role}**:\n\n- "
                + "\n- ".join(lacking_skills)
            )

        if st.button("🔁 Ulangi Simulasi"):
            del st.session_state.current_q
            del st.session_state.responses
            del st.session_state.scores
            st.experimental_rerun()
