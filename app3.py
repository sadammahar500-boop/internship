"""
RECRUITMENT DASHBOARD (Simple version)
Run:  streamlit run app.py

Flow:  Job Opening -> CVs aayein -> AI best CV suggest kare -> HR Shortlist/Reject
       -> Department ko forward -> Interview -> Offer -> Hired

Abhi data sample hai (session_state mein). Baad mein database / AI agent / email
"BACKEND" likhi jaghon par lagenge.
"""
import random
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Recruitment Dashboard", page_icon="👥", layout="wide")
S = st.session_state
TODAY = date.today()

# =============================================================================
# 1. SETTINGS (lists jo poori app mein use hoti hain)
# =============================================================================
DEPARTMENTS = ["IT", "Finance", "HR", "Marketing", "Sales"]
SKILLS = ["Python", "SQL", "Excel", "React", "Accounting", "Recruitment", "SEO", "Sales", "Communication", "Power BI"]

# Candidate ka safar (process ke steps)
STATUSES = ["Applied", "Shortlisted", "Sent to Department", "Interview", "Offer", "Hired", "Rejected"]

NEW_CV_DAYS = 7   # itne din ke andar aayi CV = "New", us se purani = "Existing"


# =============================================================================
# 2. SAMPLE DATA  (BACKEND: yahan database se data load hoga)
# =============================================================================
def make_sample_data():
    random.seed(1)
    jobs = pd.DataFrame([
        dict(job_id=1, title="Python Developer", department="IT", skills="Python,SQL", min_exp=2, salary_max=180000),
        dict(job_id=2, title="Accountant", department="Finance", skills="Accounting,Excel", min_exp=2, salary_max=110000),
        dict(job_id=3, title="HR Executive", department="HR", skills="Recruitment,Communication", min_exp=1, salary_max=95000),
        dict(job_id=4, title="Digital Marketer", department="Marketing", skills="SEO,Communication", min_exp=1, salary_max=100000),
        dict(job_id=5, title="Sales Executive", department="Sales", skills="Sales,Communication", min_exp=1, salary_max=90000),
    ])
    names = ["Ayesha Malik", "Hassan Shah", "Zain Raza", "Sana Khan", "Bilal Ahmed", "Fatima Noor", "Usman Ali", "Hina Tariq",
             "Ahmed Raza", "Mariam Siddiqui", "Kamran Javed", "Rabia Aslam", "Omar Sheikh", "Iqra Memon", "Saad Qureshi"]
    rows = []
    for i in range(1, 121):
        job = jobs.sample(1, random_state=i).iloc[0]
        pool = job["skills"].split(",") + random.sample(SKILLS, 3)
        rows.append(dict(
            cand_id=i, name=f"{random.choice(names)} {i}", job_id=job["job_id"],
            skills=",".join(sorted(set(random.sample(pool, 4)))),
            experience=random.randint(0, 9), expected_salary=random.randrange(60000, 200000, 5000),
            applied_on=TODAY - timedelta(days=random.randint(0, 60)),
            status="Applied", interview_date=None))
    return jobs, pd.DataFrame(rows)


def load_data():
    """Pehli dafa sample data banata hai."""
    if "jobs" not in S:
        S.jobs, S.cands = make_sample_data()
        S.messages = []          # email / notification log


# =============================================================================
# 3. AI LOGIC  (BACKEND: yahan Azure OpenAI agent lagega)
# =============================================================================
def match_percent(cand, job):
    """AI match: 70% skills match + 30% experience."""
    need = set(job["skills"].split(","))
    have = set(cand["skills"].split(","))
    skill_score = len(need & have) / len(need)
    exp_score = min(cand["experience"] / max(job["min_exp"], 1), 1)
    return round(skill_score * 70 + exp_score * 30)


def ai_salary(cand, job):
    """AI ka andaza: department ki base salary + experience."""
    base = {"IT": 80000, "Finance": 60000, "HR": 50000, "Marketing": 55000, "Sales": 50000}[job["department"]]
    return base + cand["experience"] * 9000


def cands_with_details():
    """Candidates table + job ka naam, match %, AI salary, New/Existing."""
    jobs = S.jobs.set_index("job_id")
    df = S.cands.copy()
    df["position"] = df["job_id"].map(jobs["title"])
    df["department"] = df["job_id"].map(jobs["department"])
    df["match"] = [match_percent(r, jobs.loc[r["job_id"]]) for _, r in df.iterrows()]
    df["ai_salary"] = [ai_salary(r, jobs.loc[r["job_id"]]) for _, r in df.iterrows()]
    df["cv_type"] = df["applied_on"].apply(lambda d: "New" if (TODAY - d).days <= NEW_CV_DAYS else "Existing")
    return df


# =============================================================================
# 4. ACTIONS  (status badalna + message bhejna)
# =============================================================================
def send_message(to, text):
    """BACKEND: yahan real email (Azure Communication Services) lagegi."""
    S.messages.insert(0, {"Time": datetime.now().strftime("%d %b %H:%M"), "To": to, "Message": text})


def get_cand(cand_id):
    return S.cands[S.cands["cand_id"] == cand_id].iloc[0]


def change_status(cand_id, new_status):
    S.cands.loc[S.cands["cand_id"] == cand_id, "status"] = new_status


def reject(cand_id, reason):
    change_status(cand_id, "Rejected")
    send_message(get_cand(cand_id)["name"], f"Aap ki application reject ho gayi hai. Wajah: {reason}. Shukriya.")


def shortlist(cand_id):
    change_status(cand_id, "Shortlisted")
    send_message(get_cand(cand_id)["name"], "Mubarak! Aap shortlist ho gaye hain.")


def send_to_department(cand_id):
    row = get_cand(cand_id)
    dept = S.jobs.set_index("job_id").loc[row["job_id"], "department"]
    change_status(cand_id, "Sent to Department")
    send_message(f"{dept} Department Head", f"{row['name']} ki CV review ke liye bheji gayi hai.")


def schedule_interview(cand_id, when):
    change_status(cand_id, "Interview")
    S.cands.loc[S.cands["cand_id"] == cand_id, "interview_date"] = when
    send_message(get_cand(cand_id)["name"], f"Aap ka interview {when} ko hai.")


def make_offer(cand_id):
    change_status(cand_id, "Offer")
    send_message(get_cand(cand_id)["name"], "Hum aap ko job offer dena chahte hain.")


def hire(cand_id):
    change_status(cand_id, "Hired")
    send_message(get_cand(cand_id)["name"], "Welcome to the team!")


# =============================================================================
# 5. PAGE: DASHBOARD  (poori recruitment ki summary)
# =============================================================================
def page_dashboard():
    st.title("📊 Dashboard")
    df = cands_with_details()

    # ---- Upar ke numbers
    c = st.columns(5)
    c[0].metric("Total CVs", len(df))
    c[1].metric("New CVs", int((df["cv_type"] == "New").sum()), help=f"Pichhle {NEW_CV_DAYS} din")
    c[2].metric("Shortlisted", int((df["status"] == "Shortlisted").sum()))
    c[3].metric("Interviews", int((df["status"] == "Interview").sum()))
    c[4].metric("Hired", int((df["status"] == "Hired").sum()))

    # ---- Process ka chart: kitne candidates kis step par hain
    st.subheader("Recruitment process (step-wise candidates)")
    st.bar_chart(df["status"].value_counts().reindex(STATUSES).fillna(0))

    # ---- Job openings ka summary
    st.subheader("Job openings")
    summary = df.groupby("position").agg(CVs=("cand_id", "count"), Best_Match=("match", "max")).reset_index()
    st.dataframe(summary, hide_index=True)


# =============================================================================
# 6. PAGE: JOB OPENINGS  (nayi job banana)
# =============================================================================
def page_jobs():
    st.title("💼 Job Openings")

    st.subheader("Nayi job banayein")
    with st.form("new_job", clear_on_submit=True):
        c1, c2 = st.columns(2)
        title = c1.text_input("Job title")
        dept = c2.selectbox("Department", DEPARTMENTS)
        skills = st.multiselect("Zaroori skills", SKILLS)
        c3, c4 = st.columns(2)
        min_exp = c3.number_input("Kam az kam experience (saal)", 0, 20, 2)
        salary = c4.number_input("Maximum salary (PKR)", 0, 1000000, 100000, 5000)
        if st.form_submit_button("Job save karein"):
            if title and skills:
                new_id = int(S.jobs["job_id"].max()) + 1
                S.jobs.loc[len(S.jobs)] = [new_id, title, dept, ",".join(skills), min_exp, salary]
                st.success("Job ban gayi ✅")
            else:
                st.error("Title aur kam az kam ek skill zaroori hai.")

    st.subheader("Sab jobs")
    st.dataframe(S.jobs, hide_index=True)


# =============================================================================
# 7. PAGE: CVs + AI SUGGESTION  (filters + best CVs)
# =============================================================================
def page_cvs():
    st.title("📄 CVs aur AI Suggestion")
    df = cands_with_details()

    # ---- Filters
    st.subheader("Filters")
    c = st.columns(4)
    job_filter = c[0].selectbox("Job", ["All"] + list(S.jobs["title"]))
    type_filter = c[1].radio("CV type", ["All", "New", "Existing"], horizontal=True)
    skill_filter = c[2].multiselect("Skill (subject)", SKILLS)
    dates = c[3].date_input("Date range", (TODAY - timedelta(days=60), TODAY))

    if job_filter != "All":
        df = df[df["position"] == job_filter]
    if type_filter != "All":
        df = df[df["cv_type"] == type_filter]
    for s in skill_filter:
        df = df[df["skills"].str.contains(s)]
    if len(dates) == 2:
        df = df[(df["applied_on"] >= dates[0]) & (df["applied_on"] <= dates[1])]

    # ---- AI best CVs (match % ke hisab se)
    st.subheader("🤖 AI recommended CVs")
    df = df.sort_values("match", ascending=False)
    best = df[df["status"] == "Applied"].head(5)
    if best.empty:
        st.info("Is filter par koi nayi CV nahi.")
    else:
        st.dataframe(best[["name", "position", "experience", "skills", "expected_salary", "ai_salary", "match"]],
                     hide_index=True,
                     column_config={"match": st.column_config.ProgressColumn("Match %", min_value=0, max_value=100, format="%d"),
                                    "expected_salary": "Expected salary", "ai_salary": "AI salary estimate"})
        if st.button("⭐ Yeh top 5 shortlist karein"):
            for cid in best["cand_id"]:
                shortlist(cid)
            st.rerun()

    # ---- Poori list
    st.subheader(f"Sab CVs ({len(df)})")
    st.dataframe(df[["cand_id", "name", "position", "cv_type", "applied_on", "experience", "skills",
                     "expected_salary", "ai_salary", "match", "status"]], hide_index=True)


# =============================================================================
# 8. PAGE: CANDIDATE PROCESS  (har step par action)
# =============================================================================
def page_process():
    st.title("🔄 Candidate Process")
    st.caption("Applied → Shortlisted → Department → Interview → Offer → Hired  (kisi bhi step par Reject)")
    df = cands_with_details()

    # Step choose karein
    step = st.radio("Step", STATUSES, horizontal=True)
    sub = df[df["status"] == step].sort_values("match", ascending=False)
    st.write(f"**{len(sub)}** candidates")
    st.dataframe(sub[["cand_id", "name", "position", "experience", "expected_salary", "match"]].head(30), hide_index=True)
    if sub.empty:
        return

    # Candidate choose karke action karein
    cand_id = st.selectbox("Candidate chunein", sub["cand_id"], format_func=lambda i: sub[sub["cand_id"] == i]["name"].iloc[0])

    st.subheader("Action")
    if step == "Applied":
        c1, c2 = st.columns(2)
        if c1.button("⭐ Shortlist"):
            shortlist(cand_id); st.rerun()
        reason = c2.selectbox("Reject ki wajah", ["Skills match nahi", "Experience kam", "Salary zyada", "Position fill ho gayi"])
        if c2.button("✖ Reject (candidate ko message jayega)"):
            reject(cand_id, reason); st.rerun()

    elif step == "Shortlisted":
        if st.button("📤 Department ko bhejein"):
            send_to_department(cand_id); st.rerun()

    elif step == "Sent to Department":
        c1, c2 = st.columns(2)
        when = c1.date_input("Interview date", TODAY + timedelta(days=3))
        if c1.button("✔ Department ne approve kiya → Interview"):
            schedule_interview(cand_id, when); st.rerun()
        if c2.button("✖ Department ne decline kiya"):
            reject(cand_id, "Department ne select nahi kiya"); st.rerun()

    elif step == "Interview":
        c1, c2 = st.columns(2)
        if c1.button("💼 Offer dein"):
            make_offer(cand_id); st.rerun()
        if c2.button("✖ Reject"):
            reject(cand_id, "Interview ke baad select nahi hua"); st.rerun()

    elif step == "Offer":
        c1, c2 = st.columns(2)
        if c1.button("✅ Offer accept → Hired"):
            hire(cand_id); st.rerun()
        if c2.button("✖ Offer decline"):
            reject(cand_id, "Candidate ne offer decline ki"); st.rerun()

    else:
        st.info("Is step par aage koi action nahi.")


# =============================================================================
# 9. PAGE: MESSAGES  (jo emails / notifications gayi)
# =============================================================================
def page_messages():
    st.title("🔔 Messages / Notifications")
    st.caption("Reject par candidate ko, Department ko forward par department head ko message jata hai.")
    if S.messages:
        st.dataframe(pd.DataFrame(S.messages), hide_index=True)
    else:
        st.info("Abhi koi message nahi gaya.")


# =============================================================================
# 10. MAIN: sidebar menu + page chalana
# =============================================================================
load_data()

PAGES = {
    "📊 Dashboard": page_dashboard,
    "💼 Job Openings": page_jobs,
    "📄 CVs aur AI Suggestion": page_cvs,
    "🔄 Candidate Process": page_process,
    "🔔 Messages": page_messages,
}

st.sidebar.title("👥 Recruitment")
choice = st.sidebar.radio("Menu", list(PAGES), label_visibility="collapsed")
PAGES[choice]()