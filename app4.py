"""
RECRUITMENT DASHBOARD
Run:  streamlit run app.py

Process:  Job Opening -> CVs received -> AI recommends best CVs -> Shortlist / Reject
          -> Department review -> Interview -> Offer -> Hired

Access control (RBAC): every user has a role, every role has permissions.
Pages and buttons are shown / enabled only if the role has the permission.

Data is sample data kept in st.session_state. Later, the places marked
"BACKEND" are replaced with the real database, AI agent, email service and login.
"""

# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
import hashlib
import random
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Recruitment Suite", page_icon="👥", layout="wide")
S = st.session_state
TODAY = date.today()


# ===========================================================================
# 1. CONSTANTS
# ===========================================================================
# Departments and skills used across the app
DEPARTMENTS = ["IT", "Finance", "HR", "Marketing", "Sales"]
SKILLS = ["Python", "SQL", "Excel", "React", "Accounting", "Recruitment",
          "SEO", "Sales", "Communication", "Power BI"]

# Steps a candidate moves through
STATUSES = ["Applied", "Shortlisted", "Sent to Department", "Interview", "Offer", "Hired", "Rejected"]

# A CV applied within this many days is "New", older CVs are "Existing"
NEW_CV_DAYS = 7

REJECT_REASONS = ["Skills do not match", "Experience below requirement",
                  "Salary expectation too high", "Position filled"]

# Column names shown to the user
COLUMN_LABELS = {
    "cand_id": "ID", "name": "Candidate", "position": "Position", "department": "Department",
    "cv_type": "CV Type", "applied_on": "Applied On", "experience": "Experience (yrs)",
    "skills": "Skills", "expected_salary": "Expected Salary", "ai_salary": "AI Salary Estimate",
    "match": "Match %", "status": "Status", "interview_date": "Interview Date",
}


# ===========================================================================
# 2. ROLE BASED ACCESS CONTROL (RBAC)
# ===========================================================================
# All permissions available in the system
ALL_PERMISSIONS = [
    "view_dashboard", "view_jobs", "manage_jobs", "view_cvs", "view_pipeline",
    "shortlist", "reject", "forward_to_department", "dept_decision",
    "make_offer", "hire", "view_messages", "manage_users",
]

# Which role has which permissions
ROLE_PERMISSIONS = {
    "Admin": set(ALL_PERMISSIONS),
    "HR Manager": set(ALL_PERMISSIONS) - {"manage_users", "dept_decision"},
    "Recruiter": {"view_dashboard", "view_jobs", "view_cvs", "view_pipeline",
                  "shortlist", "reject", "forward_to_department", "view_messages"},
    "Department Head": {"view_dashboard", "view_cvs", "view_pipeline", "dept_decision", "view_messages"},
    "Viewer": {"view_dashboard", "view_jobs", "view_cvs", "view_pipeline"},
}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Demo users. BACKEND: replace with Microsoft Entra ID (Azure AD) sign-in
USERS = {
    "admin": dict(name="Sadam Ahmed", role="Admin", department=None, password=hash_password("Admin@123")),
    "hr.manager": dict(name="Ayesha Khan", role="HR Manager", department=None, password=hash_password("Hr@12345")),
    "recruiter": dict(name="Bilal Ahmed", role="Recruiter", department=None, password=hash_password("Rec@12345")),
    "it.head": dict(name="Imran Qureshi", role="Department Head", department="IT", password=hash_password("Dept@12345")),
    "viewer": dict(name="Nida Farooq", role="Viewer", department=None, password=hash_password("View@12345")),
}
DEMO_PASSWORDS = {"admin": "Admin@123", "hr.manager": "Hr@12345", "recruiter": "Rec@12345",
                  "it.head": "Dept@12345", "viewer": "View@12345"}


def can(permission):
    """True if the signed-in user's role has this permission."""
    return bool(S.get("user")) and permission in ROLE_PERMISSIONS[S.user["role"]]


def scoped(df):
    """A Department Head only sees candidates of their own department."""
    if S.user["role"] == "Department Head":
        return df[df["department"] == S.user["department"]]
    return df


def log_audit(action):
    """Keeps a record of who did what."""
    S.audit.insert(0, {"Time": datetime.now().strftime("%d %b %H:%M"), "User": S.user["name"],
                       "Role": S.user["role"], "Action": action})


# ===========================================================================
# 3. SAMPLE DATA  (BACKEND: load from the database)
# ===========================================================================
def make_sample_data():
    random.seed(1)
    jobs = pd.DataFrame([
        dict(job_id=1, title="Python Developer", department="IT", skills="Python,SQL", min_exp=2, salary_max=180000, status="Open"),
        dict(job_id=2, title="Accountant", department="Finance", skills="Accounting,Excel", min_exp=2, salary_max=110000, status="Open"),
        dict(job_id=3, title="HR Executive", department="HR", skills="Recruitment,Communication", min_exp=1, salary_max=95000, status="Open"),
        dict(job_id=4, title="Digital Marketer", department="Marketing", skills="SEO,Communication", min_exp=1, salary_max=100000, status="Open"),
        dict(job_id=5, title="Sales Executive", department="Sales", skills="Sales,Communication", min_exp=1, salary_max=90000, status="Open"),
    ])
    names = ["Ayesha Malik", "Hassan Shah", "Zain Raza", "Sana Khan", "Bilal Ahmed", "Fatima Noor", "Usman Ali",
             "Hina Tariq", "Ahmed Raza", "Mariam Siddiqui", "Kamran Javed", "Rabia Aslam", "Omar Sheikh", "Iqra Memon"]
    rows = []
    for i in range(1, 121):
        job = jobs.sample(1, random_state=i).iloc[0]
        pool = job["skills"].split(",") + random.sample(SKILLS, 3)
        status = random.choices(STATUSES, weights=[45, 12, 12, 10, 6, 5, 10])[0]
        rows.append(dict(
            cand_id=i, name=f"{random.choice(names)} {i}", job_id=job["job_id"],
            skills=",".join(sorted(set(random.sample(pool, 4)))),
            experience=random.randint(0, 9), expected_salary=random.randrange(60000, 200000, 5000),
            applied_on=TODAY - timedelta(days=random.randint(0, 60)), status=status,
            interview_date=TODAY + timedelta(days=random.randint(1, 10)) if status == "Interview" else None))
    return jobs, pd.DataFrame(rows)


def load_data():
    """Creates the sample data once per session."""
    if "jobs" not in S:
        S.jobs, S.cands = make_sample_data()
        S.messages = [
            {"Time": "Today 09:15", "Type": "Candidate", "To": "Ayesha Malik 1", "Message": "Your application has been received."},
            {"Time": "Today 09:40", "Type": "Department", "To": "IT Department Head", "Message": "3 candidates are ready for your review."},
            {"Time": "Today 10:05", "Type": "Candidate", "To": "Hassan Shah 2", "Message": "Congratulations! You have been shortlisted."},
        ]
        S.audit = []
        S.flash = None


# ===========================================================================
# 4. AI LOGIC  (BACKEND: replace with an Azure OpenAI agent)
# ===========================================================================
def match_percent(cand, job):
    """AI match score: 70% skills match + 30% experience."""
    need = set(job["skills"].split(","))
    have = set(cand["skills"].split(","))
    skill_score = len(need & have) / len(need)
    exp_score = min(cand["experience"] / max(job["min_exp"], 1), 1)
    return round(skill_score * 70 + exp_score * 30)


def ai_salary(cand, job):
    """AI salary estimate: department base salary + experience."""
    base = {"IT": 80000, "Finance": 60000, "HR": 50000, "Marketing": 55000, "Sales": 50000}[job["department"]]
    return base + cand["experience"] * 9000


def cands_with_details():
    """Candidates joined with job info, match %, AI salary and New / Existing flag."""
    jobs = S.jobs.set_index("job_id")
    df = S.cands.copy()
    df["position"] = df["job_id"].map(jobs["title"])
    df["department"] = df["job_id"].map(jobs["department"])
    df["match"] = [match_percent(r, jobs.loc[r["job_id"]]) for _, r in df.iterrows()]
    df["ai_salary"] = [ai_salary(r, jobs.loc[r["job_id"]]) for _, r in df.iterrows()]
    df["cv_type"] = df["applied_on"].apply(lambda d: "New" if (TODAY - d).days <= NEW_CV_DAYS else "Existing")
    return scoped(df)


# ===========================================================================
# 5. ACTIONS  (status changes, messages, permission checks)
# ===========================================================================
def send_message(kind, to, text):
    """BACKEND: send a real email with Azure Communication Services."""
    S.messages.insert(0, {"Time": datetime.now().strftime("%d %b %H:%M"), "Type": kind, "To": to, "Message": text})


def flash(text, icon="✅"):
    """Shows a toast notification after the page refreshes."""
    S.flash = {"body": text, "icon": icon}


def get_cand(cand_id):
    return S.cands[S.cands["cand_id"] == cand_id].iloc[0]


def candidate_department(cand_id):
    job_id = get_cand(cand_id)["job_id"]
    return S.jobs.set_index("job_id").loc[job_id, "department"]


def is_allowed(cand_id, permission):
    """Checks the permission and, for Department Heads, the department."""
    if not can(permission):
        flash("Permission denied for your role.", "🚫")
        return False
    if S.user["role"] == "Department Head" and candidate_department(cand_id) != S.user["department"]:
        flash("This candidate belongs to another department.", "🚫")
        return False
    return True


def move_candidate(cand_id, new_status, permission, text, to=None, kind="Candidate", message="", **fields):
    """Single place where a candidate changes status."""
    if not is_allowed(cand_id, permission):
        return
    mask = S.cands["cand_id"] == cand_id
    S.cands.loc[mask, "status"] = new_status
    for column, value in fields.items():
        S.cands.loc[mask, column] = value
    if to:
        send_message(kind, to, message)
    log_audit(f"{text} (candidate #{cand_id})")
    flash(text)


# --- Specific actions (used as button callbacks) ---------------------------
def shortlist(cand_id):
    move_candidate(cand_id, "Shortlisted", "shortlist", "Candidate shortlisted",
                   to=get_cand(cand_id)["name"], message="Congratulations! You have been shortlisted.")


def shortlist_many(cand_ids):
    for cid in cand_ids:
        shortlist(cid)


def reject(cand_id, reason):
    move_candidate(cand_id, "Rejected", "reject", "Candidate rejected - notification sent",
                   to=get_cand(cand_id)["name"],
                   message=f"We regret to inform you that your application was not successful. Reason: {reason}.")


def forward_to_department(cand_id):
    dept = candidate_department(cand_id)
    move_candidate(cand_id, "Sent to Department", "forward_to_department", f"Forwarded to {dept} department",
                   to=f"{dept} Department Head", kind="Department",
                   message=f"{get_cand(cand_id)['name']} is ready for your review.")


def department_approve(cand_id):
    interview_date = S.get(f"date_{cand_id}", TODAY + timedelta(days=3))
    move_candidate(cand_id, "Interview", "dept_decision", "Approved - interview scheduled",
                   to=get_cand(cand_id)["name"], message=f"Your interview is scheduled for {interview_date}.",
                   interview_date=interview_date)


def department_decline(cand_id):
    reason = S.get(f"reason_{cand_id}", "Skills do not match")
    move_candidate(cand_id, "Rejected", "dept_decision", "Declined by department - candidate notified",
                   to=get_cand(cand_id)["name"],
                   message=f"We regret to inform you that your application was not successful. Reason: {reason}.")


def make_offer(cand_id):
    move_candidate(cand_id, "Offer", "make_offer", "Offer sent",
                   to=get_cand(cand_id)["name"], message="We are pleased to offer you the position.")


def hire(cand_id):
    move_candidate(cand_id, "Hired", "hire", "Candidate hired",
                   to=get_cand(cand_id)["name"], message="Welcome to the team!")


def create_job(title, dept, skills, min_exp, salary):
    if not can("manage_jobs"):
        flash("Permission denied for your role.", "🚫")
        return
    S.jobs.loc[len(S.jobs)] = [int(S.jobs["job_id"].max()) + 1, title, dept, ",".join(skills), min_exp, salary, "Open"]
    log_audit(f"Created job '{title}'")
    flash("Job opening created")


# ===========================================================================
# 6. STYLING AND UI HELPERS
# ===========================================================================
CSS = """
<style>
/* Page spacing */
.block-container {padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1280px;}

/* Page title */
.page-title {font-size: 2rem; font-weight: 700; margin-bottom: 0.1rem;}
.page-sub {opacity: .65; margin-bottom: 1.6rem;}

/* KPI cards */
.kpi {border-radius: 14px; padding: 18px 20px; border: 1px solid rgba(120,130,160,.25);
      border-left: 5px solid var(--c); background: rgba(120,130,160,.06);}
.kpi .label {font-size: .85rem; opacity: .7;}
.kpi .value {font-size: 2rem; font-weight: 700; line-height: 1.2;}
.kpi .note  {font-size: .75rem; opacity: .55;}

/* Buttons: rounded, lift on hover, press on click */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
    border-radius: 10px; font-weight: 600; padding: .55rem 1.2rem;
    border: 1px solid rgba(120,130,160,.35);
    transition: transform .15s ease, box-shadow .15s ease, background .2s ease, border-color .2s ease;}
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-2px); box-shadow: 0 8px 18px rgba(37,99,235,.25); border-color: #2563eb;}
.stButton > button:active, [data-testid="stFormSubmitButton"] > button:active {
    transform: translateY(0) scale(.97); box-shadow: none;}
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"],
[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg, #2563eb, #7c3aed); color: #fff; border: none;}

/* Cards (bordered containers) */
[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 14px;}

/* User card in the sidebar */
.usercard {display: flex; gap: 12px; align-items: center; padding: 12px; border-radius: 12px;
           border: 1px solid rgba(120,130,160,.25); margin-bottom: 10px;}
.usercard .avatar {width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg,#2563eb,#7c3aed);
                   color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700;}
.usercard .role {font-size: .75rem; opacity: .65;}
</style>
"""


def page_header(title, subtitle):
    st.markdown(f"<div class='page-title'>{title}</div><div class='page-sub'>{subtitle}</div>", unsafe_allow_html=True)


def kpi_card(label, value, note, color):
    return (f"<div class='kpi' style='--c:{color}'><div class='label'>{label}</div>"
            f"<div class='value'>{value}</div><div class='note'>{note}</div></div>")


def show_table(df, columns):
    """Shows a table with friendly column names, progress bar for match and PKR for salary."""
    config = {}
    if "match" in columns:
        config["Match %"] = st.column_config.ProgressColumn("Match %", min_value=0, max_value=100, format="%d%%")
    for col in ("expected_salary", "ai_salary"):
        if col in columns:
            config[COLUMN_LABELS[col]] = st.column_config.NumberColumn(COLUMN_LABELS[col], format="PKR %d")
    st.dataframe(df[columns].rename(columns=COLUMN_LABELS), hide_index=True, column_config=config)


def no_permission_note(text="Your role does not have permission for this action."):
    st.caption(f"🔒 {text}")


# ===========================================================================
# 7. LOGIN SCREEN
# ===========================================================================
def authenticate(username, password):
    """BACKEND: replace with Microsoft Entra ID (Azure AD) authentication."""
    user = USERS.get(username.strip().lower())
    if user and user["password"] == hash_password(password):
        return {"username": username.strip().lower(), **{k: v for k, v in user.items() if k != "password"}}
    return None


def login_screen():
    st.markdown(CSS, unsafe_allow_html=True)
    _, middle, _ = st.columns([1, 1.3, 1])
    with middle:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div class='page-title'>👥 Recruitment Suite</div>"
                    "<div class='page-sub'>Sign in to continue</div>", unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", type="primary")
            if submitted:
                user = authenticate(username, password)
                if user:
                    S.user = user
                    log_audit("Signed in")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        with st.expander("Demo accounts"):
            st.dataframe(pd.DataFrame([{"Username": u, "Password": DEMO_PASSWORDS[u], "Role": v["role"]}
                                       for u, v in USERS.items()]), hide_index=True)


def logout():
    log_audit("Signed out")
    S.user = None


# ===========================================================================
# 8. PAGE: DASHBOARD
# ===========================================================================
def page_dashboard():
    page_header("Dashboard", "Overview of the recruitment process")
    df = cands_with_details()

    # KPI cards
    in_review = int(df["status"].isin(["Shortlisted", "Sent to Department"]).sum())
    cards = [
        ("Total CVs", len(df), "All applications", "#3b82f6"),
        ("New CVs", int((df["cv_type"] == "New").sum()), f"Last {NEW_CV_DAYS} days", "#22c55e"),
        ("In Review", in_review, "Shortlisted or with department", "#8b5cf6"),
        ("Interviews", int((df["status"] == "Interview").sum()), "Scheduled", "#f97316"),
        ("Hired", int((df["status"] == "Hired").sum()), "Joined or joining", "#06b6d4"),
    ]
    for col, card in zip(st.columns(5), cards):
        col.markdown(kpi_card(*card), unsafe_allow_html=True)
    st.write("")
    st.write("")

    # Charts
    left, right = st.columns([1.4, 1])
    with left:
        with st.container(border=True):
            st.subheader("Recruitment funnel")
            st.bar_chart(df["status"].value_counts().reindex(STATUSES).fillna(0))
    with right:
        with st.container(border=True):
            st.subheader("New vs Existing CVs")
            st.bar_chart(df["cv_type"].value_counts())
    st.write("")

    # AI recommendations and recent activity
    left, right = st.columns([1.4, 1])
    with left:
        with st.container(border=True):
            st.subheader("Top AI recommendations")
            best = df[df["status"] == "Applied"].sort_values("match", ascending=False).head(5)
            if best.empty:
                st.info("No new applications to recommend.")
            else:
                show_table(best, ["name", "position", "experience", "expected_salary", "ai_salary", "match"])
    with right:
        with st.container(border=True):
            st.subheader("Recent activity")
            for m in S.messages[:5]:
                st.markdown(f"**{m['To']}**  \n{m['Message']}  \n<small style='opacity:.6'>{m['Time']}</small>",
                            unsafe_allow_html=True)
                st.divider()


# ===========================================================================
# 9. PAGE: JOB OPENINGS
# ===========================================================================
def page_jobs():
    page_header("Job Openings", "Create and track open positions")
    df = cands_with_details()

    # New job form (only for roles that can manage jobs)
    if can("manage_jobs"):
        with st.expander("➕ Create new job opening"):
            with st.form("job_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                title = c1.text_input("Job title")
                dept = c2.selectbox("Department", DEPARTMENTS)
                skills = st.multiselect("Required skills", SKILLS)
                c3, c4 = st.columns(2)
                min_exp = c3.number_input("Minimum experience (years)", 0, 20, 2)
                salary = c4.number_input("Maximum salary (PKR)", 0, 1000000, 100000, 5000)
                if st.form_submit_button("Create job", type="primary"):
                    if title and skills:
                        create_job(title, dept, skills, min_exp, salary)
                        st.rerun()
                    else:
                        st.error("Job title and at least one skill are required.")
    else:
        no_permission_note("Your role can view jobs but cannot create them.")

    # Jobs table
    jobs = S.jobs.copy()
    jobs["applicants"] = jobs["title"].map(df["position"].value_counts()).fillna(0).astype(int)
    st.dataframe(jobs.rename(columns={"job_id": "ID", "title": "Position", "department": "Department", "skills": "Required Skills",
                                      "min_exp": "Min Experience", "salary_max": "Max Salary (PKR)", "status": "Status",
                                      "applicants": "Applicants"}), hide_index=True)


# ===========================================================================
# 10. PAGE: CVs AND AI SUGGESTIONS
# ===========================================================================
def page_cvs():
    page_header("CVs & AI Suggestions", "Filter CVs and let AI recommend the best matches")
    df = cands_with_details()

    # Filters
    with st.container(border=True):
        c = st.columns(4)
        job_filter = c[0].selectbox("Job", ["All"] + list(S.jobs["title"]))
        type_filter = c[1].radio("CV type", ["All", "New", "Existing"], horizontal=True)
        skill_filter = c[2].multiselect("Skills (subject)", SKILLS)
        dates = c[3].date_input("Applied between", (TODAY - timedelta(days=60), TODAY))
    if job_filter != "All":
        df = df[df["position"] == job_filter]
    if type_filter != "All":
        df = df[df["cv_type"] == type_filter]
    for skill in skill_filter:
        df = df[df["skills"].str.contains(skill)]
    if len(dates) == 2:
        df = df[(df["applied_on"] >= dates[0]) & (df["applied_on"] <= dates[1])]
    df = df.sort_values("match", ascending=False)
    st.write("")

    # AI recommended CVs
    with st.container(border=True):
        st.subheader("🤖 AI recommended CVs")
        best = df[df["status"] == "Applied"].head(5)
        if best.empty:
            st.info("No new applications match these filters.")
        else:
            show_table(best, ["name", "position", "experience", "skills", "expected_salary", "ai_salary", "match"])
            st.button("⭐ Shortlist these 5", type="primary", disabled=not can("shortlist"),
                      on_click=shortlist_many, args=(list(best["cand_id"]),))
            if not can("shortlist"):
                no_permission_note()
    st.write("")

    # All CVs
    st.subheader(f"All CVs ({len(df)})")
    columns = ["cand_id", "name", "position", "cv_type", "applied_on", "experience", "expected_salary", "ai_salary", "match", "status"]
    show_table(df, columns)
    st.download_button("⬇ Download as CSV", df[columns].rename(columns=COLUMN_LABELS).to_csv(index=False), "cvs.csv")


# ===========================================================================
# 11. PAGE: CANDIDATE PIPELINE
# ===========================================================================
def page_pipeline():
    page_header("Candidate Pipeline", "Move candidates step by step through the hiring process")
    df = cands_with_details()

    # Step selector with counts
    counts = df["status"].value_counts()
    step = st.radio("Step", STATUSES, horizontal=True, format_func=lambda s: f"{s} ({int(counts.get(s, 0))})")
    sub = df[df["status"] == step].sort_values("match", ascending=False)
    show_table(sub.head(30), ["cand_id", "name", "position", "experience", "expected_salary", "ai_salary", "match"])
    if sub.empty:
        st.info("No candidates in this step.")
        return

    # Candidate action panel
    st.write("")
    with st.container(border=True):
        st.subheader("Actions")
        cand_id = st.selectbox("Select candidate", list(sub["cand_id"]),
                               format_func=lambda i: f"{sub[sub['cand_id'] == i]['name'].iloc[0]}  ·  {sub[sub['cand_id'] == i]['match'].iloc[0]}% match")
        if step == "Applied":
            c1, c2 = st.columns(2)
            c1.button("⭐ Shortlist", type="primary", disabled=not can("shortlist"), on_click=shortlist, args=(cand_id,))
            reason = c2.selectbox("Rejection reason", REJECT_REASONS, key="pipeline_reason")
            c2.button("✖ Reject and notify candidate", disabled=not can("reject"), on_click=reject, args=(cand_id, reason))
        elif step == "Shortlisted":
            st.button("📤 Forward to department", type="primary", disabled=not can("forward_to_department"),
                      on_click=forward_to_department, args=(cand_id,))
        elif step == "Sent to Department":
            st.info("Waiting for the department head's decision. Use the Department Review page.")
        elif step == "Interview":
            reason = st.selectbox("Rejection reason", REJECT_REASONS, key="pipeline_reason_i")
            c1, c2 = st.columns(2)
            c1.button("💼 Send offer", type="primary", disabled=not can("make_offer"), on_click=make_offer, args=(cand_id,))
            c2.button("✖ Reject", disabled=not can("reject"), on_click=reject, args=(cand_id, reason))
        elif step == "Offer":
            c1, c2 = st.columns(2)
            c1.button("✅ Offer accepted - Hire", type="primary", disabled=not can("hire"), on_click=hire, args=(cand_id,))
            c2.button("✖ Offer declined", disabled=not can("hire"), on_click=reject, args=(cand_id, "Offer declined by candidate"))
        else:
            st.info("No further actions for this step.")


# ===========================================================================
# 12. PAGE: DEPARTMENT REVIEW
# ===========================================================================
def page_department():
    page_header("Department Review", "Review candidates forwarded by HR and approve or decline")
    df = cands_with_details()
    waiting = df[df["status"] == "Sent to Department"].sort_values("match", ascending=False)
    if waiting.empty:
        st.success("No candidates are waiting for review.")
        return
    st.write(f"**{len(waiting)}** candidate(s) waiting for your decision")
    for _, c in waiting.head(10).iterrows():
        cid = c["cand_id"]
        with st.container(border=True):
            info, action = st.columns([1.6, 1.4])
            info.markdown(f"#### {c['name']}")
            info.caption(f"{c['position']} · {c['department']} · {c['experience']} years experience")
            info.markdown(f"**{c['match']}% match**  ·  Expected PKR {c['expected_salary']:,}  ·  AI estimate PKR {c['ai_salary']:,}")
            info.caption(f"Skills: {c['skills'].replace(',', ', ')}")
            action.date_input("Interview date", TODAY + timedelta(days=3), key=f"date_{cid}")
            action.selectbox("Decline reason", REJECT_REASONS, key=f"reason_{cid}")
            b1, b2 = action.columns(2)
            b1.button("✔ Approve", key=f"approve_{cid}", type="primary", on_click=department_approve, args=(cid,))
            b2.button("✖ Decline", key=f"decline_{cid}", on_click=department_decline, args=(cid,))


# ===========================================================================
# 13. PAGE: MESSAGES
# ===========================================================================
def page_messages():
    page_header("Messages", "Notifications sent to candidates and departments")
    messages = pd.DataFrame(S.messages)
    if S.user["role"] == "Department Head":
        messages = messages[messages["To"].str.contains(S.user["department"])]
    kind = st.radio("Show", ["All", "Candidate", "Department"], horizontal=True)
    if kind != "All":
        messages = messages[messages["Type"] == kind]
    if messages.empty:
        st.info("No messages yet.")
    else:
        st.dataframe(messages, hide_index=True)


# ===========================================================================
# 14. PAGE: ACCESS CONTROL (Admin only)
# ===========================================================================
def page_access():
    page_header("Access Control", "Users, roles, permissions and audit log")
    users_tab, roles_tab, audit_tab = st.tabs(["Users", "Role permissions", "Audit log"])

    with users_tab:
        st.dataframe(pd.DataFrame([{"Username": u, "Name": v["name"], "Role": v["role"], "Department": v["department"] or "All"}
                                   for u, v in USERS.items()]), hide_index=True)

    with roles_tab:
        matrix = pd.DataFrame({role: ["✔" if p in perms else "" for p in ALL_PERMISSIONS]
                               for role, perms in ROLE_PERMISSIONS.items()},
                              index=[p.replace("_", " ").title() for p in ALL_PERMISSIONS])
        st.dataframe(matrix)

    with audit_tab:
        if S.audit:
            st.dataframe(pd.DataFrame(S.audit), hide_index=True)
        else:
            st.info("No activity recorded yet.")


# ===========================================================================
# 15. NAVIGATION AND APP START
# ===========================================================================
# (menu title, function, icon, required permission, section, url)
PAGES = [
    ("Dashboard", page_dashboard, ":material/dashboard:", "view_dashboard", "Overview", "dashboard"),
    ("Job Openings", page_jobs, ":material/work:", "view_jobs", "Recruitment", "jobs"),
    ("CVs & AI Suggestions", page_cvs, ":material/auto_awesome:", "view_cvs", "Recruitment", "cvs"),
    ("Candidate Pipeline", page_pipeline, ":material/view_kanban:", "view_pipeline", "Recruitment", "pipeline"),
    ("Department Review", page_department, ":material/account_tree:", "dept_decision", "Recruitment", "department"),
    ("Messages", page_messages, ":material/mail:", "view_messages", "Communication", "messages"),
    ("Access Control", page_access, ":material/admin_panel_settings:", "manage_users", "Administration", "access"),
]


def sidebar_user_card():
    initials = "".join(w[0] for w in S.user["name"].split()[:2]).upper()
    st.markdown(f"<div class='usercard'><div class='avatar'>{initials}</div><div><b>{S.user['name']}</b>"
                f"<div class='role'>{S.user['role']}{' · ' + S.user['department'] if S.user['department'] else ''}</div></div></div>",
                unsafe_allow_html=True)
    st.button("Sign out", on_click=logout)


def main():
    load_data()
    if not S.get("user"):
        login_screen()
        return
    st.markdown(CSS, unsafe_allow_html=True)

    # Build the menu: only pages the role is allowed to see (RBAC)
    sections = {}
    for title, func, icon, permission, section, url in PAGES:
        if can(permission):
            sections.setdefault(section, []).append(st.Page(func, title=title, icon=icon, url_path=url, default=(url == "dashboard")))
    navigation = st.navigation(sections)

    with st.sidebar:
        st.divider()
        sidebar_user_card()

    # Show the toast from the last action
    if S.get("flash"):
        st.toast(S.flash["body"], icon=S.flash["icon"])
        S.flash = None
    navigation.run()


main()