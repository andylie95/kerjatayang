import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np

# Azure config (replace with your values)
AZURE_ENDPOINT = "https://kerjatayang.cognitiveservices.azure.com/"
AZURE_KEY = "8NT1mJXQxgeY7dJZioDN236Uu3DLzXfu5foUlggWBVUgOvIbJt8iJQQJ99BFACqBBLyXJ3w3AAAaACOGIhsJ"
AZURE_REGION = "southeastasia"

# Soft skill red flag keywords in Indonesian
red_flag_keywords = [
    "menolak", "menghindar", "tidak peduli", "acuh", "membiarkan",
    "tidak mau", "emosi", "menyerah", "tidak tertarik", "tidak ikut",
    "salahkan", "malas", "tidak mau berusaha", "tidak penting",
    "tidak mendukung", "tidak mau belajar", "pasrah", "tidak sopan",
    "tidak tanggung jawab", "tidak membantu"
]

# Setup
st.set_page_config(page_title="KerjaTayang", page_icon="🧑‍💼", layout="centered")
st.title("💼 KerjaTayang: Simulasi Soft Skill Berbasis Role")

# Upload questions CSV
uploaded_file = st.file_uploader("📄 Upload CSV pertanyaan", type=["csv"])
if uploaded_file:
    questions_df = pd.read_csv(uploaded_file)

    # Pilih peran
    roles = questions_df["Role"].dropna().unique().tolist()
    role = st.selectbox("🔽 Pilih peran kerja yang ingin disimulasikan:", [""] + roles)

    if role:
        st.success(f"Simulasi untuk peran: **{role}**")

        # Ambil daftar skill
        skill_list = questions_df[questions_df["Role"] == role]["Skills"].dropna().unique().tolist()
        st.info("Skill yang dibutuhkan:")
        for skill in skill_list:
            st.markdown(f"- ✅ {skill}")

        # Tombol mulai simulasi
        if st.button("🚀 Mulai Simulasi"):
            st.session_state['start_sim'] = True
            st.session_state['responses'] = []
            st.session_state['softskill_scores'] = {skill: 0 for skill in skill_list}
            st.experimental_rerun()

    # Mulai Simulasi
    if st.session_state.get('start_sim'):
        st.header("🎭 Sesi Simulasi")

        selected_qs = questions_df[questions_df["Role"] == role]
        for idx, row in selected_qs.iterrows():
            st.markdown(f"🧑 **Skenario:** {row['Scenario']}")
            response = st.text_area(f"💬 Tanggapanmu:", key=f"resp_{idx}")

            if response:
                # Kirim ke Azure Sentiment API
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

                sentiment = analyze_sentiment(response)

                # Red flag detection
                flags = [k for k in red_flag_keywords if k in response.lower()]
                softskill = row['Skills']

                score = 2 if sentiment == "positive" and not flags else 0 if sentiment == "negative" or flags else 1
                st.session_state['softskill_scores'][softskill] = max(score, st.session_state['softskill_scores'].get(softskill, 0))

                # Show feedback
                if score == 2:
                    st.success("✅ Jawabanmu mencerminkan soft skill yang baik.")
                elif score == 1:
                    st.warning("🟡 Jawabanmu masih netral, bisa dikembangkan.")
                else:
                    st.error("❌ Jawabanmu menunjukkan red flag atau negatif.")

        if st.button("📊 Lihat Evaluasi"):
            st.session_state['submitted'] = True

    # Evaluasi akhir
    if st.session_state.get('submitted'):
        st.header("📈 Evaluasi & Rekomendasi")

        scores = st.session_state['softskill_scores']
        positive = [s for s in scores.values() if s == 2]
        ratio = len(positive) / len(scores) * 100

        if ratio >= 50:
            st.success(f"🎉 Selamat! Kamu telah memiliki skill dasar untuk peran **{role}**.")
        else:
            skills_to_improve = [k for k, v in scores.items() if v < 2]
            st.error("😅 Semangat! Kamu masih perlu mengembangkan skill berikut:")
            for s in skills_to_improve:
                st.markdown(f"- ⚠️ {s}")

        # Radar Chart
        st.subheader("🧭 Pemetaan Soft Skill")

        skills_sorted = sorted(scores.keys())
        values = [scores[k] for k in skills_sorted]

        labels = skills_sorted
        num_vars = len(labels)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

        values += values[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.plot(angles, values, color='blue', linewidth=2)
        ax.fill(angles, values, color='skyblue', alpha=0.25)
        ax.set_thetagrids(np.degrees(angles[:-1]), labels)
        ax.set_ylim(0, 2)
        st.pyplot(fig)
