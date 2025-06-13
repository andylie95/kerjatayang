import streamlit as st
import pandas as pd
import requests

# ====== KONFIGURASI AZURE LANGUAGE SERVICE ======
AZURE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"
AZURE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"
AZURE_REGION = "southeastasia"

# ====== RED FLAG KEYWORDS ======
red_flag_keywords = [
    "menolak", "menghindar", "tidak peduli", "acuh", "membiarkan",
    "tidak mau", "emosi", "menyerah", "tidak tertarik", "tidak ikut",
    "salahkan", "malas", "tidak mau berusaha", "tidak penting",
    "tidak mendukung", "tidak mau belajar", "pasrah", "tidak sopan",
    "tidak tanggung jawab", "tidak membantu"
]

# ====== FUNGSI ANALISIS SENTIMEN MENGGUNAKAN AZURE ======
def analyze_sentiment(text):
    url = AZURE_ENDPOINT + "/text/analytics/v3.1/sentiment"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_REGION,
        "Content-Type": "application/json"
    }
    body = {"documents": [{"id": "1", "language": "id", "text": text}]}
    r = requests.post(url, headers=headers, json=body)
    result = r.json()
    try:
        return result['documents'][0]['sentiment']
    except:
        return "neutral"

# ====== SETUP STREAMLIT ======
st.set_page_config(page_title="KerjaTayang", page_icon="🧠", layout="centered")
st.title("🎯 KerjaTayang: Simulasi Soft Skill Berdasarkan Peran")

uploaded_file = st.file_uploader("📂 Upload file pertanyaan (CSV)", type=["csv"])
if uploaded_file:
    questions_df = pd.read_csv(uploaded_file)

    roles = questions_df["Role"].dropna().unique().tolist()
    role = st.selectbox("💼 Pilih peran kerja:", [""] + roles)

    if role:
        st.success(f"Simulasi akan dilakukan untuk peran: **{role}**")
        skills = questions_df[questions_df["Role"] == role]["Skills"].dropna().unique().tolist()
        st.markdown("#### 📌 Soft Skill Utama:")
        for s in skills:
            st.markdown(f"- {s}")

        if st.button("🚀 Mulai Simulasi"):
            st.session_state['mulai'] = True
            st.session_state['results'] = []

    # ====== SIMULASI BERLANGSUNG ======
    if st.session_state.get('mulai'):
        st.header("🧪 Simulasi Dimulai")

        selected_questions = questions_df[questions_df["Role"] == role]
        for i, row in selected_questions.iterrows():
            st.markdown(f"🧑 **Skenario:** {row['Scenario']}")
            response = st.text_area("💬 Jawabanmu:", key=f"q_{i}")

            if response:
                sentiment = analyze_sentiment(response)
                flags = [k for k in red_flag_keywords if k in response.lower()]
                score = 2 if sentiment == "positive" and not flags else 0 if sentiment == "negative" or flags else 1

                st.session_state['results'].append({
                    "skill": row["Skills"],
                    "sentiment": sentiment,
                    "red_flag": bool(flags),
                    "score": score
                })

        if st.button("📊 Evaluasi Hasil"):
            st.session_state['evaluasi'] = True

    # ====== EVALUASI ======
    if st.session_state.get('evaluasi'):
        st.header("📋 Hasil Evaluasi Soft Skill")
        result_df = pd.DataFrame(st.session_state['results'])

        if result_df.empty:
            st.warning("Belum ada jawaban yang diisi.")
        else:
            fit_count = len(result_df[result_df["score"] == 2])
            total = len(result_df)
            percentage = (fit_count / total) * 100

            if percentage >= 50:
                st.success(f"🎉 Selamat! Kamu telah menguasai soft skill dasar untuk peran **{role}**.")
            else:
                st.warning("💡 Tetap semangat! Kamu masih perlu mengembangkan soft skill berikut:")
                needs_improvement = result_df[result_df["score"] < 2]["skill"].unique()
                for s in needs_improvement:
                    st.markdown(f"- 🔧 {s}")
