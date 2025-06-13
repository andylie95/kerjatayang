import streamlit as st
import pandas as pd
import requests
import os

# ✅ MUST be the first Streamlit command
st.set_page_config(page_title="KerjaTayang", page_icon="🎙️", layout="centered")

# -------------------------
# Azure Language Service Setup
# -------------------------
AZURE_LANGUAGE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"
AZURE_LANGUAGE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"
AZURE_LANGUAGE_REGION = "southeastasia"

headers = {
    "Ocp-Apim-Subscription-Key": AZURE_LANGUAGE_KEY,
    "Ocp-Apim-Subscription-Region": AZURE_LANGUAGE_REGION,
    "Content-Type": "application/json"
}

def analyze_sentiment(text):
    url = f"{AZURE_LANGUAGE_ENDPOINT}language/:analyze-text?api-version=2022-05-01"
    body = {
        "kind": "SentimentAnalysis",
        "parameters": {
            "modelVersion": "latest"
        },
        "analysisInput": {
            "documents": [
                {"id": "1", "language": "id", "text": text}
            ]
        }
    }
    response = requests.post(url, headers=headers, json=body)
    result = response.json()
    sentiment = result['results']['documents'][0]['sentiment']
    return sentiment

# -------------------------
# Load Questions CSV
# -------------------------
@st.cache_data
def load_questions():
    return pd.read_csv("questions.csv")

df = load_questions()

# -------------------------
# Streamlit UI
# -------------------------
st.title("🎯 KerjaTayang: Simulasi Soft Skill untuk Karir Impian")
st.write("Simulasi ini akan mengukur kesiapan kamu berdasarkan situasi kerja nyata.")

name = st.text_input("Nama kamu:")
age = st.number_input("Usia kamu:", min_value=10, max_value=100, step=1)
selected_role = st.selectbox("Pilih peran pekerjaan yang ingin kamu simulasikan:", df['job_role'].unique())

if name and age and selected_role:
    st.markdown("---")
    st.subheader(f"📋 Pertanyaan untuk {selected_role}")

    role_questions = df[df['job_role'] == selected_role].sort_values("question_id")
    responses = []
    score = 0

    with st.form("simulation_form"):
        for idx, row in role_questions.iterrows():
            response = st.text_area(f"{row['question_id']}. {row['question']}", key=f"q{row['question_id']}")
            responses.append((row['question_id'], response))
        submitted = st.form_submit_button("Kirim Jawaban & Analisis")

    if submitted:
        st.markdown("---")
        st.subheader("📊 Hasil Analisis")
        for qid, user_input in responses:
            if not user_input.strip():
                st.warning(f"❗ Pertanyaan {qid} belum dijawab.")
                continue
            sentiment = analyze_sentiment(user_input)
            st.write(f"**Jawaban #{qid}**: *{sentiment}*")
            if sentiment in ['positive', 'neutral']:
                st.success("✅ Jawaban menunjukkan soft skill yang baik.")
                score += 1
            else:
                st.error("⚠️ Jawaban menunjukkan perlunya peningkatan.")

        st.markdown("---")
        st.subheader("🏁 Ringkasan")

        if score >= 3:
            st.balloons()
            st.success(f"🎉 {name}, kamu cocok sebagai seorang **{selected_role}**! Skor kamu: {score}/5")
        else:
            st.warning(f"💡 {name}, tetap semangat! Kamu mendapatkan skor {score}/5. Latihan akan membuatmu semakin siap.")

        st.markdown("---")
        if st.button("🔽 Unduh Hasil sebagai TXT"):
            result_text = f"KerjaTayang - Simulasi {selected_role}\nNama: {name}\nUsia: {age}\n\n"
            for qid, user_input in responses:
                result_text += f"{qid}. {user_input}\n"
            result_text += f"\nSkor Akhir: {score}/5\n"
            st.download_button("Klik untuk unduh", result_text, file_name="kerjatayang_result.txt")

