import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np

# Set page config first
st.set_page_config(page_title="KerjaTayang", page_icon="🎯", layout="centered")
st.markdown("""<meta name="dicoding:email" content="andy.lie95@gmail.com">""", unsafe_allow_html=True)

# Azure config
AZURE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"
AZURE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"

# Load questions
@st.cache_data
def load_questions():
    return pd.read_csv("questions.csv")

questions_df = load_questions()

# Sentiment function
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

def sentiment_score(sentiment):
    return {"positive": 2, "neutral": 1, "negative": 0}.get(sentiment, 1)

# Interface
st.title("🎯 KerjaTayang")
st.subheader("Simulasi Kasus Kerja Berbasis Soft Skills")

# Role Selection
role = st.selectbox("Pilih peran kerja:", [""] + sorted(questions_df["Role"].unique()))
if role:
    skills = questions_df[questions_df["Role"] == role]["Skills"].unique()
    st.markdown(f"**🧠 Keterampilan utama:** {', '.join(skills)}")
    if "start" not in st.session_state:
        if st.button("🚀 Mulai Simulasi"):
            st.session_state.start = True
            st.session_state.step = 0
            st.session_state.responses = []
            st.session_state.scores = []
else:
    st.stop()

if st.session_state.get("start", False):
    questions = questions_df[questions_df["Role"] == role].reset_index(drop=True)
    step = st.session_state.get("step", 0)

    if step < len(questions):
        row = questions.iloc[step]
        st.markdown(f"🧑‍💼 **Skenario {step+1}**: {row['Scenario']}")
        st.markdown(f"🎤 **Pertanyaan:** {row['Question']}")
        user_input = st.text_area("✍️ Jawabanmu:", key=f"input_{step}")

        if st.button("✅ Kirim Jawaban"):
            sentiment = get_sentiment(user_input)
            score = sentiment_score(sentiment)
            st.session_state.responses.append({
                "question": row["Question"],
                "response": user_input,
                "sentiment": sentiment,
                "score": score,
                "skill": row["Skills"]
            })
            st.session_state.scores.append(score)
            st.session_state.step += 1
            st.experimental_rerun()
    else:
        st.success("✅ Simulasi selesai!")
        df = pd.DataFrame(st.session_state.responses)
        skill_summary = df.groupby("skill")["score"].mean().reset_index()
        skill_summary = skill_summary[skill_summary["score"] > 0]

        if not skill_summary.empty:
            # Radar chart
            labels = skill_summary["skill"].tolist()
            values = skill_summary["score"].tolist()
            labels += labels[:1]
            values += values[:1]

            angles = [n / float(len(labels)) * 2 * np.pi for n in range(len(labels))]
            fig, ax = plt.subplots(subplot_kw={"polar": True})
            ax.plot(angles, values, "o-", linewidth=2)
            ax.fill(angles, values, alpha=0.25)
            ax.set_thetagrids(np.degrees(angles[:-1]), labels)
            st.pyplot(fig)

        total = sum(st.session_state.scores)
        max_score = len(st.session_state.scores) * 2
        percentage = total / max_score * 100

        if percentage >= 50:
            st.success(f"🎉 Selamat, kamu telah memiliki skill dasar untuk peran **{role}**!")
        else:
            underdeveloped = df[df["score"] < 2]["skill"].unique()
            st.warning(f"⚠️ Semangat! Kamu masih perlu mengembangkan skill: {', '.join(underdeveloped)}")

        if st.button("🔄 Ulangi Simulasi"):
            for k in ["start", "step", "responses", "scores"]:
                st.session_state.pop(k, None)
            st.experimental_rerun()
