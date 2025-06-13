import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np

# Set page config
st.set_page_config(page_title="KerjaTayang", page_icon="🎯", layout="centered")
st.markdown("""<meta name="dicoding:email" content="andy.lie95@gmail.com">""", unsafe_allow_html=True)

# AZURE CONFIG (integrated directly here)
AZURE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"
AZURE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"

# Load questions
@st.cache_data
def load_questions():
    return pd.read_csv("questions.csv")

questions_df = load_questions()

# Get sentiment
def get_sentiment(text):
    url = f"{AZURE_ENDPOINT}/text/analytics/v3.1/sentiment"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "documents": [{"id": "1", "language": "id", "text": text}]
    }
    try:
        r = requests.post(url, headers=headers, json=body)
        sentiment = r.json()["documents"][0]["sentiment"]
        return sentiment
    except:
        return "neutral"

# Convert sentiment to score
def sentiment_score(sentiment):
    return {"positive": 2, "neutral": 1, "negative": 0}.get(sentiment, 1)

st.title("🎯 KerjaTayang")
st.subheader("Simulasi Kasus Kerja Berbasis Soft Skills")

role = st.selectbox("Pilih peran kerja:", [""] + sorted(questions_df["Role"].unique()))
if role:
    questions = questions_df[questions_df["Role"] == role].reset_index(drop=True)
    skills = questions["Skills"].unique()
    st.markdown(f"**Keterampilan Utama:** {', '.join(skills)}")

    st.markdown("---")
    st.markdown("### ✍️ Jawabanmu:")

    responses = []
    for i, row in questions.iterrows():
        st.markdown(f"**🧑‍💼 Skenario {i+1}:** {row['Scenario']}")
        st.markdown(f"**🎤 Pertanyaan:** {row['Question']}")
        user_input = st.text_area(f"Jawaban {i+1}", key=f"answer_{i}")
        responses.append({
            "question": row["Question"],
            "response": user_input,
            "skill": row["Skills"]
        })

    if st.button("✅ Kirim Semua Jawaban"):
        result_data = []
        for r in responses:
            sentiment = get_sentiment(r["response"])
            score = sentiment_score(sentiment)
            result_data.append({
                "Skill": r["skill"],
                "Question": r["question"],
                "Response": r["response"],
                "Sentiment": sentiment,
                "Score": score
            })

        result_df = pd.DataFrame(result_data)

        # Summary chart
        skill_scores = result_df.groupby("Skill")["Score"].mean().reindex(skills, fill_value=0)
        labels = skill_scores.index.tolist()
        values = skill_scores.tolist()

        labels += labels[:1]
        values += values[:1]
        angles = [n / float(len(labels)) * 2 * np.pi for n in range(len(labels))]

        st.markdown("---")
        st.subheader("📊 Pemetaan Soft Skills")

        fig, ax = plt.subplots(subplot_kw={'polar': True})
        ax.plot(angles, values, 'o-', linewidth=2)
        ax.fill(angles, values, alpha=0.25)
        ax.set_thetagrids(np.degrees(angles[:-1]), labels)
        st.pyplot(fig)

        # Evaluation
        total_score = sum(result_df["Score"])
        max_score = len(result_df) * 2
        percentage = (total_score / max_score) * 100

        if percentage >= 50:
            st.success(f"🎉 Selamat! Kamu telah memiliki skill dasar untuk peran **{role}**.")
        else:
            underdeveloped = result_df[result_df["Score"] < 2]["Skill"].unique()
            st.warning(f"⚠️ Semangat! Kamu masih perlu mengembangkan skill: {', '.join(underdeveloped)}")

        st.markdown("---")
        st.markdown("Ingin mencoba ulang?")
        if st.button("🔄 Ulangi Simulasi"):
            st.experimental_rerun()
