import streamlit as st
import pandas as pd
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

# Azure credentials
AZURE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"
AZURE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"

# Initialize Azure Text Analytics
def authenticate_client():
    credential = AzureKeyCredential(AZURE_KEY)
    client = TextAnalyticsClient(endpoint=AZURE_ENDPOINT, credential=credential)
    return client

client = authenticate_client()

# Sentiment check
def analyze_sentiment(text):
    try:
        response = client.analyze_sentiment([text])[0]
        return response.sentiment  # positive, neutral, negative
    except Exception as e:
        return "error"

# Load questions from CSV
@st.cache_data
def load_questions():
    return pd.read_csv("questions.csv")

questions_df = load_questions()

# App Title
st.set_page_config(page_title="KerjaTayang", page_icon="🎙️", layout="centered")
st.title("🎙️ KerjaTayang: Simulasi Dunia Kerja")
st.markdown("Pelatihan soft skill berbasis simulasi untuk generasi siap kerja.")

# User intro
st.subheader("🔍 Siapa kamu?")
name = st.text_input("Nama kamu:")
age = st.number_input("Usia", min_value=12, max_value=60, step=1)
aspiration = st.text_input("Cita-cita kariermu?")

if name and aspiration:
    st.success(f"Halo {name}! Yuk kita mulai simulasi jadi **{aspiration}**!")

    # Pick job role
    roles = questions_df['job_role'].unique().tolist()
    selected_role = st.selectbox("Pilih jenis pekerjaan yang ingin kamu simulasikan:", roles)

    if selected_role:
        user_answers = []
        user_sentiments = []

        st.markdown("### ✍️ Jawab 5 situasi berikut dengan sejujur-jujurnya:")

        role_questions = questions_df[questions_df['job_role'] == selected_role].sort_values("question_id")

        for idx, row in role_questions.iterrows():
            st.markdown(f"**Situasi {row['question_id']}:** {row['question']}")
            answer = st.text_area(f"Jawabanmu ({row['question_id']})", key=f"q_{row['question_id']}")

            if answer:
                sentiment = analyze_sentiment(answer)
                user_answers.append(answer)
                user_sentiments.append(sentiment)
                if sentiment == "positive":
                    st.success("✅ Jawabanmu menunjukkan sikap positif!")
                elif sentiment == "neutral":
                    st.warning("➖ Jawabanmu netral, bisa dikembangkan lagi.")
                elif sentiment == "negative":
                    st.error("❌ Jawabanmu menunjukkan kurangnya kesiapan.")
                else:
                    st.warning("⚠️ Analisis gagal. Coba lagi.")

        if len(user_sentiments) == 5:
            fit_score = user_sentiments.count("positive") / 5 * 100
            st.markdown("---")
            st.subheader("📊 Hasil Simulasi:")

            if fit_score >= 60:
                st.success(f"🎉 Selamat {name}! Kamu cocok sebagai **{selected_role}**! ({fit_score:.0f}%)")
            else:
                st.info(f"Semangat, {name}! Kamu bisa latihan lagi untuk menjadi **{selected_role}** yang lebih siap. ({fit_score:.0f}%)")

            # Download option
            result_text = "\n\n".join([f"{i+1}. {q}\nJawaban: {a}" for i, (q, a) in enumerate(zip(role_questions['question'], user_answers))])
            st.download_button("📥 Unduh Jawaban & Hasil", result_text, file_name=f"{name}_hasil_kerjatayang.txt")

