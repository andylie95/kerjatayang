
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

# ---- CONFIG ----
st.set_page_config(page_title="KerjaTayang", page_icon="🎙️", layout="centered")
st.markdown("<h1 style='text-align: center;'>🎙️ KerjaTayang: Simulasi Dunia Kerja</h1>", unsafe_allow_html=True)
st.markdown("<meta name='dicoding:email' content='andy.lie95@gmail.com'>", unsafe_allow_html=True)

# ---- SESSION INIT ----
if "started" not in st.session_state:
    st.session_state.started = False
if "role" not in st.session_state:
    st.session_state.role = ""
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "responses" not in st.session_state:
    st.session_state.responses = []
if "score_map" not in st.session_state:
    st.session_state.score_map = defaultdict(int)

# ---- DATA ----
@st.cache_data
def load_questions():
    df = pd.read_csv("questions.csv")
    df.columns = df.columns.str.strip()
    return df

questions_df = load_questions()

# ---- SELECT ROLE ----
roles = questions_df["Role"].dropna().unique()
role = st.selectbox("👨‍💼 Pilih peran kerja yang ingin disimulasikan:", [""] + list(roles))

if role and not st.session_state.started:
    if st.button("🚀 Mulai Simulasi"):
        st.session_state.role = role
        st.session_state.started = True
        st.rerun()

# ---- MAIN SIMULATION ----
if st.session_state.started and st.session_state.role:
    st.markdown(f"### Simulasi untuk peran: **{st.session_state.role}**")
    role_questions = questions_df[questions_df["Role"] == st.session_state.role].reset_index(drop=True)

    # Display required skills
    skills_for_role = role_questions["Skills"].dropna().unique()
    st.info("💡 Soft Skills yang dibutuhkan: " + ", ".join(skills_for_role))

    q_index = st.session_state.current_question

    if q_index < len(role_questions):
        question_row = role_questions.iloc[q_index]
        st.markdown(f"**📘 Situasi:** {question_row['Background']}")
        st.markdown(f"**❓ Pertanyaan:** {question_row['Question']}")
        user_input = st.text_area("✍️ Jawaban kamu:", key=f"answer_{q_index}")

        if st.button("Kirim Jawaban"):
            # Soft skill scoring logic
            red_flags = ["tidak", "menolak", "menghindari", "tidak tahu", "malas", "membiarkan", "tidak mau"]
            score = 2  # Default: positive
            lowered = user_input.lower()

            if any(flag in lowered for flag in red_flags):
                score = 0
            elif any(neg in lowered for neg in ["mungkin", "kurang", "ragu"]):
                score = 1

            # Save result
            st.session_state.responses.append({
                "Skill": question_row["Skills"],
                "Score": score,
                "Jawaban": user_input
            })
            st.session_state.score_map[question_row["Skills"]] += score
            st.session_state.current_question += 1
            st.rerun()
    else:
        st.success("✅ Simulasi selesai!")

        # Show radar chart
        st.markdown("### 🔎 Pemetaan Soft Skills")

        skill_scores = st.session_state.score_map
        skill_names = list(skill_scores.keys())
        scores = list(skill_scores.values())

        filtered_skills = [s for s in skill_names if skill_scores[s] > 0]
        filtered_scores = [skill_scores[s] for s in filtered_skills]

        if filtered_skills:
            angles = np.linspace(0, 2 * np.pi, len(filtered_skills), endpoint=False).tolist()
            scores = filtered_scores + filtered_scores[:1]
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
            ax.plot(angles, scores, "o-", linewidth=2)
            ax.fill(angles, scores, alpha=0.25)
            ax.set_thetagrids(np.degrees(angles[:-1]), filtered_skills)
            ax.set_title("Soft Skills Radar")
            st.pyplot(fig)

        # Final evaluation
        total_score = sum([r["Score"] for r in st.session_state.responses])
        max_score = len(st.session_state.responses) * 2
        percentage = (total_score / max_score) * 100 if max_score > 0 else 0

        if percentage >= 50:
            st.success(f"🎉 Selamat! Kamu telah memiliki skill dasar untuk peran **{st.session_state.role}**.")
        else:
            low_skills = [r["Skill"] for r in st.session_state.responses if r["Score"] < 2]
            st.warning("💪 Semangat! Kamu masih perlu mengembangkan skill berikut:")
            st.markdown("- " + "
- ".join(set(low_skills)))

        st.button("🔁 Ulangi Simulasi", on_click=lambda: st.session_state.clear())
