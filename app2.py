"""
XLOOP - Complete Recruitment Suite  (app.py)
People & Culture Department

Run:
    pip install -r requirements.txt
    streamlit run app.py

FRONTEND + SIMULATED ENGINE. Sab data st.session_state mein hai (5000 demo CVs).
Backend baad mein in jaghon par lagega (search "BACKEND HOOK"):
    persist()        -> Azure SQL / Cosmos DB
    publish_event()  -> Azure Service Bus / Event Grid / Logic Apps / Functions
    send_mail()      -> Azure Communication Services (Email)
    score_vec()      -> Azure OpenAI / AI Foundry Agent (re-ranking, summaries)
    parse_cv()       -> Azure AI Document Intelligence + Blob Storage
    generate_ad()    -> Azure OpenAI (job ad writer)
Integrations page par poora mapping, event catalogue, SQL DDL aur agent contract maujood hai.
"""
import io
import os
import re
import json
import random
import time
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Xloop | Recruitment Suite", page_icon="♾️", layout="wide",
                   initial_sidebar_state="expanded")
S = st.session_state
TODAY = date.today()


# =============================================================================
# CONFIG (Azure keys: .streamlit/secrets.toml ya environment variables)
# =============================================================================
def cfg(key, default=""):
    v = None
    try:
        v = st.secrets.get(key)
    except Exception:
        v = None
    return str(v) if v else os.environ.get(key, default)


AZURE_SERVICES = {
    "Azure OpenAI / AI Foundry (AI agent)": ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_DEPLOYMENT"],
    "Azure SQL / Cosmos DB (database)": ["AZURE_SQL_CONNECTION_STRING"],
    "Azure Blob Storage (CV files)": ["AZURE_BLOB_CONNECTION_STRING", "AZURE_BLOB_CONTAINER"],
    "Azure Communication Services (email/SMS)": ["AZURE_COMM_CONNECTION_STRING", "AZURE_COMM_SENDER"],
    "Azure Document Intelligence (CV parsing)": ["AZURE_DOCINT_ENDPOINT", "AZURE_DOCINT_KEY"],
    "Azure Service Bus / Event Grid (automation)": ["AZURE_SERVICEBUS_CONNECTION_STRING", "AZURE_EVENTGRID_ENDPOINT"],
    "Microsoft Entra ID (login / roles)": ["AZURE_TENANT_ID", "AZURE_CLIENT_ID"],
}

# =============================================================================
# CONSTANTS
# =============================================================================
DEPTS = ["IT", "Finance", "HR", "Marketing", "Sales", "Operations"]
DEPT_SKILLS = {
    "IT": ["Python", "JavaScript", "React", "Node.js", "Django", "SQL", "Java", "AWS", "Docker", "Git",
           "HTML", "CSS", "Machine Learning", "TypeScript", "Flutter"],
    "Finance": ["Excel", "Accounting", "Taxation", "Power BI", "Auditing", "SAP", "Financial Modeling", "SQL", "Budgeting"],
    "HR": ["Recruitment", "Communication", "Payroll", "Labor Law", "Training", "HRIS", "Excel"],
    "Marketing": ["SEO", "Social Media", "Content Writing", "Figma", "UI/UX", "Google Ads", "Photoshop", "Copywriting"],
    "Sales": ["Sales", "CRM", "Negotiation", "Communication", "Lead Generation", "Excel"],
    "Operations": ["Supply Chain", "Logistics", "Excel", "Procurement", "Inventory", "SAP"],
}
SKILLS = sorted({s for v in DEPT_SKILLS.values() for s in v})
SK_IDX = {s: i for i, s in enumerate(SKILLS)}
TITLES = {
    "IT": ["Software Engineer", "Backend Developer", "Frontend Developer", "Data Engineer", "QA Engineer", "DevOps Engineer"],
    "Finance": ["Accountant", "Financial Analyst", "Data Analyst", "Auditor", "Finance Officer"],
    "HR": ["HR Executive", "Recruiter", "HR Associate", "Payroll Officer"],
    "Marketing": ["Digital Marketer", "UI/UX Designer", "Content Writer", "SEO Specialist", "Graphic Designer"],
    "Sales": ["Sales Executive", "Account Manager", "Business Developer", "Sales Officer"],
    "Operations": ["Supply Chain Officer", "Logistics Coordinator", "Procurement Officer", "Operations Executive"],
}
DEPT_HEADS = {
    "IT": ("Imran Qureshi", "imran.qureshi@xloop.com"), "Finance": ("Nida Farooq", "nida.farooq@xloop.com"),
    "HR": ("Sadam Ahmed", "sadam.ahmed@xloop.com"), "Marketing": ("Ayesha Khan", "ayesha.khan@xloop.com"),
    "Sales": ("Bilal Ahmed", "bilal.ahmed@xloop.com"), "Operations": ("Hamza Raza", "hamza.raza@xloop.com"),
}
CITIES = ["Karachi", "Lahore", "Islamabad", "Hyderabad", "Sukkur", "Larkana", "Multan", "Faisalabad", "Peshawar"]
CITY_MULT = {"Karachi": 1.08, "Lahore": 1.08, "Islamabad": 1.12}
SAL_BASE = dict(IT=70000, Finance=55000, HR=48000, Marketing=52000, Sales=48000, Operations=50000)
EDU = {1: "Matric", 2: "Intermediate", 3: "Bachelors", 4: "Masters", 5: "PhD"}
STAGES = ["Applied", "Talent Pool", "Shortlisted", "Dept Review", "Interview", "Offer", "Hired", "Rejected", "On Hold"]
ADV_STAGES = ["Shortlisted", "Dept Review", "Interview", "Offer", "Hired"]
CHANNELS = ["Rozee.pk", "LinkedIn", "Company Website", "Mustakbil", "Indeed", "Facebook"]
SOURCES = CHANNELS + ["Referral", "Walk-in"]
PANEL = ["Sadam Ahmed", "Ayesha Khan", "Imran Qureshi", "Nida Farooq", "Bilal Ahmed", "Hamza Raza"]
ROUNDS = ["HR Screening", "Technical", "Managerial", "Final"]
REJECT_REASONS = ["Skills mismatch", "Experience below requirement", "Salary expectation too high", "Position filled",
                  "Better-matched candidate", "Not responsive", "Other"]
FIRST = ["Ayesha", "Hassan", "Zain", "Sana", "Bilal", "Fatima", "Usman", "Hina", "Ahmed", "Mariam", "Kamran", "Rabia",
         "Ali", "Noor", "Hamza", "Iqra", "Saad", "Maham", "Faisal", "Zara", "Omar", "Laiba", "Danish", "Aiman", "Asad", "Sidra"]
LAST = ["Malik", "Shah", "Raza", "Khan", "Siddiqui", "Noor", "Ali", "Tariq", "Javed", "Aslam", "Memon", "Chandio",
        "Soomro", "Qureshi", "Ansari", "Baloch", "Mirza", "Sheikh", "Butt", "Abbasi"]
ONBOARD_TASKS = ["Offer letter signed", "CNIC & documents collected", "Employee record created",
                 "Laptop & accounts provisioned", "Email & system access", "Orientation scheduled",
                 "Payroll registration", "Probation plan shared"]
DEFAULT_WEIGHTS = dict(skills=45, exp=25, edu=10, salary=10, loc=10)
DEFAULT_KW = dict(date="", time="", mode="", panel="", salary="", joining="", link="", feedback_line="",
                  dept="", count="", candidates="")

DEFAULT_TEMPLATES = {
    "Application received": ("We received your application for {job}",
        "Dear {name},\n\nThank you for applying for {job} at {company}. Our team is reviewing your profile and "
        "we will update you shortly.\n\nRegards,\nPeople & Culture, {company}"),
    "Shortlisted": ("You have been shortlisted for {job}",
        "Dear {name},\n\nGood news! Your profile has been shortlisted for {job}. Our hiring team will contact you "
        "soon with the next steps.\n\nRegards,\nPeople & Culture, {company}"),
    "Interview invitation": ("Interview invitation - {job}",
        "Dear {name},\n\nYou are invited for an interview for {job}.\nDate: {date}\nTime: {time}\nMode: {mode}\n"
        "{link}\nPanel: {panel}\n\nPlease confirm your availability.\n\nRegards,\nPeople & Culture, {company}"),
    "Interview reminder": ("Reminder: interview for {job}",
        "Dear {name},\n\nThis is a reminder for your interview for {job} on {date} at {time} ({mode}).\n{link}\n\n"
        "Regards,\nPeople & Culture, {company}"),
    "Regret / rejection": ("Update on your application - {job}",
        "Dear {name},\n\nThank you for your interest in {company}. After careful review we will not be moving "
        "forward with your application for {job}.{feedback_line}\nWe will keep your CV for future openings.\n\n"
        "Best wishes,\nPeople & Culture, {company}"),
    "Job offer": ("Job offer - {job}",
        "Dear {name},\n\nWe are delighted to offer you the position of {job} at {company}. Please find your offer "
        "letter attached (monthly salary PKR {salary}, joining {joining}).\n\nRegards,\nPeople & Culture, {company}"),
    "Offer follow-up": ("Following up on your offer - {job}",
        "Dear {name},\n\nWe wanted to follow up on the offer sent for {job}. Please let us know if you have any "
        "questions.\n\nRegards,\nPeople & Culture, {company}"),
    "Welcome onboard": ("Welcome to {company}!",
        "Dear {name},\n\nWelcome to {company}! We are excited to have you join as {job}. Your onboarding "
        "checklist will be shared shortly.\n\nRegards,\nPeople & Culture, {company}"),
    "Invite to apply": ("A new opportunity at {company}: {job}",
        "Dear {name},\n\nYour profile in our talent pool matches our opening for {job}. We would love to "
        "talk to you.\n\nRegards,\nPeople & Culture, {company}"),
    "Dept forward": ("Candidates forwarded for review: {job} ({count})",
        "Dear {name},\n\nHR has shortlisted {count} candidate(s) for {job} ({dept}). Top profiles:\n{candidates}\n\n"
        "Please open Xloop > Department Handoff to approve or decline.\n\nRegards,\nPeople & Culture, {company}"),
}
INTERNAL_TEMPLATES = ["Dept forward"]


class SD(dict):
    def __missing__(self, k):
        return "{" + k + "}"


def render(t, **kw):
    return t.format_map(SD(**kw))


def nowstr():
    return datetime.now().strftime("%d %b %H:%M")


def pct(x):
    return "n/a" if pd.isna(x) else f"{x:.0f}%"


def sal_range(ai):
    return f"PKR {ai * 0.92 / 1000:,.0f}K - {ai * 1.08 / 1000:,.0f}K"


# =============================================================================
# DATA GENERATION + SALARY ESTIMATE
# BACKEND HOOK: replace generate_cvs() with database / job-portal APIs
# =============================================================================
def est_salary_df(df):
    """AI market salary estimate (rule-based). BACKEND HOOK: Azure OpenAI / salary benchmark API."""
    base = df["dept"].map(SAL_BASE).values
    cm = df["city"].map(CITY_MULT).fillna(1.0).values
    em = 1 + (df["edu"].values - 3) * 0.06
    v = (base + df["exp"].values * 8500) * em * cm
    return (np.round(v / 1000) * 1000).astype(int)


def generate_cvs(n, start_id, seed, max_age=90, bias=1.6, jobs_by_dept=None, fresh=False):
    r = random.Random(seed)
    rows, seen = [], []
    for k in range(n):
        cid = start_id + k
        dept = r.choices(DEPTS, [34, 16, 10, 14, 14, 12])[0]
        pool = DEPT_SKILLS[dept]
        sk = set(r.sample(pool, r.randint(3, min(8, len(pool)))))
        if r.random() < 0.25:
            sk.add(r.choice(SKILLS))
        exp = round(min(r.gammavariate(2.0, 2.2), 25), 1)
        edu = r.choices([1, 2, 3, 4, 5], [3, 10, 55, 28, 4])[0]
        fn, ln = r.choice(FIRST), r.choice(LAST)
        email = r.choice(seen[-400:]) if (seen and r.random() < 0.015) else f"{fn}.{ln}{cid}@mail.com".lower()
        seen.append(email)
        lvl = "Senior " if exp >= 6 else ("Junior " if exp < 2 else "")
        age = 0 if fresh else int(max_age * (r.random() ** bias))
        jids = (jobs_by_dept or {}).get(dept, [])
        pooled = (not jids) or r.random() < 0.12
        rows.append(dict(
            id=cid, name=f"{fn} {ln}", email=email, phone="03" + "".join(r.choice("0123456789") for _ in range(9)),
            city=r.choice(CITIES), title=lvl + r.choice(TITLES[dept]), dept=dept, exp=exp, edu=edu, salary=0,
            skills="|".join(sorted(sk)), source=r.choice(SOURCES),
            applied=pd.Timestamp(TODAY - timedelta(days=age)),
            stage="Talent Pool" if pooled else "Applied", job_id=0 if pooled else r.choice(jids),
            score=np.nan, acked=age > 10 or pooled, tags="", notes=""))
    df = pd.DataFrame(rows).set_index("id")
    df["ai_salary"] = est_salary_df(df)
    rng = np.random.default_rng(seed)
    df["salary"] = (np.round(df["ai_salary"].values * rng.uniform(0.85, 1.3, len(df)) / 1000) * 1000).astype(int)
    return df


def default_jobs():
    def J(i, title, dept, must, nice, mn, mx, edu, smin, smax, loc, hc, status, dl):
        return dict(id=i, title=title, dept=dept, must=must, nice=nice, min_exp=mn, max_exp=mx, edu_min=edu,
                    sal_min=smin, sal_max=smax, location=loc, headcount=hc, status=status,
                    deadline=TODAY + timedelta(days=dl), manager=DEPT_HEADS[dept][0], created=TODAY - timedelta(days=20),
                    weights=dict(DEFAULT_WEIGHTS), min_must=0.6)
    return [
        J(1, "Senior Python Developer", "IT", ["Python", "Django", "SQL"], ["Docker", "AWS", "Git"], 4, 10, 3, 140000, 220000, "Karachi", 2, "Open", 14),
        J(2, "Frontend Developer", "IT", ["JavaScript", "React", "HTML", "CSS"], ["TypeScript", "Git"], 2, 6, 3, 90000, 150000, "Remote", 2, "Open", 20),
        J(3, "Data Analyst", "Finance", ["Excel", "SQL", "Power BI"], ["Financial Modeling"], 2, 6, 3, 90000, 140000, "Lahore", 1, "Open", 3),
        J(4, "Accountant", "Finance", ["Accounting", "Taxation", "Excel"], ["SAP", "Auditing"], 2, 8, 3, 70000, 110000, "Karachi", 2, "Open", 25),
        J(5, "HR Executive", "HR", ["Recruitment", "Communication", "HRIS"], ["Payroll", "Labor Law"], 2, 6, 3, 70000, 100000, "Karachi", 1, "Open", 18),
        J(6, "Digital Marketing Specialist", "Marketing", ["SEO", "Social Media", "Google Ads"], ["Content Writing"], 2, 7, 3, 80000, 120000, "Islamabad", 1, "Open", 12),
        J(7, "Sales Executive", "Sales", ["Sales", "CRM", "Negotiation"], ["Lead Generation"], 1, 6, 3, 60000, 100000, "Lahore", 3, "Open", 30),
        J(8, "Supply Chain Officer", "Operations", ["Supply Chain", "Logistics", "Procurement"], ["SAP", "Inventory"], 2, 8, 3, 75000, 115000, "Hyderabad", 1, "Pending Approval", 28),
        J(9, "Machine Learning Engineer", "IT", ["Python", "Machine Learning", "SQL"], ["AWS", "Docker"], 3, 8, 4, 200000, 320000, "Remote", 1, "Draft", 40),
    ]


def get_job(jid):
    return next((j for j in S.jobs if j["id"] == jid), None)


def rebuild_matrix():
    sk = S.df["skills"]
    S.M = np.column_stack([sk.str.contains(rf"(?:^|\|){re.escape(s)}(?:\||$)", regex=True).values for s in SKILLS]).astype(np.float32)


def new_mask(df):
    return (df["applied"] >= pd.Timestamp(TODAY - timedelta(days=int(S.settings["new_days"])))).values


# =============================================================================
# JOB ADS
# =============================================================================
def generate_ad(job):
    """BACKEND HOOK: Azure OpenAI job-ad writer. Abhi template-based."""
    head = f"We are hiring: {job['title']} ({job['dept']}) - {job['location']}"
    body = (f"**{S.settings['company']}** is looking for a {job['title']} to join our {job['dept']} team in {job['location']}.\n\n"
            f"**What you will do**\n- Own day-to-day work in {job['dept']} and collaborate with cross-functional teams\n"
            f"- Use {', '.join(job['must'][:3])} to deliver high-quality results\n- Share knowledge and improve processes\n\n"
            f"**What we are looking for**\n- {job['min_exp']:g}+ years of relevant experience\n"
            f"- Must-have skills: {', '.join(job['must'])}\n" + (f"- Nice to have: {', '.join(job['nice'])}\n" if job["nice"] else "") +
            f"- {EDU[job['edu_min']]} degree or equivalent\n\n"
            f"**What we offer**\n- Competitive salary and benefits\n- Learning budget, health cover and a friendly culture\n\n"
            f"**Openings:** {job['headcount']}  |  **Apply before:** {job['deadline']:%d %b %Y}\n"
            f"Apply now at careers.xloop.com")
    return head, body


def create_ad(job, status="Draft", channels=None):
    head, body = generate_ad(job)
    ad = dict(id=max([a["id"] for a in S.ads], default=0) + 1, job_id=job["id"],
              channels=channels or ["Company Website", "LinkedIn", "Rozee.pk"], headline=head, body=body, status=status,
              posted_on=TODAY if status == "Live" else None, expires=job["deadline"], views={}, boosted=False)
    if status == "Live":
        seed_views(ad)
    S.ads.append(ad)
    return ad


def seed_views(ad, rnd=None):
    rnd = rnd or random
    for ch in ad["channels"]:
        ad["views"].setdefault(ch, rnd.randint(900, 6500))


def ad_for_job(jid):
    return next((a for a in S.ads if a["job_id"] == jid and a["status"] != "Closed"), None)


def ad_stats(ad):
    sub = S.df[S.df["job_id"] == ad["job_id"]]
    rows = []
    for ch in ad["channels"]:
        v = ad["views"].get(ch, 0)
        apps = int((sub["source"] == ch).sum())
        sh = int(((sub["source"] == ch) & sub["stage"].isin(ADV_STAGES)).sum())
        rows.append({"Channel": ch, "Views": v, "Applications": apps, "Shortlisted": sh,
                     "View > Apply %": round(apps / v * 100, 1) if v else 0.0})
    return pd.DataFrame(rows)


# =============================================================================
# AI MATCHING ENGINE (vectorised - 5000 CVs in milliseconds)
# BACKEND HOOK: Azure OpenAI / AI Foundry agent can re-rank the top N returned here
# =============================================================================
def score_vec(job, w=None):
    df, M = S.df, S.M
    w = w or job["weights"]
    must = [SK_IDX[s] for s in job["must"] if s in SK_IDX]
    nice = [SK_IDX[s] for s in job["nice"] if s in SK_IDX]
    must_cov = M[:, must].mean(axis=1) if must else np.ones(len(df))
    nice_cov = M[:, nice].mean(axis=1) if nice else must_cov
    sk = 0.75 * must_cov + 0.25 * nice_cov
    ex = df["exp"].values
    e = np.clip(ex / max(job["min_exp"], 0.5), 0, 1)
    e = np.where(ex > job["max_exp"] + 4, e * 0.85, e)
    ed = np.clip(df["edu"].values / max(job["edu_min"], 1), 0, 1)
    sal = df["salary"].values
    sl = np.where(sal <= job["sal_max"], 1.0, np.clip(1 - (sal - job["sal_max"]) / job["sal_max"] * 2, 0, 1))
    lc = np.where((df["city"].values == job["location"]) | (job["location"] == "Remote"), 1.0, 0.6)
    comps = dict(skills=sk, exp=e, edu=ed, salary=sl, loc=lc)
    tot = sum(w[k] * comps[k] for k in comps) / max(sum(w.values()), 1) * 100
    return tot, must_cov, comps


def explain(cid, job, w=None):
    sc, must, comps = score_vec(job, w)
    p = S.df.index.get_loc(cid)
    have = [SKILLS[i] for i in np.where(S.M[p] > 0)[0]]
    return dict(score=float(sc[p]), must=float(must[p]), comps={k: float(v[p]) for k, v in comps.items()}, have=have,
                mm=[s for s in job["must"] if s in have], mx=[s for s in job["must"] if s not in have],
                nm=[s for s in job["nice"] if s in have], nx=[s for s in job["nice"] if s not in have])


def ai_summary(c, job, ex):
    s = ex["score"]
    label = "Excellent fit" if s >= 85 else "Good fit" if s >= 70 else "Partial fit" if s >= 50 else "Weak fit"
    txt = f"**{label} ({s:.0f}%)** - has {len(ex['mm'])}/{len(job['must'])} must-have skills"
    if ex["mx"]:
        txt += f" (gap: {', '.join(ex['mx'])})"
    txt += f"; {c['exp']} yrs experience vs {job['min_exp']:g}+ required; "
    txt += f"expects PKR {c['salary']:,} (AI market estimate {sal_range(c['ai_salary'])}) "
    txt += "- within budget." if c["salary"] <= job["sal_max"] else f"- above the PKR {job['sal_max']:,} budget cap."
    return txt


def suggested_offer(c, job):
    return int(min(max(c["salary"], job["sal_min"]), job["sal_max"]))


# =============================================================================
# EVENTS / EMAIL / STAGE MOVES  (candidate responses + department forwarding)
# =============================================================================
def ev(text, kind="info"):
    S.events.insert(0, dict(time=nowstr(), text=text, kind=kind, read=False))


def _clean(v):
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return float(v)
    if isinstance(v, (date, datetime, pd.Timestamp)):
        return str(v)
    if isinstance(v, (list, tuple, set, np.ndarray)):
        return [_clean(x) for x in list(v)]
    if isinstance(v, dict):
        return {str(k): _clean(x) for k, x in v.items()}
    return v


def publish_event(name, payload):
    """BACKEND HOOK: Azure Service Bus / Event Grid / Logic Apps webhook. Abhi kuch nahi karta."""
    return None


def persist(kind, ids=None):
    """BACKEND HOOK: write-through to Azure SQL / Cosmos DB (kind = candidate/job/ad/interview/offer/...)."""
    return None


def emit(name, **payload):
    p = _clean(payload)
    S.eventlog.insert(0, dict(time=datetime.now().strftime("%d %b %H:%M:%S"), event=name, payload=p))
    del S.eventlog[1500:]
    publish_event(name, p)


def send_mail(ids, key, extra=None):
    """BACKEND HOOK: Azure Communication Services Email / SMS / WhatsApp."""
    ids = list(ids)
    if not ids or key not in S.templates:
        return
    subj, body = S.templates[key]
    jobs = {j["id"]: j["title"] for j in S.jobs}
    sub = S.df.loc[ids, ["name", "email", "job_id"]]
    ts = nowstr()
    rows = []
    for cid, name, email, jid in sub.itertuples():
        job = jobs.get(jid, "your application")
        kw = {**DEFAULT_KW, **dict(name=name, job=job, company=S.settings["company"]), **(extra or {})}
        rows.append(dict(time=ts, to=email, name=name, type=key, subject=render(subj, **kw), body=render(body, **kw),
                         job=job, audience="Candidate", status="Sent (simulated)"))
    S.outbox.extend(rows)


def send_internal(to_email, to_name, key, **kw):
    subj, body = S.templates[key]
    k = {**DEFAULT_KW, **dict(name=to_name, company=S.settings["company"]), **kw}
    S.outbox.append(dict(time=nowstr(), to=to_email, name=to_name, type=key, subject=render(subj, **k),
                         body=render(body, **k), job=kw.get("job", ""), audience="Internal", status="Sent (simulated)"))


STAGE_MAIL = {"Shortlisted": "Shortlisted", "Rejected": "Regret / rejection", "Hired": "Welcome onboard"}


def move(ids, stage, reason="", email="auto", extra=None):
    ids = [int(i) for i in ids]
    if not ids:
        return
    S.df.loc[ids, "stage"] = stage
    ts = nowstr()
    for i in ids:
        S.hist.setdefault(i, []).append((ts, stage, reason))
    key = STAGE_MAIL.get(stage) if email == "auto" else email
    if key and S.auto["send_emails"]:
        send_mail(ids, key, extra)
    S.ver += 1
    persist("candidate", ids)


def reject(ids, reason="", share=False):
    """Candidate ko automatic response jata hai (Regret email) + event 'candidate.rejected'."""
    ids = [int(i) for i in ids]
    if not ids:
        return
    fb = f"\nFeedback: {reason}\n" if (share and reason) else ""
    move(ids, "Rejected", reason or "Rejected", email="Regret / rejection", extra=dict(feedback_line=fb))
    emit("candidate.rejected", candidate_ids=ids[:100], count=len(ids), reason=reason, feedback_shared=bool(fb),
         response="regret_email_sent" if S.auto["send_emails"] else "email_disabled")


def add_handoff(cid, job, status="Pending", comment="", sent_on=None):
    if any(h["cid"] == cid and h["status"] == "Pending" for h in S.handoffs):
        return None
    h = dict(id=len(S.handoffs) + 1, cid=int(cid), job_id=job["id"], dept=job["dept"], head=DEPT_HEADS[job["dept"]][0],
             status=status, sent_on=sent_on or TODAY, decided_on=None if status == "Pending" else TODAY, comment=comment)
    S.handoffs.append(h)
    return h


def forward_to_dept(ids, note=""):
    """HR accept -> department ko forward (email + handoff queue + event)."""
    ids = [int(i) for i in ids if S.df.at[int(i), "job_id"] > 0 and S.df.at[int(i), "stage"] in ("Shortlisted", "Applied", "Talent Pool", "On Hold")]
    if not ids:
        return 0
    move(ids, "Dept Review", "Forwarded to department", email=None)
    groups = {}
    for i in ids:
        job = get_job(int(S.df.at[i, "job_id"]))
        add_handoff(i, job)
        groups.setdefault(job["id"], []).append(i)
    for jid, cids in groups.items():
        job = get_job(jid)
        name, mail = DEPT_HEADS[job["dept"]]
        top = S.df.loc[cids].sort_values("score", ascending=False).head(5)
        lines = "\n".join(f"- {r['name']} ({pct(r['score'])} match, {r['exp']} yrs, expects PKR {r['salary']:,})" for _, r in top.iterrows())
        send_internal(mail, name, "Dept forward", job=job["title"], dept=job["dept"], count=len(cids), candidates=lines)
    emit("candidate.forwarded_to_department", candidate_ids=ids[:100], count=len(ids), departments=sorted({get_job(int(S.df.at[i, 'job_id']))['dept'] for i in ids}), note=note)
    ev(f"{len(ids)} candidate(s) forwarded to department heads", "info")
    return len(ids)


def shortlist(ids, reason="", job_id=None, forward=None):
    ids = [int(i) for i in ids]
    if not ids:
        return 0
    if job_id:
        S.df.loc[ids, "job_id"] = job_id
    move(ids, "Shortlisted", reason)
    emit("candidate.shortlisted", candidate_ids=ids[:100], count=len(ids), reason=reason)
    forward = S.auto["auto_forward"] if forward is None else forward
    return forward_to_dept(ids) if forward else 0


def dept_decide(hid, decision, comment=""):
    h = next(x for x in S.handoffs if x["id"] == hid)
    h.update(status=decision, decided_on=TODAY, comment=comment)
    cid = h["cid"]
    if decision == "Approved":
        move([cid], "Interview", "Approved by department", email=None)
        emit("department.approved", candidate_id=cid, job_id=h["job_id"], department=h["dept"], comment=comment)
        if S.auto["auto_schedule"]:
            auto_schedule([cid], "Technical", TODAY + timedelta(days=1), [h["head"], S.settings["user"]], "Online", 45)
    elif decision == "Declined":
        reject([cid], reason=f"Declined by department: {comment}" if comment else "Declined by department", share=S.auto["share_feedback"])
        emit("department.declined", candidate_id=cid, job_id=h["job_id"], department=h["dept"], comment=comment)
    elif decision == "On Hold":
        move([cid], "On Hold", "Department asked to hold", email=None)


def goto(name, job_id=None):
    if job_id:
        S.mj_pref = job_id
        S.ad_pref = job_id
    if name in PG:
        st.switch_page(PG[name])


# =============================================================================
# AUTOMATION ENGINE
# BACKEND HOOK: yeh poora function Azure Function / Logic App par shift ho sakta hai
# =============================================================================
def send_due_reminders():
    n = 0
    now = datetime.now()
    for iv in S.interviews:
        if iv["status"] != "Scheduled" or iv["reminded"]:
            continue
        when = datetime.combine(iv["date"], datetime.strptime(iv["time"], "%H:%M").time())
        if timedelta(0) <= when - now <= timedelta(hours=S.auto["reminder_hours"]):
            send_mail([iv["cid"]], "Interview reminder", dict(date=iv["date"].strftime("%A, %d %b"), time=iv["time"],
                                                              mode=iv["mode"], link=iv.get("link", "")))
            iv["reminded"] = True
            n += 1
    return n


def send_offer_followups():
    n = 0
    for o in S.offers:
        if o["status"] == "Sent" and (TODAY - o["sent_on"]).days >= S.auto["followup_days"] and not o.get("followed"):
            send_mail([o["cid"]], "Offer follow-up")
            o["followed"] = True
            n += 1
    return n


def run_automation(only_before=None, rescreen=False, quiet=False):
    a, df = S.auto, S.df
    t0 = time.perf_counter()
    res = dict(screened=0, shortlisted=0, forwarded=0, rejected=0, review=0, pooled=0, acked=0, reminders=0, followups=0, skipped=0)
    m = (df["stage"] == "Applied") & (df["job_id"] > 0)
    if not rescreen:
        m &= df["score"].isna()
    if only_before is not None:
        m &= df["applied"] < pd.Timestamp(only_before)
    pend = df[m]
    if a["ack"] and a["send_emails"]:
        ack_ids = pend.index[~pend["acked"].values]
        send_mail(ack_ids, "Application received")
        df.loc[ack_ids, "acked"] = True
        res["acked"] = len(ack_ids)
    jobs = {j["id"]: j for j in S.jobs}
    for jid, grp in pend.groupby("job_id"):
        job = jobs.get(jid)
        if job is None or job["status"] != "Open":
            res["skipped"] += len(grp)
            continue
        sc, must, _ = score_vec(job)
        pos = df.index.get_indexer(grp.index)
        s, mc, idx = sc[pos], must[pos], grp.index
        df.loc[idx, "score"] = np.round(s, 1)
        ko = mc < job["min_must"]
        rej = (s < a["reject_below"]) | (ko & a["reject_knockout"])
        ok = (~rej) & (s >= a["shortlist_at"]) & (~ko)
        existing = int(((df["job_id"] == jid) & df["stage"].isin(["Shortlisted", "Dept Review"])).sum())
        room = max(0, a["max_shortlist"] - existing)
        sl_ids = idx[ok][np.argsort(-s[ok])][:room]
        rej_ids = idx[rej]
        rest = idx[(~rej) & (~idx.isin(sl_ids))]
        reject(rej_ids, "AI auto-screen: below threshold or missing must-have skills")
        fwd = shortlist(sl_ids, f"AI auto-shortlist (>={a['shortlist_at']}%)")
        if a["pool_rest"]:
            move(rest, "Talent Pool", "AI auto-screen: keep for future", email=None)
            res["pooled"] += len(rest)
        else:
            res["review"] += len(rest)
        res["screened"] += len(idx)
        res["shortlisted"] += len(sl_ids)
        res["forwarded"] += fwd
        res["rejected"] += len(rej_ids)
        emit("cv.screened", job_id=jid, screened=len(idx), shortlisted=len(sl_ids), rejected=len(rej_ids), review=len(rest))
        if a["notify_hr"] and not quiet:
            ev(f"{job['title']}: {len(sl_ids)} shortlisted, {len(rej_ids)} rejected, {len(rest)} need review", "success")
    res["reminders"] = send_due_reminders()
    res["followups"] = send_offer_followups()
    res["seconds"] = round(time.perf_counter() - t0, 2)
    res["time"] = nowstr()
    if not quiet:
        S.autolog.insert(0, res)
        S.last_run = res
        ev(f"Automation run complete: {res['screened']} CVs screened in {res['seconds']}s", "info")
    return res


# =============================================================================
# INTERVIEWS / OFFERS / EMPLOYEES
# =============================================================================
def cname(cid):
    return S.df.at[cid, "name"] if cid in S.df.index else "(removed)"


def conflicts_for(d, t, panel):
    return [iv for iv in S.interviews if iv["status"] == "Scheduled" and iv["date"] == d and iv["time"] == t
            and set(iv["panel"]) & set(panel)]


def schedule_interview(cid, rnd, d, t, mode, panel, override=False, silent=False):
    if conflicts_for(d, t, panel) and not override:
        return False
    iid = len(S.interviews) + 1
    link = f"Join link: https://teams.microsoft.com/l/meetup-join/xloop-{iid}" if mode == "Online" else ""
    S.interviews.append(dict(id=iid, cid=int(cid), job_id=int(S.df.at[cid, "job_id"]), round=rnd, date=d, time=t, mode=mode,
                             panel=list(panel), status="Scheduled", scores=None, rec="", comment="", reminded=False, link=link))
    move([cid], "Interview", f"{rnd} on {d}", email=None)
    if not silent:
        send_mail([cid], "Interview invitation", dict(date=d.strftime("%A, %d %b %Y"), time=t, mode=mode,
                                                      panel=", ".join(panel), link=link))
        emit("interview.scheduled", candidate_id=int(cid), round=rnd, date=d, time=t, mode=mode, panel=panel)
    persist("interview", [iid])
    return True


def slot_stream(start, mins=45):
    day = start
    while True:
        if day.weekday() < 5:
            cur = datetime.combine(day, datetime.strptime("10:00", "%H:%M").time())
            end = datetime.combine(day, datetime.strptime("17:00", "%H:%M").time())
            while cur + timedelta(minutes=mins) <= end:
                if not (13 <= cur.hour < 14):
                    yield day, cur.strftime("%H:%M")
                cur += timedelta(minutes=mins)
        day += timedelta(days=1)


def auto_schedule(ids, rnd, start, panel, mode, mins):
    n = 0
    gen = slot_stream(start, mins)
    for cid in ids:
        for d, t in gen:
            if not conflicts_for(d, t, panel):
                schedule_interview(cid, rnd, d, t, mode, panel)
                n += 1
                break
    return n


def awaiting_schedule():
    sched = {iv["cid"] for iv in S.interviews if iv["status"] == "Scheduled"}
    sub = S.df[S.df["stage"] == "Interview"]
    return sub[~sub.index.isin(sched)]


def offer_letter(cid, job, salary, joining):
    c = S.df.loc[cid]
    return (f"OFFER OF EMPLOYMENT\n\nDate: {TODAY:%d %B %Y}\n\nDear {c['name']},\n\n"
            f"We are pleased to offer you the position of {job['title']} in the {job['dept']} department at "
            f"{S.settings['company']}.\n\nMonthly gross salary : PKR {salary:,}\nJoining date         : {joining:%d %B %Y}\n"
            f"Location             : {job['location']}\nProbation            : 3 months\n\n"
            f"Please sign and return this letter to confirm your acceptance.\n\nRegards,\n"
            f"{S.settings['user']}\nPeople & Culture, {S.settings['company']}\n")


def make_employee(cid, salary, joining):
    c = S.df.loc[cid]
    job = get_job(int(c["job_id"])) or dict(title=c["title"], dept=c["dept"])
    S.employees.append(dict(id=len(S.employees) + 1, cid=int(cid), name=c["name"], title=job["title"], dept=job["dept"],
                            join=joining, salary=salary, hired_on=TODAY, applied=c["applied"].date(),
                            tasks={t: (i < 2) for i, t in enumerate(ONBOARD_TASKS)}))
    emit("candidate.hired", candidate_id=int(cid), job_id=int(c["job_id"]), department=job["dept"], salary=salary, joining=joining)
    persist("employee", [cid])


def compute_alerts():
    df, al = S.df, []
    pend = int(((df["stage"] == "Applied") & df["score"].isna() & (df["job_id"] > 0)).sum())
    if pend:
        al.append(("high", f"{pend:,} new CVs are waiting for AI screening", "Automation", None, "Run automation"))
    review = int(((df["stage"] == "Applied") & df["score"].notna()).sum())
    if review:
        al.append(("med", f"{review:,} borderline CVs need manual review", "Pipeline", None, "Review"))
    for j in S.jobs:
        dl = (j["deadline"] - TODAY).days
        if j["status"] == "Open" and dl <= 5:
            al.append(("high", f"'{j['title']}' closes in {dl} day(s)", "AI Matching", j["id"], "Find talent"))
        if j["status"] == "Pending Approval":
            al.append(("med", f"'{j['title']}' is waiting for approval", "Job Requisitions", None, "Open"))
        if j["status"] == "Open" and not ad_for_job(j["id"]):
            al.append(("med", f"'{j['title']}' is approved but has no advertisement", "Job Ads & Careers", j["id"], "Create ad"))
    for h in S.handoffs:
        if h["status"] == "Pending" and (TODAY - h["sent_on"]).days >= 2:
            al.append(("high", f"{h['dept']} has not reviewed {cname(h['cid'])} for {(TODAY - h['sent_on']).days} days", "Department Handoff", None, "Open"))
    n_wait = len(awaiting_schedule())
    if n_wait:
        al.append(("med", f"{n_wait} department-approved candidate(s) need an interview slot", "Interviews", None, "Schedule"))
    for iv in S.interviews:
        if iv["status"] == "Scheduled" and iv["date"] <= TODAY + timedelta(days=1):
            al.append(("med", f"Interview: {cname(iv['cid'])} - {iv['round']} on {iv['date']:%d %b} {iv['time']}", "Interviews", None, "Agenda"))
        if iv["status"] == "Completed" and iv["scores"] is None:
            al.append(("med", f"Scorecard pending for {cname(iv['cid'])}", "Interviews", None, "Fill"))
    for o in S.offers:
        if o["status"] == "Sent" and (TODAY - o["sent_on"]).days >= S.auto["followup_days"]:
            al.append(("med", f"Offer to {cname(o['cid'])} has no reply for {(TODAY - o['sent_on']).days} days", "Offers & Onboarding", None, "Follow up"))
    return al


# =============================================================================
# SEEDING
# =============================================================================
def init():
    if "ready" in S:
        return
    n = S.pop("n_seed", 5000)
    S.settings = dict(company="Xloop", role="HR Manager", user="Sadam Ahmed", new_days=7)
    S.jobs = default_jobs()
    S.hist, S.outbox, S.events, S.interviews, S.offers = {}, [], [], [], []
    S.employees, S.autolog, S.handoffs, S.eventlog, S.ads = [], [], [], [], []
    S.templates = dict(DEFAULT_TEMPLATES)
    S.auto = dict(send_emails=True, ack=True, shortlist_at=80, reject_below=40, reject_knockout=True, max_shortlist=15,
                  pool_rest=False, auto_forward=True, auto_schedule=True, share_feedback=False, run_on_import=True,
                  reminder_hours=24, followup_days=3, notify_hr=True)
    S.ver, S.last_run, S.mj_pref, S.ad_pref = 0, None, 1, 1
    by_dept = {}
    for j in S.jobs:
        if j["status"] == "Open":
            by_dept.setdefault(j["dept"], []).append(j["id"])
    S.df = generate_cvs(n, 1, 42, jobs_by_dept=by_dept)
    rebuild_matrix()
    S.auto["auto_forward"] = False
    run_automation(only_before=TODAY - timedelta(days=10), quiet=True)
    S.auto["auto_forward"] = True
    for k, j in enumerate([x for x in S.jobs if x["status"] == "Open"]):
        sl = S.df[(S.df["job_id"] == j["id"]) & (S.df["stage"] == "Shortlisted")].sort_values("score", ascending=False)
        panel = [DEPT_HEADS[j["dept"]][0], PANEL[1]]
        for pos, cid in enumerate(list(sl.index[:6])):
            if pos == 0:
                add_handoff(cid, j, "Approved", "Strong profile", TODAY - timedelta(days=6))
                schedule_interview(cid, "Technical", TODAY - timedelta(days=2), "11:00", "Online", panel, silent=True, override=True)
                S.interviews[-1].update(status="Completed", scores={"Technical": 4, "Communication": 4, "Problem Solving": 5, "Culture Fit": 4},
                                        rec="Hire", comment="Strong candidate.")
            elif pos == 1:
                add_handoff(cid, j, "Approved", "OK to interview", TODAY - timedelta(days=4))
                schedule_interview(cid, "HR Screening", TODAY + timedelta(days=1 + k % 3), f"{10 + k % 5}:00", "Onsite", panel, silent=True, override=True)
            elif pos == 2 and k % 3 == 0:
                add_handoff(cid, j, "Approved", "Good fit", TODAY - timedelta(days=9))
                move([cid], "Offer", "Seed", email=None)
                sal = suggested_offer(S.df.loc[cid], j)
                S.offers.append(dict(id=len(S.offers) + 1, cid=int(cid), job_id=j["id"], salary=sal, joining=TODAY + timedelta(days=30),
                                     status="Sent", sent_on=TODAY - timedelta(days=4), letter=offer_letter(cid, j, sal, TODAY + timedelta(days=30))))
            elif pos == 2 and k % 4 == 1:
                add_handoff(cid, j, "Approved", "Good fit", TODAY - timedelta(days=12))
                move([cid], "Hired", "Seed", email=None)
                make_employee(cid, suggested_offer(S.df.loc[cid], j), TODAY + timedelta(days=14))
            else:
                add_handoff(cid, j, "Pending", "", TODAY - timedelta(days=(k + pos) % 4))
                move([cid], "Dept Review", "Forwarded to department", email=None)
    for j in S.jobs:
        if j["status"] == "Open":
            ad = create_ad(j, "Live", random.Random(j["id"]).sample(CHANNELS, 4))
            ad["posted_on"] = j["created"] + timedelta(days=1)
    S.events, S.autolog, S.eventlog = [], [], []
    ev("Welcome to Xloop Recruitment Suite", "info")
    S.ready = True


# =============================================================================
# UI HELPERS
# =============================================================================
CSS = """<style>
.block-container {padding-top: 1rem; max-width: 1500px;}
section[data-testid="stSidebar"] {border-right: 1px solid rgba(120,130,160,.25);}
.hdr {background: linear-gradient(90deg,#10235c,#1b3a8a 60%,#2b59d6); color:#fff; padding:16px 26px; border-radius:14px;
      display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; box-shadow:0 4px 14px rgba(16,35,92,.25);}
.hdr h2 {margin:0; font-size:25px; color:#fff; padding:0;} .hdr p {margin:2px 0 0; opacity:.8; font-size:14px; color:#fff;}
.hdr .right {text-align:right; font-weight:600; color:#fff;} .hdr .right span {font-weight:400; font-size:13px; opacity:.85;}
.kpi {border-radius:14px; padding:14px 18px; border:1px solid rgba(120,130,160,.25); border-left:5px solid var(--c);
      background:linear-gradient(90deg,color-mix(in srgb,var(--c) 10%,transparent),transparent);}
.kpi .l {font-size:13px; opacity:.75;} .kpi .v {font-size:29px; font-weight:700; line-height:1.2;} .kpi .s {font-size:12px; opacity:.6;}
.k1{--c:#3b82f6} .k2{--c:#22c55e} .k3{--c:#8b5cf6} .k4{--c:#f97316} .k5{--c:#06b6d4} .k6{--c:#ec4899}
.life {display:flex; gap:6px; align-items:stretch; margin-bottom:6px; flex-wrap:wrap;}
.lstep {flex:1; min-width:105px; border-radius:12px; padding:10px 10px 8px; text-align:center; border:1px solid rgba(120,130,160,.25);
        background:linear-gradient(180deg,color-mix(in srgb,var(--c) 14%,transparent),transparent);}
.lstep .n {font-size:22px; font-weight:700;} .lstep .t {font-size:12px; opacity:.8;} .lstep .i {font-size:18px;}
.adcard {border:1px solid rgba(120,130,160,.3); border-radius:14px; padding:16px 18px; background:rgba(120,130,160,.06);}
.adcard h4 {margin:0 0 6px;} .adcard .ch {font-size:12px; opacity:.7;}
.cand-h {display:flex; gap:14px; align-items:center; margin-bottom:6px;}
.cand-h .av {width:48px; height:48px; border-radius:50%; background:linear-gradient(135deg,#3b82f6,#7c3aed); color:#fff;
             display:flex; align-items:center; justify-content:center; font-weight:700; font-size:18px;}
.cand-h .nm {font-size:20px; font-weight:700;} .cand-h .sb {font-size:13px; opacity:.7;}
</style>"""


def badge(stage):
    col = {"Applied": "#dbeafe|#1e40af", "Shortlisted": "#ede9fe|#5b21b6", "Dept Review": "#cffafe|#155e75",
           "Interview": "#e0e7ff|#3730a3", "Offer": "#ffedd5|#9a3412", "Hired": "#bbf7d0|#14532d",
           "Rejected": "#fee2e2|#991b1b", "On Hold": "#fef3c7|#92400e", "Talent Pool": "#e5e7eb|#374151"}[stage]
    bg, fg = col.split("|")
    return f"<span style='background:{bg};color:{fg};padding:2px 10px;border-radius:8px;font-size:12px;font-weight:600'>{stage}</span>"


def type_badge(is_new):
    bg, fg, t = ("#dcfce7", "#166534", "NEW CV") if is_new else ("#e5e7eb", "#374151", "EXISTING CV")
    return f"<span style='background:{bg};color:{fg};padding:2px 10px;border-radius:8px;font-size:11px;font-weight:700'>{t}</span>"


def chips(items, tone="b"):
    c = dict(b=("#eaf1ff", "#1e40af"), g=("#dcfce7", "#166534"), r=("#fee2e2", "#991b1b"), y=("#fef3c7", "#92400e"))[tone]
    return "".join(f"<span style='display:inline-block;background:{c[0]};color:{c[1]};padding:2px 10px;margin:2px 4px 2px 0;"
                   f"border-radius:999px;font-size:12px'>{s}</span>" for s in items) or "<span style='opacity:.6'>None</span>"


def kpi(label, value, sub="", tone="k1"):
    return f"<div class='kpi {tone}'><div class='l'>{label}</div><div class='v'>{value}</div><div class='s'>{sub}</div></div>"


def header(title, sub=""):
    st.markdown(f"<div class='hdr'><div><h2>{title}</h2><p>{sub}</p></div><div class='right'>"
                f"{S.settings['company']} · People &amp; Culture<br><span>{TODAY:%A, %d %B %Y}</span></div></div>",
                unsafe_allow_html=True)


def view_df(sub):
    return pd.DataFrame({"ID": sub.index, "Name": sub["name"].values, "Title": sub["title"].values, "Dept": sub["dept"].values,
                         "CV Type": np.where(new_mask(sub), "New", "Existing"), "Exp": sub["exp"].values,
                         "Education": sub["edu"].map(EDU).values, "City": sub["city"].values,
                         "Expected Salary": sub["salary"].values, "AI Est. Salary": sub["ai_salary"].values,
                         "Skills": sub["skills"].str.replace("|", ", ", regex=False).values, "Source": sub["source"].values,
                         "Applied": sub["applied"].dt.date.values, "Stage": sub["stage"].values,
                         "Match %": sub["score"].round(0).values})


PROG = st.column_config.ProgressColumn("Match %", min_value=0, max_value=100, format="%.0f")
SAL_CFG = {"Expected Salary": st.column_config.NumberColumn(format="PKR %d"),
           "AI Est. Salary": st.column_config.NumberColumn(format="PKR %d")}


def reset_filters(prefix):
    for k in [k for k in S.keys() if isinstance(k, str) and k.startswith(prefix)]:
        del S[k]


def cv_filters(p):
    """Reusable filter bar: CV type (New/Existing), date, subject/skills, department, experience, salary..."""
    df = S.df
    r1 = st.columns([2.2, 1.5, 1.6, 1.2])
    kw = r1[0].text_input("🔎 Search (name, title, skill, email)", key=p + "kw", placeholder="e.g. Python, Ayesha, Accountant")
    ctype = r1[1].radio("CV type", ["All", "New", "Existing"], horizontal=True, key=p + "ct")
    when = r1[2].selectbox("Date applied", ["Any time", "Today", "Last 7 days", "Last 30 days", "This month", "Custom range"], key=p + "wh")
    dept = r1[3].selectbox("Department", ["All"] + DEPTS, key=p + "dp")
    dr = None
    if when == "Custom range":
        dr = st.date_input("From - To", (TODAY - timedelta(days=30), TODAY), key=p + "dr")
    r2 = st.columns([2.2, 1.2, 1.8, 1.2])
    skl = r2[0].multiselect("Subject / Skills", SKILLS, key=p + "sk")
    mode = r2[1].radio("Skills match", ["ALL", "ANY"], horizontal=True, key=p + "sm")
    pos = r2[2].selectbox("Applied position", [0] + [j["id"] for j in S.jobs],
                          format_func=lambda i: "All positions" if i == 0 else get_job(i)["title"], key=p + "po")
    emin = r2[3].selectbox("Min education", list(EDU), format_func=lambda k: EDU[k], key=p + "ed")
    with st.expander("More filters (experience, salary, city, source, stage)"):
        m1, m2, m3 = st.columns(3)
        er = m1.slider("Experience (yrs)", 0.0, 25.0, (0.0, 25.0), key=p + "ex")
        sal = m1.slider("Expected salary (PKR K)", 0, 500, (0, 500), key=p + "sa")
        city = m2.multiselect("City", CITIES, key=p + "ci")
        src = m2.multiselect("Source / Channel", SOURCES, key=p + "so")
        stg = m3.multiselect("Stage", STAGES, default=STAGES, key=p + "st")
    m = df["stage"].isin(stg).values & df["exp"].between(*er).values & (df["edu"].values >= emin)
    m &= df["salary"].between(sal[0] * 1000, sal[1] * 1000).values
    if kw:
        m &= (df["name"].str.contains(kw, case=False, regex=False) | df["title"].str.contains(kw, case=False, regex=False) |
              df["skills"].str.contains(kw, case=False, regex=False) | df["email"].str.contains(kw, case=False, regex=False)).values
    if ctype != "All":
        m &= new_mask(df) if ctype == "New" else ~new_mask(df)
    ap = df["applied"]
    if when == "Today":
        m &= (ap >= pd.Timestamp(TODAY)).values
    elif when == "Last 7 days":
        m &= (ap >= pd.Timestamp(TODAY - timedelta(days=7))).values
    elif when == "Last 30 days":
        m &= (ap >= pd.Timestamp(TODAY - timedelta(days=30))).values
    elif when == "This month":
        m &= (ap >= pd.Timestamp(TODAY.replace(day=1))).values
    elif dr is not None and len(dr) == 2:
        m &= ((ap >= pd.Timestamp(dr[0])) & (ap <= pd.Timestamp(dr[1]))).values
    if dept != "All":
        m &= (df["dept"].values == dept)
    if pos:
        m &= (df["job_id"].values == pos)
    if skl:
        cols = S.M[:, [SK_IDX[s] for s in skl]] > 0
        m &= cols.all(axis=1) if mode == "ALL" else cols.any(axis=1)
    if city:
        m &= df["city"].isin(city).values
    if src:
        m &= df["source"].isin(src).values
    out = df[m]
    nn = int(new_mask(out).sum()) if len(out) else 0
    a, b = st.columns([5, 1])
    a.markdown(f"**{len(out):,}** of {len(df):,} CVs match &nbsp;·&nbsp; 🟢 New: **{nn:,}** &nbsp;·&nbsp; ⚪ Existing: **{len(out) - nn:,}**")
    b.button("↺ Reset filters", key=p + "reset", on_click=reset_filters, args=(p,))
    return out


def candidate_card(cid, key, job_override=None):
    c = S.df.loc[cid]
    job = job_override or get_job(int(c["job_id"]))
    isnew = bool(c["applied"] >= pd.Timestamp(TODAY - timedelta(days=int(S.settings["new_days"]))))
    ini = "".join(w[0] for w in c["name"].split()[:2]).upper()
    st.markdown(f"<div class='cand-h'><div class='av'>{ini}</div><div><div class='nm'>{c['name']}</div>"
                f"<div class='sb'>{c['title']} · {c['city']} · {c['exp']} yrs · {EDU[c['edu']]}</div></div></div>", unsafe_allow_html=True)
    st.markdown(badge(c["stage"]) + " " + type_badge(isnew) + f" &nbsp; <small>{c['source']} · applied {c['applied']:%d %b %Y} · "
                f"{c['email']} · {c['phone']}</small>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Expected salary", f"PKR {c['salary'] / 1000:,.0f}K")
    m2.metric("AI market estimate", f"PKR {c['ai_salary'] / 1000:,.0f}K", help=sal_range(c["ai_salary"]))
    if job:
        m3.metric("Suggested offer", f"PKR {suggested_offer(c, job) / 1000:,.0f}K", help=f"Budget: PKR {job['sal_min']:,} - {job['sal_max']:,}")
    else:
        m3.metric("Suggested offer", "n/a")
    st.markdown("**Skills**<br>" + chips(c["skills"].split("|")), unsafe_allow_html=True)
    if job:
        ex = explain(cid, job)
        st.info(ai_summary(c, job, ex))
        t1, t2 = st.tabs([f"Match vs {job['title']}", "Skill gap"])
        with t1:
            for k, lbl in [("skills", "Skills"), ("exp", "Experience"), ("edu", "Education"), ("salary", "Salary fit"), ("loc", "Location")]:
                st.progress(min(max(ex["comps"][k], 0.0), 1.0), text=f"{lbl}: {ex['comps'][k] * 100:.0f}%")
        with t2:
            st.markdown("**Must-have matched**<br>" + chips(ex["mm"], "g"), unsafe_allow_html=True)
            st.markdown("**Must-have missing**<br>" + chips(ex["mx"], "r"), unsafe_allow_html=True)
            st.markdown("**Nice-to-have matched**<br>" + chips(ex["nm"], "g"), unsafe_allow_html=True)
    b = st.columns(5)
    jid = job["id"] if job else 0
    if b[0].button("⭐ Shortlist", key=f"{key}_sl_{cid}", disabled=not jid):
        shortlist([cid], "Manual shortlist", job_id=jid); st.rerun()
    if b[1].button("📤 Forward to dept", key=f"{key}_fw_{cid}", disabled=not jid):
        S.df.at[cid, "job_id"] = jid
        forward_to_dept([cid]); st.rerun()
    if b[2].button("⏸ Hold", key=f"{key}_ho_{cid}"):
        move([cid], "On Hold", "Manual action", email=None); st.rerun()
    if b[3].button("🗂 Talent pool", key=f"{key}_tp_{cid}"):
        move([cid], "Talent Pool", "Manual action", email=None); st.rerun()
    with b[4].popover("✖ Reject"):
        why = st.selectbox("Reason", REJECT_REASONS, key=f"{key}_rr_{cid}")
        share = st.checkbox("Share feedback with candidate", key=f"{key}_rs_{cid}")
        st.caption("Candidate ko regret email automatically jayegi.")
        if st.button("Confirm reject", key=f"{key}_rc_{cid}", type="primary"):
            reject([cid], why, share); st.rerun()
    with st.expander("📅 Schedule interview"):
        f1, f2, f3, f4 = st.columns(4)
        rnd = f1.selectbox("Round", ROUNDS, key=f"{key}_r_{cid}")
        d = f2.date_input("Date", TODAY + timedelta(days=2), key=f"{key}_d_{cid}")
        t = f3.time_input("Time", datetime.strptime("11:00", "%H:%M").time(), key=f"{key}_t_{cid}")
        mode = f4.selectbox("Mode", ["Onsite", "Online", "Phone"], key=f"{key}_m_{cid}")
        pn = st.multiselect("Panel", PANEL, default=PANEL[:2], key=f"{key}_p_{cid}")
        if st.button("Confirm & notify candidate", key=f"{key}_ci_{cid}"):
            if schedule_interview(cid, rnd, d, t.strftime("%H:%M"), mode, pn):
                st.rerun()
            else:
                st.error("Panel conflict at this time. Choose another slot.")
    notes = st.text_area("Recruiter notes", c["notes"], key=f"{key}_n_{cid}")
    if st.button("Save notes", key=f"{key}_sn_{cid}"):
        S.df.at[cid, "notes"] = notes
        st.toast("Notes saved")
    hist = S.hist.get(cid, [])
    if hist:
        with st.expander("🕑 History"):
            for ts, stg, why in reversed(hist[-10:]):
                st.caption(f"{ts} → **{stg}** {('· ' + why) if why else ''}")


# =============================================================================
# IMPORT HELPERS
# =============================================================================
def new_row(**kw):
    base = dict(name="Unknown", email="", phone="", city="Karachi", title="Candidate", dept="IT", exp=1.0, edu=3, salary=0,
                skills="", source="Company Website", applied=pd.Timestamp(TODAY), stage="Applied", job_id=0, score=np.nan,
                acked=False, tags="", notes="")
    base.update(kw)
    return base


def add_candidates(new):
    """Naye CVs database mein daalta hai (email se duplicate skip). BACKEND HOOK: Azure SQL insert."""
    new = new[~new["email"].isin(S.df["email"])]
    new = new[~new["email"].duplicated()].copy()
    if new.empty:
        return []
    new["ai_salary"] = est_salary_df(new)
    new["salary"] = np.where(new["salary"] <= 0, new["ai_salary"], new["salary"])
    start = int(S.df.index.max()) + 1
    new.index = pd.RangeIndex(start, start + len(new), name="id")
    S.df = pd.concat([S.df, new])
    rebuild_matrix()
    ids = [int(i) for i in new.index]
    emit("cv.received", count=len(ids), candidate_ids=ids[:100])
    ev(f"{len(ids)} new CV(s) received", "info")
    persist("candidate", ids)
    return ids


def best_job_for(ids):
    best, bj = np.full(len(S.df), -1.0), np.zeros(len(S.df), int)
    for j in S.jobs:
        if j["status"] != "Open":
            continue
        sc, _, _ = score_vec(j)
        better = sc > best
        best, bj = np.where(better, sc, best), np.where(better, j["id"], bj)
    return bj[S.df.index.get_indexer(ids)]


def finish_import(ids, assign):
    if assign.startswith("Auto"):
        jids = best_job_for(ids)
    else:
        jids = [int(assign.split(" - ")[0])] * len(ids)
    S.df.loc[ids, "job_id"] = jids
    return run_automation() if S.auto["run_on_import"] else None


def parse_cv(name, data):
    """BACKEND HOOK: Azure AI Document Intelligence + Blob Storage."""
    text = ""
    low_name = name.lower()
    if low_name.endswith(".txt"):
        text = data.decode("utf-8", errors="ignore")
    elif low_name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
        except Exception:
            text = ""
    elif low_name.endswith(".docx"):
        try:
            import docx
            text = "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
        except Exception:
            text = ""
    low = (text + " " + name).lower()
    sk = [s for s in SKILLS if re.search(r"(?<![a-z])" + re.escape(s.lower()) + r"(?![a-z])", low)]
    em = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    ph = re.search(r"(?:\+92|0)3\d{2}[- ]?\d{7}", text)
    ex = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs|year)", text, re.I)
    edu = 5 if re.search(r"ph\.?d", low) else 4 if re.search(r"master|msc|mba|\bms\b", low) else 3 if re.search(r"bachelor|bsc|\bbs\b|bba|b\.e", low) else 2
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    nm = first if 2 <= len(first.split()) <= 4 and len(first) < 40 else re.sub(r"[_\-]+|cv|resume", " ", name.rsplit(".", 1)[0], flags=re.I).strip().title()
    city = next((c for c in CITIES if c.lower() in low), "Karachi")
    dept = max(DEPTS, key=lambda d: len(set(sk) & set(DEPT_SKILLS[d]))) if sk else "IT"
    slug = re.sub(r"[^a-z]", "", nm.lower()) or "cv"
    return new_row(name=nm or "Unknown", email=em.group(0) if em else f"{slug}{random.randint(100, 999)}@unknown.com",
                   phone=ph.group(0) if ph else "", city=city, dept=dept, exp=float(ex.group(1)) if ex else 1.0, edu=edu,
                   skills="|".join(sk))


def date_mask(df, when):
    ap = df["applied"]
    days = {"Today": 0, "Last 7 days": 7, "Last 30 days": 30}.get(when)
    if days is not None:
        return (ap >= pd.Timestamp(TODAY - timedelta(days=days))).values
    if when == "This month":
        return (ap >= pd.Timestamp(TODAY.replace(day=1))).values
    return np.ones(len(df), bool)


# =============================================================================
# PAGES - OVERVIEW
# =============================================================================
def page_dashboard():
    header("Recruitment Command Center", "Advertisement se hiring tak - sab ek jagah")
    if S.get("flash"):
        st.success(S.pop("flash"))
    df = S.df
    cnt = df["stage"].value_counts()
    nm = new_mask(df)
    pend = int(((df["stage"] == "Applied") & df["score"].isna() & (df["job_id"] > 0)).sum())
    live = sum(1 for a in S.ads if a["status"] == "Live")
    pend_dept = sum(1 for h in S.handoffs if h["status"] == "Pending")
    steps = [("📝", "Requisitions", len(S.jobs), "#3b82f6"), ("📣", "Live ads", live, "#06b6d4"),
             ("📥", "CVs received", f"{len(df):,}", "#3b82f6"), ("🤖", "AI screened", f"{int(df['score'].notna().sum()):,}", "#8b5cf6"),
             ("⭐", "Shortlisted", int(cnt.get("Shortlisted", 0)), "#8b5cf6"), ("🏢", "Dept review", int(cnt.get("Dept Review", 0)), "#06b6d4"),
             ("🎤", "Interview", int(cnt.get("Interview", 0)), "#6366f1"), ("💼", "Offer", int(cnt.get("Offer", 0)), "#f97316"),
             ("✅", "Hired", int(cnt.get("Hired", 0)), "#22c55e")]
    st.markdown("<div class='life'>" + "".join(
        f"<div class='lstep' style='--c:{c}'><div class='i'>{i}</div><div class='n'>{n}</div><div class='t'>{t}</div></div>"
        for i, t, n, c in steps) + "</div>", unsafe_allow_html=True)
    st.write("")
    r1 = st.columns(4)
    for col, (a, b, c_, t) in zip(r1, [("Total CVs in database", f"{len(df):,}", f"🟢 New {int(nm.sum()):,} · ⚪ Existing {int((~nm).sum()):,}", "k1"),
                                       (f"New CVs (last {S.settings['new_days']} days)", f"{int(nm.sum()):,}", "incoming applications", "k2"),
                                       ("Awaiting AI screening", f"{pend:,}", "run automation", "k3"),
                                       ("Open positions", sum(1 for j in S.jobs if j["status"] == "Open"), f"{live} live advertisement(s)", "k4")]):
        col.markdown(kpi(a, b, c_, t), unsafe_allow_html=True)
    st.write("")
    r2 = st.columns(4)
    for col, (a, b, c_, t) in zip(r2, [("Pending department review", pend_dept, "waiting for dept heads", "k5"),
                                       ("Interviews scheduled", sum(1 for iv in S.interviews if iv["status"] == "Scheduled"), "upcoming", "k3"),
                                       ("Offers pending", sum(1 for o in S.offers if o["status"] in ("Draft", "Sent")), "awaiting reply", "k4"),
                                       ("Hired", int(cnt.get("Hired", 0)), "this pipeline", "k2")]):
        col.markdown(kpi(a, b, c_, t), unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1.7, 1])
    with left:
        st.markdown("#### 🚨 Needs your attention")
        al = compute_alerts()
        if not al:
            st.success("Sab clear hai ✅")
        for i, (sev, txt, pg, jid, lbl) in enumerate(al[:7]):
            a, b = st.columns([5, 1.4])
            a.markdown(f"{'🔴' if sev == 'high' else '🟡'} {txt}")
            if b.button(lbl, key=f"al_{i}") and pg in PG:
                goto(pg, jid)
    with right:
        with st.container(border=True):
            st.markdown("#### ⚙️ Automation")
            lr = S.last_run
            st.caption("Last run: " + (f"{lr['time']} · {lr['screened']} screened" if lr else "not run yet"))
            if st.button("▶ Run automation now", type="primary", key="dash_run"):
                with st.spinner("Screening CVs..."):
                    r = run_automation()
                S.flash = (f"{r['screened']:,} CVs screened · {r['shortlisted']} shortlisted · {r['forwarded']} forwarded to departments · "
                           f"{r['rejected']} rejected (candidates notified) · {r['acked']} acknowledged · {r['seconds']}s")
                st.rerun()
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.markdown("##### Hiring funnel")
    c1.bar_chart(pd.Series({s: int(cnt.get(s, 0)) for s in ["Applied", "Shortlisted", "Dept Review", "Interview", "Offer", "Hired"]}))
    c2.markdown("##### Applications - last 30 days")
    last = df[df["applied"] >= pd.Timestamp(TODAY - timedelta(days=30))]
    c2.line_chart(last.groupby(last["applied"].dt.date).size())
    c3.markdown("##### Source / channel mix")
    c3.bar_chart(df["source"].value_counts())
    st.markdown("#### Open positions")
    rows = []
    for j in S.jobs:
        sub = df[df["job_id"] == j["id"]]
        ad = ad_for_job(j["id"])
        rows.append({"Position": j["title"], "Dept": j["dept"], "Status": j["status"], "Ad": ad["status"] if ad else "-",
                     "Applicants": len(sub), "New CVs": int(new_mask(sub).sum()) if len(sub) else 0,
                     "Top AI score": float(sub["score"].max()) if len(sub) and sub["score"].notna().any() else None,
                     "In pipeline": int(sub["stage"].isin(ADV_STAGES[:-1]).sum()),
                     "Hired / Headcount": f"{int((sub['stage'] == 'Hired').sum())}/{j['headcount']}", "Days left": (j["deadline"] - TODAY).days})
    st.dataframe(pd.DataFrame(rows), hide_index=True, column_config={"Top AI score": st.column_config.NumberColumn(format="%.0f%%")})
    st.markdown("#### ⭐ Top AI picks (with expected salary)")
    jobs_open = [j for j in S.jobs if j["status"] == "Open"]
    pj = st.selectbox("Position", [j["id"] for j in jobs_open], format_func=lambda i: get_job(i)["title"], key="dash_pj")
    top = df[(df["job_id"] == pj) & df["stage"].isin(["Applied", "Shortlisted", "Dept Review"])].sort_values("score", ascending=False).head(5)
    if top.empty:
        st.info("Is position ke liye abhi screened CVs nahi hain. Automation chalayein.")
    else:
        st.dataframe(view_df(top)[["Name", "Title", "CV Type", "Exp", "Expected Salary", "AI Est. Salary", "Stage", "Match %"]],
                     hide_index=True, column_config={"Match %": PROG, **SAL_CFG})


# =============================================================================
# PAGES - SOURCING
# =============================================================================
def page_jobs():
    header("Job Requisitions", "Create > Approve > Advertise > Auto-match talent")
    can_approve = S.settings["role"] in ("Admin", "HR Manager")
    t1, t2 = st.tabs(["All requisitions", "➕ New requisition"])
    with t2:
        with st.form("job_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            title = c1.text_input("Position title")
            dept = c2.selectbox("Department", DEPTS)
            loc = c3.selectbox("Location", CITIES + ["Remote"])
            hc = c4.number_input("Headcount", 1, 50, 1)
            must = st.multiselect("Must-have skills (subject)", SKILLS)
            nice = st.multiselect("Nice-to-have skills", SKILLS)
            c5, c6, c7, c8 = st.columns(4)
            mn = c5.number_input("Min experience (yrs)", 0.0, 30.0, 2.0)
            mx = c6.number_input("Max experience (yrs)", 0.0, 40.0, 8.0)
            edu = c7.selectbox("Min education", list(EDU), index=2, format_func=lambda k: EDU[k])
            dl = c8.date_input("Closing date", TODAY + timedelta(days=30))
            c9, c10, c11 = st.columns(3)
            smin = c9.number_input("Salary min (PKR)", 0, 3000000, 80000, 5000)
            smax = c10.number_input("Salary max (PKR)", 0, 3000000, 130000, 5000)
            mgr = c11.text_input("Hiring manager", DEPT_HEADS["IT"][0])
            with st.expander("Scoring weights"):
                w = {k: st.slider(k.title(), 0, 100, v, key=f"nw_{k}") for k, v in DEFAULT_WEIGHTS.items()}
            if st.form_submit_button("Submit for approval", type="primary"):
                if title and must:
                    jid = max(j["id"] for j in S.jobs) + 1
                    S.jobs.append(dict(id=jid, title=title, dept=dept, must=must, nice=nice, min_exp=mn, max_exp=mx, edu_min=edu,
                                       sal_min=smin, sal_max=smax, location=loc, headcount=hc, status="Pending Approval", deadline=dl,
                                       manager=mgr, created=TODAY, weights=w, min_must=0.6))
                    emit("job.created", job_id=jid, title=title, department=dept)
                    ev(f"New requisition '{title}' submitted for approval", "info")
                    st.success("Requisition submit ho gayi. Approval ke baad ad ka draft khud ban jayega.")
                else:
                    st.error("Title aur kam az kam ek must-have skill zaroori hai.")
    with t1:
        for j in S.jobs:
            ad = ad_for_job(j["id"])
            with st.container(border=True):
                a, b, c_ = st.columns([3.2, 2.5, 2.3])
                a.markdown(f"**{j['title']}**  \n{j['dept']} · {j['location']} · {j['headcount']} opening(s) · "
                           f"PKR {j['sal_min'] // 1000}K-{j['sal_max'] // 1000}K · closes {j['deadline']:%d %b}")
                b.markdown("Must: " + chips(j["must"], "g") + "<br>Nice: " + chips(j["nice"]), unsafe_allow_html=True)
                n_app = int((S.df["job_id"] == j["id"]).sum())
                c_.markdown(f"**{j['status']}** · {n_app:,} applicants<br>Ad: **{ad['status'] if ad else 'none'}**", unsafe_allow_html=True)
                x = st.columns(5)
                if j["status"] in ("Pending Approval", "Draft"):
                    if x[0].button("✅ Approve & open" if can_approve else "🔒 Needs HR Manager", key=f"ap_{j['id']}", disabled=not can_approve):
                        j["status"] = "Open"
                        if not ad_for_job(j["id"]):
                            create_ad(j, "Draft")
                        sc, must, _ = score_vec(j)
                        good = int(((sc >= S.auto["shortlist_at"]) & (must >= j["min_must"]) & S.df["stage"].isin(["Talent Pool", "Applied"]).values).sum())
                        emit("job.approved", job_id=j["id"], title=j["title"])
                        ev(f"'{j['title']}' approved. Draft ad created. AI found {good} strong matches in the CV database.", "success")
                        st.rerun()
                if j["status"] == "Open" and x[1].button("⏸ Hold", key=f"ho_{j['id']}"):
                    j["status"] = "On Hold"; st.rerun()
                if j["status"] in ("On Hold", "Closed") and x[1].button("▶ Reopen", key=f"ro_{j['id']}"):
                    j["status"] = "Open"; st.rerun()
                if j["status"] != "Closed" and x[2].button("⛔ Close", key=f"cl_{j['id']}"):
                    j["status"] = "Closed"; st.rerun()
                if x[3].button("📣 Job ad", key=f"ad_{j['id']}"):
                    goto("Job Ads & Careers", j["id"])
                if x[4].button("🎯 Best CVs", key=f"fb_{j['id']}"):
                    goto("AI Matching", j["id"])


def _gen_ad(jid):
    h, b = generate_ad(get_job(jid))
    S[f"ah_{jid}"], S[f"ab_{jid}"] = h, b


def publish_ad(ad):
    ad.update(status="Live", posted_on=TODAY)
    seed_views(ad)
    emit("job.published", ad_id=ad["id"], job_id=ad["job_id"], channels=ad["channels"], title=ad["headline"])
    ev(f"Ad published on {', '.join(ad['channels'])}", "success")
    persist("ad", [ad["id"]])


def page_ads():
    header("Job Ads & Careers", "Advertise > Collect applications > Track channel performance")
    t1, t2, t3, t4 = st.tabs(["📣 Advertisements", "✍ Create / publish", "🌐 Careers page (candidate view)", "📊 Channel performance"])
    with t1:
        if not S.ads:
            st.info("Abhi koi ad nahi. 'Create / publish' tab se banayein.")
        for ad in S.ads:
            job = get_job(ad["job_id"])
            stats = ad_stats(ad)
            with st.container(border=True):
                a, b, c_ = st.columns([3, 3, 2])
                a.markdown(f"**{job['title']}** · {job['dept']}  \n{ad['headline']}")
                b.markdown(chips(ad["channels"]) + f"<br><small>Posted {ad['posted_on'] or '-'} · expires {ad['expires']:%d %b}</small>", unsafe_allow_html=True)
                c_.markdown(f"**{ad['status']}**{' 🚀 boosted' if ad['boosted'] else ''}<br><small>{int(stats['Views'].sum()):,} views · {int(stats['Applications'].sum())} applications</small>", unsafe_allow_html=True)
                x = st.columns(5)
                if ad["status"] in ("Draft", "Paused") and x[0].button("🚀 Publish", key=f"pb_{ad['id']}", type="primary"):
                    publish_ad(ad); st.rerun()
                if ad["status"] == "Live" and x[1].button("⏸ Pause", key=f"pa_{ad['id']}"):
                    ad["status"] = "Paused"; st.rerun()
                if ad["status"] != "Closed" and x[2].button("⛔ Close ad", key=f"ca_{ad['id']}"):
                    ad["status"] = "Closed"; st.rerun()
                if ad["status"] == "Live" and x[3].button("⚡ Boost", key=f"bo_{ad['id']}"):
                    ad["boosted"] = True
                    ad["views"] = {k: int(v * 1.4) for k, v in ad["views"].items()}
                    st.rerun()
                x[4].download_button("⬇ Ad text", f"{ad['headline']}\n\n{ad['body']}", f"ad_{ad['id']}.txt", key=f"dl_ad_{ad['id']}")
                with st.expander("Channel stats"):
                    st.dataframe(stats, hide_index=True)
    with t2:
        jobs = [j for j in S.jobs if j["status"] in ("Open", "On Hold")]
        if not jobs:
            st.info("Pehle koi requisition approve karein.")
        else:
            ids = [j["id"] for j in jobs]
            idx = ids.index(S.ad_pref) if S.ad_pref in ids else 0
            jid = st.selectbox("Position", ids, index=idx, format_func=lambda i: f"{get_job(i)['title']} · {get_job(i)['dept']}", key="adj")
            S.ad_pref = jid
            existing = ad_for_job(jid)
            if f"ah_{jid}" not in S:
                S[f"ah_{jid}"] = existing["headline"] if existing else generate_ad(get_job(jid))[0]
                S[f"ab_{jid}"] = existing["body"] if existing else generate_ad(get_job(jid))[1]
                S[f"ac_{jid}"] = existing["channels"] if existing else ["Company Website", "LinkedIn", "Rozee.pk"]
            c1, c2 = st.columns([1.3, 1])
            with c1:
                st.button("✨ Generate with AI", key=f"gen_{jid}", on_click=_gen_ad, args=(jid,))
                head = st.text_input("Headline", key=f"ah_{jid}")
                body = st.text_area("Ad description (markdown)", height=330, key=f"ab_{jid}")
                chs = st.multiselect("Publish on", CHANNELS, key=f"ac_{jid}")
            with c2:
                st.markdown("**Live preview**")
                with st.container(border=True):
                    st.markdown(f"#### {head}")
                    st.markdown(body)
                    st.caption("Channels: " + ", ".join(chs))
            b1, b2 = st.columns(2)
            if b1.button("💾 Save as draft"):
                if existing:
                    existing.update(headline=head, body=body, channels=chs)
                else:
                    ad = create_ad(get_job(jid), "Draft", chs); ad.update(headline=head, body=body)
                st.toast("Draft saved")
            if b2.button("🚀 Publish now", type="primary", disabled=not chs):
                ad = existing or create_ad(get_job(jid), "Draft", chs)
                ad.update(headline=head, body=body, channels=chs)
                publish_ad(ad); st.success("Ad publish ho gaya ✅"); st.rerun()
    with t3:
        live = [a for a in S.ads if a["status"] == "Live"]
        st.caption("Yeh woh page hai jo candidate dekhta hai. Yahan se apply karne par CV seedha pipeline mein aati hai aur automation chalti hai.")
        if not live:
            st.info("Koi live ad nahi.")
        else:
            for ad in live:
                j = get_job(ad["job_id"])
                st.markdown(f"<div class='adcard'><h4>{j['title']}</h4><span class='ch'>{j['dept']} · {j['location']} · apply before {j['deadline']:%d %b}</span><br>"
                            + chips(j["must"], "g") + "</div>", unsafe_allow_html=True)
            with st.form("apply_form", clear_on_submit=True):
                st.markdown("##### Apply now")
                jid = st.selectbox("Position", [a["job_id"] for a in live], format_func=lambda i: get_job(i)["title"])
                c1, c2, c3 = st.columns(3)
                nm, em, ph = c1.text_input("Full name"), c2.text_input("Email"), c3.text_input("Phone")
                c4, c5, c6, c7 = st.columns(4)
                city = c4.selectbox("City", CITIES)
                exp = c5.number_input("Experience (yrs)", 0.0, 40.0, 2.0)
                edu = c6.selectbox("Education", list(EDU), index=2, format_func=lambda k: EDU[k])
                exs = c7.number_input("Expected salary (PKR)", 0, 3000000, 90000, 5000)
                sk = st.multiselect("Skills", SKILLS)
                src = st.selectbox("How did you hear about us?", SOURCES)
                f = st.file_uploader("Upload CV (optional)", type=["pdf", "docx", "txt"])
                if st.form_submit_button("Submit application", type="primary"):
                    if not (nm and em):
                        st.error("Name aur email zaroori hain.")
                    else:
                        j = get_job(jid)
                        parsed = parse_cv(f.name, f.read()) if f else {}
                        skills = sorted(set(sk) | set(parsed.get("skills", "").split("|")) - {""})
                        row = new_row(name=nm, email=em.strip().lower(), phone=ph, city=city, title="Applicant", dept=j["dept"], exp=float(exp),
                                      edu=int(edu), salary=int(exs), skills="|".join(skills), source=src, job_id=jid)
                        ids = add_candidates(pd.DataFrame([row]))
                        if not ids:
                            st.warning("Is email se application pehle hi maujood hai.")
                        else:
                            if S.auto["run_on_import"]:
                                run_automation()
                            st.success(f"Application receive ho gayi. Reference ID: XL-{ids[0]:05d}. Acknowledgement email bhej di gayi.")
    with t4:
        rows = []
        for ch in CHANNELS:
            sub = S.df[S.df["source"] == ch]
            views = sum(a["views"].get(ch, 0) for a in S.ads)
            rows.append({"Channel": ch, "Views": views, "Applications": len(sub), "Shortlisted+": int(sub["stage"].isin(ADV_STAGES).sum()),
                         "Hired": int((sub["stage"] == "Hired").sum()), "Avg AI score": round(float(sub["score"].mean()), 1) if sub["score"].notna().any() else None})
        d = pd.DataFrame(rows)
        st.dataframe(d, hide_index=True)
        st.bar_chart(d.set_index("Channel")[["Applications", "Shortlisted+", "Hired"]])


def page_cvdb():
    header("CV Database", f"{len(S.df):,} CVs · New vs Existing, date/subject filters, bulk import, duplicates")
    nm = new_mask(S.df)
    k = st.columns(4)
    for col, (l, v, t) in zip(k, [("Total CVs", f"{len(S.df):,}", "k1"), ("New CVs", f"{int(nm.sum()):,}", "k2"),
                                  ("Existing CVs", f"{int((~nm).sum()):,}", "k3"),
                                  ("Talent pool", f"{int((S.df['stage'] == 'Talent Pool').sum()):,}", "k4")]):
        col.markdown(kpi(l, v, f"'New' = last {S.settings['new_days']} days" if l == "New CVs" else "", t), unsafe_allow_html=True)
    st.write("")
    t1, t2, t3 = st.tabs(["🔍 Search & manage", "⬆ Import CVs", "👯 Duplicates"])
    with t1:
        with st.container(border=True):
            sub = cv_filters("db_")
        ps = st.selectbox("Rows per page", [25, 50, 100], key="db_ps")
        pages = max(1, -(-len(sub) // ps))
        pg = st.number_input("Page", 1, pages, 1, key="db_pg")
        view = sub.iloc[(pg - 1) * ps: pg * ps]
        st.dataframe(view_df(view), hide_index=True, column_config={"Match %": PROG, **SAL_CFG})
        a, b, c_ = st.columns([2, 1, 2])
        tgt = a.selectbox("Bulk move ALL filtered CVs to", STAGES, index=1, key="db_tg")
        ok = b.checkbox("Confirm", key="db_ok")
        if c_.button(f"Apply to {len(sub):,} CVs", disabled=not ok or sub.empty):
            move(sub.index, tgt, "Bulk action (CV Database)", email=None); st.rerun()
        st.download_button("⬇ Export filtered (CSV)", view_df(sub).to_csv(index=False), "cv_export.csv")
        if len(view):
            pick = st.selectbox("Open CV", list(view.index), format_func=cname, key="db_pick")
            with st.container(border=True):
                candidate_card(pick, "db")
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Upload CVs (PDF / DOCX / TXT)")
            files = st.file_uploader("Multiple files allowed", type=["pdf", "docx", "txt"], accept_multiple_files=True)
            assign = st.selectbox("Assign to position", ["Auto-assign best matching job"] + [f"{j['id']} - {j['title']}" for j in S.jobs if j["status"] == "Open"])
            if files and st.button("Parse & import", type="primary"):
                rows, bar = [], st.progress(0.0)
                for i, f in enumerate(files):
                    rows.append(parse_cv(f.name, f.read()))
                    bar.progress((i + 1) / len(files))
                ids = add_candidates(pd.DataFrame(rows))
                if ids:
                    finish_import(ids, assign)
                st.success(f"{len(ids)} CV import hui ({len(files) - len(ids)} duplicate skip).")
        with c2:
            st.markdown("##### Simulate bulk inflow (portal / email import)")
            n = st.number_input("How many new CVs?", 50, 10000, 500, 50)
            if st.button("📥 Generate & auto-process"):
                by_dept = {}
                for j in S.jobs:
                    if j["status"] == "Open":
                        by_dept.setdefault(j["dept"], []).append(j["id"])
                new = generate_cvs(int(n), int(S.df.index.max()) + 1, random.randint(1, 10 ** 6), max_age=0, jobs_by_dept=by_dept, fresh=True)
                new["acked"], new["stage"] = False, "Applied"
                open_ids = [j["id"] for j in S.jobs if j["status"] == "Open"]
                z = new["job_id"] == 0
                new.loc[z, "job_id"] = [random.choice(open_ids) for _ in range(int(z.sum()))]
                ids = add_candidates(new)
                if S.auto["run_on_import"]:
                    run_automation()
                st.success(f"{len(ids):,} CVs aaye aur automation ne process kar di (Dashboard dekhein).")
    with t3:
        d = S.df[S.df["email"].duplicated(keep=False)].sort_values("email")
        st.write(f"**{len(d)}** duplicate rows found (same email).")
        if not d.empty:
            st.dataframe(view_df(d).assign(Email=d["email"].values), hide_index=True)
            if st.button("🧹 Remove duplicates (keep earliest)"):
                S.df = S.df[~S.df["email"].duplicated(keep="first")]
                rebuild_matrix(); st.rerun()


# =============================================================================
# PAGES - SCREENING
# =============================================================================
def page_matching():
    header("AI Talent Matching", "Bohat saari CVs aaein to AI khud best CVs recommend karta hai (expected salary ke sath)")
    jobs = [j for j in S.jobs if j["status"] != "Closed"]
    ids = [j["id"] for j in jobs]
    idx = ids.index(S.mj_pref) if S.mj_pref in ids else 0
    jid = st.selectbox("Select position", ids, index=idx, format_func=lambda i: f"{get_job(i)['title']} · {get_job(i)['dept']} · {get_job(i)['status']}")
    S.mj_pref = jid
    job = get_job(jid)
    c1, c2, c3, c4 = st.columns([1.5, 1.6, 1.5, 1])
    scope = c1.radio("Scan", ["Applicants of this job", "Entire CV database"], key=f"sc_{jid}")
    ctype = c2.radio("CV type", ["All", "New", "Existing"], horizontal=True, key=f"mct_{jid}")
    when = c3.selectbox("Date applied", ["Any time", "Today", "Last 7 days", "Last 30 days", "This month"], key=f"mwh_{jid}")
    topn = c4.slider("Show top", 10, 200, 50, 10, key=f"tn_{jid}")
    stg = st.multiselect("Include stages", STAGES, default=["Applied", "Talent Pool", "Shortlisted", "On Hold"], key=f"stg_{jid}")
    with st.expander("⚙️ Scoring weights & knockout rules"):
        wc = st.columns(5)
        w = {k: wc[i].slider(k.title(), 0, 100, int(job["weights"][k]), key=f"w_{jid}_{k}") for i, k in enumerate(DEFAULT_WEIGHTS)}
        k1, k2, k3 = st.columns(3)
        min_must = k1.slider("Min must-have skill coverage %", 0, 100, int(job["min_must"] * 100), key=f"mm_{jid}") / 100
        cities = k2.multiselect("Only cities", CITIES, key=f"ct_{jid}")
        cap = k3.checkbox("Exclude if expected salary > budget +10%", key=f"cap_{jid}")
    t0 = time.perf_counter()
    sc, must, _ = score_vec(job, w)
    df = S.df
    mask = df["stage"].isin(stg).to_numpy(copy=True)
    if scope.startswith("Applicants"):
        mask &= (df["job_id"].values == jid)
    if ctype != "All":
        mask &= new_mask(df) if ctype == "New" else ~new_mask(df)
    mask &= date_mask(df, when)
    if cities:
        mask &= df["city"].isin(cities).values
    if cap:
        mask &= df["salary"].values <= job["sal_max"] * 1.1
    res = pd.DataFrame({"score": sc, "must": must * 100}, index=df.index)[mask]
    res["ko"] = res["must"] < min_must * 100
    res = res.sort_values("score", ascending=False)
    ms = (time.perf_counter() - t0) * 1000
    k = st.columns(5)
    for col, (l, v) in zip(k, [("CVs scanned", f"{int(mask.sum()):,}"), ("Excellent (≥85)", int((res["score"] >= 85).sum())),
                               ("Good (70-85)", int(((res["score"] >= 70) & (res["score"] < 85)).sum())),
                               ("Knockouts", int(res["ko"].sum())), ("Match time", f"{ms:.0f} ms")]):
        col.metric(l, v)
    top = res.head(topn)
    if not top.empty:
        best = top.index[0]
        bc = S.df.loc[best]
        st.success(f"🏆 **AI recommends: {bc['name']}** - {top['score'].iloc[0]:.0f}% match · expects PKR {bc['salary']:,} "
                   f"(AI market estimate {sal_range(bc['ai_salary'])}) · budget PKR {job['sal_min']:,} - {job['sal_max']:,}")
    tabs = st.tabs(["🏆 Ranked candidates", "🤖 Recommendation board (all jobs)", "👤 Deep-dive", "⚖️ Compare"])
    with tabs[0]:
        if top.empty:
            st.warning("Is filter par koi candidate nahi mila.")
        else:
            h = np.histogram(res["score"], bins=list(range(0, 101, 10)))[0]
            st.bar_chart(pd.Series(h, index=[f"{a}-{a + 10}" for a in range(0, 100, 10)]), height=130)
            sub = S.df.loc[top.index]
            tbl = pd.DataFrame({"Select": False, "ID": top.index, "Rank": range(1, len(top) + 1), "Name": sub["name"].values,
                                "Title": sub["title"].values, "CV Type": np.where(new_mask(sub), "New", "Existing"),
                                "Exp": sub["exp"].values, "Education": sub["edu"].map(EDU).values, "City": sub["city"].values,
                                "Expected Salary": sub["salary"].values, "AI Est. Salary": sub["ai_salary"].values,
                                "Budget": np.where(sub["salary"].values <= job["sal_max"], "Within", "Above"),
                                "Match %": top["score"].round(1).values, "Must-have %": top["must"].round(0).values,
                                "Flag": np.where(top["ko"], "⚠ must-have gap", "OK"), "Stage": sub["stage"].values})
            ed = st.data_editor(tbl, hide_index=True, key=f"med_{jid}_{S.ver}_{topn}", column_config={"Match %": PROG, **SAL_CFG},
                                disabled=[c for c in tbl.columns if c != "Select"])
            sel = [int(i) for i in ed.loc[ed["Select"], "ID"]]
            st.caption(f"{len(sel)} selected")
            b = st.columns(5)
            if b[0].button("⭐ Shortlist selected", disabled=not sel):
                shortlist(sel, f"AI Matching: {job['title']}", job_id=jid); st.rerun()
            if b[1].button("📤 Forward to dept", disabled=not sel):
                S.df.loc[sel, "job_id"] = jid
                forward_to_dept(sel); st.rerun()
            if b[2].button("✉ Invite from pool", disabled=not sel):
                S.df.loc[sel, "job_id"] = jid
                move(sel, "Shortlisted", "Invited from talent pool", email="Invite to apply"); st.rerun()
            why = b[3].selectbox("Reject reason", REJECT_REASONS, label_visibility="collapsed")
            if b[3].button("✖ Reject selected", disabled=not sel):
                reject(sel, why); st.rerun()
            kk = b[4].number_input("Top K", 1, 100, 10, label_visibility="collapsed")
            if b[4].button(f"🚀 Auto-shortlist top {kk}"):
                cand = top[(~top["ko"]) & S.df.loc[top.index, "stage"].isin(["Applied", "Talent Pool"])].head(kk).index
                n = shortlist(list(cand), f"Auto top-{kk}: {job['title']}", job_id=jid)
                ev(f"{len(cand)} candidates auto-shortlisted for {job['title']}", "success"); st.rerun()
            st.download_button("⬇ Export ranked list (CSV)", tbl.drop(columns="Select").to_csv(index=False), f"ranked_{job['title'].replace(' ', '_')}.csv")
    with tabs[1]:
        st.caption("Har open position ke liye poori database mein se top 3 CVs (non-rejected, non-hired).")
        avail = (~S.df["stage"].isin(["Rejected", "Hired"])).values
        for j in [x for x in S.jobs if x["status"] == "Open"]:
            s2, m2, _ = score_vec(j)
            r = pd.DataFrame({"score": s2, "must": m2}, index=S.df.index)[avail & (m2 >= j["min_must"])].sort_values("score", ascending=False).head(3)
            with st.expander(f"{j['title']} · {j['dept']} · best: {r['score'].iloc[0]:.0f}%" if len(r) else f"{j['title']} · no qualified CV", expanded=False):
                if len(r):
                    st.dataframe(view_df(S.df.loc[r.index]).assign(**{"Match %": r["score"].round(0).values})[["Name", "Title", "CV Type", "Exp", "Expected Salary", "AI Est. Salary", "Stage", "Match %"]],
                                 hide_index=True, column_config={"Match %": PROG, **SAL_CFG})
                    if st.button(f"Shortlist these {len(r)}", key=f"bd_{j['id']}"):
                        shortlist(list(r.index), f"Recommendation board: {j['title']}", job_id=j["id"]); st.rerun()
    with tabs[2]:
        if top.empty:
            st.info("Koi candidate nahi.")
        else:
            pick = st.selectbox("Open candidate", list(top.index[:50]), format_func=lambda i: f"{cname(i)} · {top.at[i, 'score']:.0f}%", key=f"pk_{jid}")
            candidate_card(pick, "mt", job)
    with tabs[3]:
        cmp_ids = st.multiselect("Pick 2-3 candidates", list(top.index[:50]), max_selections=3, format_func=cname, key=f"cmp_{jid}")
        if len(cmp_ids) >= 2:
            rows = {}
            for i in cmp_ids:
                ex = explain(i, job, w)
                c = S.df.loc[i]
                rows[c["name"]] = {"Match %": round(ex["score"], 1), "Experience": f"{c['exp']} yrs", "Education": EDU[c["edu"]],
                                   "Must-have": f"{len(ex['mm'])}/{len(job['must'])}", "Missing": ", ".join(ex["mx"]) or "-",
                                   "Nice-to-have": f"{len(ex['nm'])}/{len(job['nice'])}", "Expected salary": f"PKR {c['salary']:,}",
                                   "AI market estimate": f"PKR {c['ai_salary']:,}", "Budget fit": "Within" if c["salary"] <= job["sal_max"] else "Above",
                                   "City": c["city"], "Stage": c["stage"]}
            st.dataframe(pd.DataFrame(rows))


def page_pipeline():
    header("Candidate Pipeline", "Stage-wise tracking, board view & bulk moves")
    df = S.df
    top = st.columns([2, 1.2, 1.6])
    jf = top[0].selectbox("Position", [0] + [j["id"] for j in S.jobs], format_func=lambda i: "All positions" if i == 0 else get_job(i)["title"])
    ctype = top[1].radio("CV type", ["All", "New", "Existing"], horizontal=True, key="pl_ct")
    view = top[2].radio("View", ["Board", "Table"], horizontal=True)
    base = df if jf == 0 else df[df["job_id"] == jf]
    if ctype != "All":
        base = base[new_mask(base)] if ctype == "New" else base[~new_mask(base)]
    cnt = base["stage"].value_counts()
    cols = st.columns(len(STAGES))
    for c, s in zip(cols, STAGES):
        c.metric(s, f"{int(cnt.get(s, 0)):,}")
    if view == "Board":
        board = [("Shortlisted", "Forward →"), ("Dept Review", "Approve →"), ("Interview", "To offer →"), ("Offer", "Open offers"), ("Hired", None)]
        for col, (stg, btn) in zip(st.columns(5), board):
            sub = base[base["stage"] == stg].sort_values("score", ascending=False)
            col.markdown(f"**{stg}** · {len(sub)}")
            for cid, r in sub.head(6).iterrows():
                with col.container(border=True):
                    st.markdown(f"**{r['name']}**  \n<small>{r['title']} · {pct(r['score'])}</small>", unsafe_allow_html=True)
                    if btn and st.button(btn, key=f"bd_{stg}_{cid}"):
                        if stg == "Shortlisted":
                            forward_to_dept([cid])
                        elif stg == "Dept Review":
                            h = next((x for x in S.handoffs if x["cid"] == cid and x["status"] == "Pending"), None)
                            if h:
                                dept_decide(h["id"], "Approved", "Approved from board")
                        elif stg == "Interview":
                            move([cid], "Offer", "Interview passed", email=None)
                        else:
                            goto("Offers & Onboarding")
                        st.rerun()
        st.caption("Har column ke top 6 dikhaye gaye hain. Poori list ke liye 'Table' view use karein.")
        return
    stage = st.radio("Stage", STAGES, horizontal=True, index=2)
    sub = base[base["stage"] == stage].sort_values("score", ascending=False)
    if stage == "Applied":
        if st.checkbox("Only borderline CVs needing manual review (already screened)", True):
            sub = sub[sub["score"].notna()]
    st.caption(f"Showing top 200 of {len(sub):,}")
    v = view_df(sub.head(200))
    v.insert(0, "Select", False)
    ed = st.data_editor(v, hide_index=True, key=f"pl_{stage}_{jf}_{ctype}_{S.ver}", column_config={"Match %": PROG, **SAL_CFG},
                        disabled=[c for c in v.columns if c != "Select"])
    sel = [int(i) for i in ed.loc[ed["Select"], "ID"]]
    a, b, c_ = st.columns([2, 1.5, 1.5])
    tgt = a.selectbox("Move selected to", [s for s in STAGES if s != stage], key="pl_tg")
    mail = b.checkbox("Send email", True)
    if c_.button(f"Move {len(sel)} candidate(s)", disabled=not sel, type="primary"):
        if tgt == "Rejected":
            reject(sel, "Bulk move (Pipeline)")
        elif tgt == "Dept Review":
            forward_to_dept(sel)
        else:
            move(sel, tgt, "Pipeline bulk move", email="auto" if mail else None)
        st.rerun()
    if len(sub):
        pick = st.selectbox("Open profile", list(sub.head(200).index), format_func=lambda i: f"{cname(i)} · {pct(sub.at[i, 'score'])}", key="pl_pick")
        with st.container(border=True):
            candidate_card(pick, "pl")


# =============================================================================
# PAGES - SELECTION
# =============================================================================
def page_handoff():
    header("Department Handoff", "HR accept > Department ko forward > Department approve/decline > Interview")
    t1, t2, t3 = st.tabs(["📤 Forward to department", "📥 Department inbox", "📋 Tracking"])
    with t1:
        jobs = [j for j in S.jobs if j["status"] == "Open"]
        jid = st.selectbox("Position", [j["id"] for j in jobs], format_func=lambda i: f"{get_job(i)['title']} → {DEPT_HEADS[get_job(i)['dept']][0]} ({get_job(i)['dept']})", key="hf_job")
        sub = S.df[(S.df["job_id"] == jid) & (S.df["stage"] == "Shortlisted")].sort_values("score", ascending=False)
        st.caption(f"{len(sub)} HR-shortlisted candidates not yet forwarded. (Automation mein 'auto-forward' on ho to yeh khud chala jata hai.)")
        if sub.empty:
            st.info("Koi shortlisted candidate pending nahi.")
        else:
            v = view_df(sub.head(100))[["ID", "Name", "Title", "CV Type", "Exp", "Expected Salary", "AI Est. Salary", "Match %"]]
            v.insert(0, "Select", False)
            ed = st.data_editor(v, hide_index=True, key=f"hf_{jid}_{S.ver}", column_config={"Match %": PROG, **SAL_CFG},
                                disabled=[c for c in v.columns if c != "Select"])
            sel = [int(i) for i in ed.loc[ed["Select"], "ID"]]
            note = st.text_input("Note for department head (optional)")
            a, b = st.columns(2)
            if a.button(f"📤 Forward selected ({len(sel)})", disabled=not sel, type="primary"):
                forward_to_dept(sel, note); st.rerun()
            if b.button(f"📤 Forward all {len(sub)}"):
                forward_to_dept(list(sub.index), note); st.rerun()
    with t2:
        dsel = st.selectbox("Acting as department", ["All"] + DEPTS, key="hf_dept")
        pend = [h for h in S.handoffs if h["status"] == "Pending" and (dsel == "All" or h["dept"] == dsel)]
        st.write(f"**{len(pend)}** candidate(s) waiting for review")
        for h in pend[:25]:
            c, job = S.df.loc[h["cid"]], get_job(h["job_id"])
            with st.container(border=True):
                a, b = st.columns([3, 2])
                ex = explain(h["cid"], job)
                a.markdown(f"**{c['name']}** · {c['title']} · {c['exp']} yrs  \n{job['title']} ({h['dept']}) · sent {h['sent_on']:%d %b} to {h['head']}")
                a.markdown(chips(ex["mm"], "g") + chips(ex["mx"], "r"), unsafe_allow_html=True)
                b.markdown(f"<span style='font-size:26px;font-weight:700'>{ex['score']:.0f}%</span> match<br>"
                           f"Expects PKR {c['salary'] / 1000:,.0f}K · AI est. {c['ai_salary'] / 1000:,.0f}K · budget {job['sal_min'] // 1000}-{job['sal_max'] // 1000}K",
                           unsafe_allow_html=True)
                x = st.columns([1.3, 1.3, 1, 2.4])
                cm = x[3].text_input("Comment", key=f"hc_{h['id']}", label_visibility="collapsed", placeholder="Comment (optional)")
                if x[0].button("✔ Approve", key=f"ha_{h['id']}", type="primary"):
                    dept_decide(h["id"], "Approved", cm); st.rerun()
                with x[1].popover("✖ Decline"):
                    rs = st.selectbox("Reason", REJECT_REASONS, key=f"hr_{h['id']}")
                    st.caption("Candidate ko regret email jayegi.")
                    if st.button("Confirm decline", key=f"hd_{h['id']}"):
                        dept_decide(h["id"], "Declined", rs); st.rerun()
                if x[2].button("⏸ Hold", key=f"hh_{h['id']}"):
                    dept_decide(h["id"], "On Hold", cm); st.rerun()
    with t3:
        if not S.handoffs:
            st.info("Abhi koi handoff nahi.")
        else:
            d = pd.DataFrame([dict(ID=h["id"], Candidate=cname(h["cid"]), Position=get_job(h["job_id"])["title"], Department=h["dept"],
                                   Head=h["head"], Status=h["status"], Sent=h["sent_on"], Decided=h["decided_on"],
                                   Days=((h["decided_on"] or TODAY) - h["sent_on"]).days, Comment=h["comment"]) for h in S.handoffs])
            f = st.multiselect("Status", ["Pending", "Approved", "Declined", "On Hold"], default=["Pending", "Approved", "Declined", "On Hold"])
            d = d[d["Status"].isin(f)]
            m = st.columns(4)
            m[0].metric("Pending", int((d["Status"] == "Pending").sum()))
            m[1].metric("Approved", int((d["Status"] == "Approved").sum()))
            m[2].metric("Declined", int((d["Status"] == "Declined").sum()))
            m[3].metric("Avg days to decide", f"{d[d['Status'] != 'Pending']['Days'].mean():.1f}" if (d["Status"] != "Pending").any() else "-")
            st.dataframe(d, hide_index=True)


def page_interviews():
    header("Interview Management", "Schedule · Panel · Online links · Scorecards · Reminders")
    t1, t2, t3 = st.tabs(["📆 Agenda", "➕ Schedule", "📝 Scorecards & ranking"])
    with t1:
        if st.button("🔔 Send due reminders (next %dh)" % S.auto["reminder_hours"]):
            st.success(f"{send_due_reminders()} reminder bheje gaye")
        up = sorted([iv for iv in S.interviews if iv["status"] == "Scheduled"], key=lambda x: (x["date"], x["time"]))
        st.write(f"**{len(up)}** upcoming")
        last = None
        for iv in up:
            if iv["date"] != last:
                st.markdown(f"##### {iv['date']:%A, %d %B}")
                last = iv["date"]
            with st.container(border=True):
                a, b, d = st.columns([4, 2, 2.5])
                a.markdown(f"**{iv['time']}** · {cname(iv['cid'])} · {iv['round']} · {iv['mode']}  \nPanel: {', '.join(iv['panel'])}"
                           + (f"  \n<small>{iv['link']}</small>" if iv.get("link") else ""), unsafe_allow_html=True)
                if b.button("✔ Completed", key=f"ic_{iv['id']}"):
                    iv["status"] = "Completed"; st.rerun()
                if d.button("✖ Cancel", key=f"ix_{iv['id']}"):
                    iv["status"] = "Cancelled"; st.rerun()
    with t2:
        wait = awaiting_schedule()
        st.markdown(f"##### Department-approved, interview slot pending: **{len(wait)}**")
        jobs = [j for j in S.jobs if j["status"] == "Open"]
        b = st.columns(5)
        jid = b[0].selectbox("Position", [j["id"] for j in jobs], format_func=lambda i: get_job(i)["title"], key="as_j")
        rnd2 = b[1].selectbox("Round", ROUNDS, key="as_r")
        start = b[2].date_input("Start date", TODAY + timedelta(days=1), key="as_d")
        mins = b[3].selectbox("Slot (mins)", [30, 45, 60], index=1)
        mode2 = b[4].selectbox("Mode", ["Onsite", "Online", "Phone"], index=1, key="as_m")
        pn2 = st.multiselect("Panel", PANEL, default=[DEPT_HEADS[get_job(jid)["dept"]][0], S.settings["user"]], key=f"as_p_{jid}")
        sl = wait[wait["job_id"] == jid].sort_values("score", ascending=False)
        st.caption(f"{len(sl)} candidate(s) · slots 10:00-17:00, lunch 13-14, weekends skipped, panel conflicts avoided, Teams link auto-generated for Online")
        if st.button(f"📅 Auto-schedule {len(sl)} candidates", disabled=sl.empty or not pn2, type="primary"):
            n = auto_schedule(list(sl.index), rnd2, start, pn2, mode2, mins)
            ev(f"{n} interviews auto-scheduled for {get_job(jid)['title']}", "success")
            st.success(f"{n} interviews schedule + invitations sent"); st.rerun()
        st.divider()
        st.markdown("##### Single interview")
        pool = S.df[S.df["stage"].isin(["Interview", "Shortlisted"])].sort_values("score", ascending=False).head(300)
        if pool.empty:
            st.info("Pehle candidates shortlist karein.")
        else:
            a = st.columns(5)
            cid = a[0].selectbox("Candidate", list(pool.index), format_func=lambda i: f"{cname(i)} ({pct(S.df.at[i, 'score'])})")
            rnd = a[1].selectbox("Round", ROUNDS)
            d = a[2].date_input("Date", TODAY + timedelta(days=2))
            t = a[3].time_input("Time", datetime.strptime("11:00", "%H:%M").time())
            mode = a[4].selectbox("Mode", ["Onsite", "Online", "Phone"])
            pn = st.multiselect("Panel", PANEL, default=PANEL[:2])
            ts = t.strftime("%H:%M")
            cf = conflicts_for(d, ts, pn)
            if cf:
                st.warning("Conflict: " + ", ".join(set(sum([c["panel"] for c in cf], [])) & set(pn)) + " already has an interview at this time.")
            if st.button("Schedule & notify", disabled=bool(cf)):
                schedule_interview(cid, rnd, d, ts, mode, pn); st.success("Scheduled ✅"); st.rerun()
    with t3:
        crit = ["Technical", "Communication", "Problem Solving", "Culture Fit"]
        pend = [iv for iv in S.interviews if iv["status"] == "Completed" and iv["scores"] is None]
        for iv in pend:
            with st.form(f"sc_{iv['id']}"):
                st.markdown(f"**{cname(iv['cid'])}** · {iv['round']}")
                cols = st.columns(4)
                sc = {k: cols[i].slider(k, 1, 5, 3) for i, k in enumerate(crit)}
                rec = st.selectbox("Recommendation", ["Strong Hire", "Hire", "Hold", "No Hire"], index=1)
                cm = st.text_input("Comments")
                if st.form_submit_button("Save scorecard"):
                    iv.update(scores=sc, rec=rec, comment=cm); st.rerun()
        done = [iv for iv in S.interviews if iv["scores"]]
        if done:
            rows = []
            for iv in done:
                avg = np.mean(list(iv["scores"].values()))
                ai = S.df.at[iv["cid"], "score"]
                rows.append({"ID": iv["cid"], "Candidate": cname(iv["cid"]), "Round": iv["round"], "Interview avg (1-5)": round(avg, 2),
                             "AI match %": ai, "Recommendation": iv["rec"],
                             "Combined": round((0.5 * (ai if pd.notna(ai) else 60)) + 0.5 * avg / 5 * 100, 1)})
            r = pd.DataFrame(rows).sort_values("Combined", ascending=False)
            st.dataframe(r, hide_index=True)
            hire = [int(i) for i, rc in zip(r["ID"], r["Recommendation"]) if rc in ("Strong Hire", "Hire") and S.df.at[i, "stage"] == "Interview"]
            c1, c2 = st.columns(2)
            if c1.button(f"💼 Move {len(hire)} recommended candidate(s) to Offer", disabled=not hire, type="primary"):
                move(hire, "Offer", "Interview recommended", email=None); st.rerun()
            nohire = [int(i) for i, rc in zip(r["ID"], r["Recommendation"]) if rc == "No Hire" and S.df.at[i, "stage"] == "Interview"]
            if c2.button(f"✖ Reject {len(nohire)} 'No Hire' candidate(s) (notify)", disabled=not nohire):
                reject(nohire, "Not selected after interview"); st.rerun()


def page_offers():
    header("Offers & Onboarding", "Offer letter > Acceptance > Employee record > Onboarding checklist")
    t1, t2, t3 = st.tabs(["💼 Offers", "✅ Onboarding", "👥 Employees"])
    with t1:
        noffer = S.df[(S.df["stage"] == "Offer") & (~S.df.index.isin([o["cid"] for o in S.offers if o["status"] in ("Draft", "Sent")]))]
        for cid in noffer.index[:20]:
            job = get_job(int(S.df.at[cid, "job_id"]))
            if not job:
                continue
            with st.form(f"of_{cid}"):
                st.markdown(f"**Create offer: {cname(cid)}** · {job['title']} · expects PKR {S.df.at[cid, 'salary']:,} · AI est. PKR {S.df.at[cid, 'ai_salary']:,} · budget PKR {job['sal_min']:,}-{job['sal_max']:,}")
                a, b = st.columns(2)
                sal = a.number_input("Monthly salary (PKR)", 0, 3000000, suggested_offer(S.df.loc[cid], job), 5000)
                jn = b.date_input("Joining date", TODAY + timedelta(days=30))
                if st.form_submit_button("Generate & send offer"):
                    S.offers.append(dict(id=len(S.offers) + 1, cid=int(cid), job_id=job["id"], salary=sal, joining=jn, status="Sent",
                                         sent_on=TODAY, letter=offer_letter(cid, job, sal, jn)))
                    send_mail([cid], "Job offer", dict(salary=f"{sal:,}", joining=jn.strftime("%d %b %Y")))
                    emit("offer.sent", candidate_id=int(cid), job_id=job["id"], salary=sal, joining=jn)
                    persist("offer", [cid])
                    st.rerun()
        st.markdown("##### All offers")
        if not S.offers:
            st.info("Abhi koi offer nahi.")
        for o in S.offers:
            with st.container(border=True):
                a, b, c_, d = st.columns([3, 1.5, 2.5, 2])
                jb = get_job(o["job_id"])
                a.markdown(f"**{cname(o['cid'])}** · {jb['title'] if jb else ''}  \nPKR {o['salary']:,} · join {o['joining']:%d %b}")
                b.markdown(f"**{o['status']}**")
                d.download_button("📄 Letter", o["letter"], f"offer_{o['cid']}.txt", key=f"dl_{o['id']}")
                if o["status"] == "Sent":
                    x, y = c_.columns(2)
                    if x.button("✔ Accepted", key=f"oa_{o['id']}"):
                        o["status"] = "Accepted"
                        move([o["cid"]], "Hired", "Offer accepted")
                        make_employee(o["cid"], o["salary"], o["joining"])
                        ev(f"{cname(o['cid'])} accepted the offer 🎉", "success"); st.rerun()
                    if y.button("✖ Declined", key=f"od_{o['id']}"):
                        o["status"] = "Declined"
                        move([o["cid"]], "Talent Pool", "Offer declined", email=None)
                        emit("offer.declined", candidate_id=o["cid"], job_id=o["job_id"]); st.rerun()
    with t2:
        if not S.employees:
            st.info("Hired employees yahan onboarding checklist ke sath aayenge.")
        for e in S.employees:
            done = sum(e["tasks"].values())
            with st.expander(f"👤 {e['name']} · {e['title']} · {done}/{len(ONBOARD_TASKS)} done"):
                for t in ONBOARD_TASKS:
                    e["tasks"][t] = st.checkbox(t, e["tasks"][t], key=f"ob_{e['id']}_{t}")
                st.progress(sum(e["tasks"].values()) / len(ONBOARD_TASKS))
    with t3:
        st.dataframe(pd.DataFrame([{k: v for k, v in e.items() if k not in ("tasks", "cid")} for e in S.employees]), hide_index=True)


# =============================================================================
# PAGES - AUTOMATION
# =============================================================================
def page_automation():
    header("Automation Center", "Rules jo HR ka manual kaam khud karte hain")
    a = S.auto
    st.graphviz_chart("""digraph { rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#eaf1ff", fontsize=11];
      A [label="New CV\\n(portal / email / upload)"]; B [label="Acknowledgement\\nemail"]; C [label="AI scoring\\nvs job"];
      D [label="Score >= shortlist %\\n+ must-haves", fillcolor="#dcfce7"]; E [label="Score < reject %\\nor knockout", fillcolor="#fee2e2"];
      F [label="Borderline:\\nmanual review", fillcolor="#fef3c7"]; G [label="Shortlist email\\nto candidate"]; H [label="Regret email\\nto candidate"];
      I [label="Forward to\\ndepartment head", fillcolor="#cffafe"]; J [label="Dept approves?", shape=diamond, fillcolor="#ede9fe"];
      K [label="Auto-schedule\\ninterview"]; L [label="Reminders, offer,\\nonboarding"];
      A->B->C; C->D; C->E; C->F; D->G->I->J; J->K [label="yes"]; J->H [label="no"]; E->H; K->L; }""")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("##### Screening rules")
            a["shortlist_at"] = st.slider("Auto-shortlist if match ≥ %", 50, 100, a["shortlist_at"])
            a["reject_below"] = st.slider("Auto-reject if match < %", 0, 80, a["reject_below"])
            a["reject_knockout"] = st.checkbox("Reject if must-have coverage below job minimum", a["reject_knockout"])
            a["max_shortlist"] = st.number_input("Max shortlisted per job", 1, 200, a["max_shortlist"])
            a["pool_rest"] = st.checkbox("Move borderline CVs to Talent Pool automatically", a["pool_rest"])
    with c2:
        with st.container(border=True):
            st.markdown("##### Workflow & communication")
            a["auto_forward"] = st.checkbox("Auto-forward shortlisted candidates to department head", a["auto_forward"])
            a["auto_schedule"] = st.checkbox("Auto-schedule interview when department approves", a["auto_schedule"])
            a["send_emails"] = st.checkbox("Send candidate emails automatically (shortlist / reject / offer)", a["send_emails"])
            a["share_feedback"] = st.checkbox("Include rejection reason in candidate email", a["share_feedback"])
            a["ack"] = st.checkbox("Acknowledgement email on new application", a["ack"])
            a["notify_hr"] = st.checkbox("Notify HR of automation results", a["notify_hr"])
            a["run_on_import"] = st.checkbox("Run automation automatically after CV import / application", a["run_on_import"])
            r1, r2 = st.columns(2)
            a["reminder_hours"] = r1.number_input("Interview reminder (hours before)", 1, 72, a["reminder_hours"])
            a["followup_days"] = r2.number_input("Offer follow-up after (days)", 1, 14, a["followup_days"])
    x, y = st.columns([1, 1])
    rs = y.checkbox("Re-screen already scored applicants")
    if x.button("▶ Run automation now", type="primary"):
        with st.spinner("Processing..."):
            r = run_automation(rescreen=rs)
        st.success(f"{r['screened']:,} CVs screened in {r['seconds']}s · {r['shortlisted']} shortlisted · {r['forwarded']} forwarded · {r['rejected']} rejected")
    if S.autolog:
        st.markdown("##### Run history")
        st.dataframe(pd.DataFrame(S.autolog), hide_index=True)


def page_comm():
    header("Communication Center", "Templates · Bulk messaging · Outbox (candidate + internal)")
    t1, t2, t3 = st.tabs(["✉ Templates", "📣 Bulk message", "📤 Outbox"])
    with t1:
        key = st.selectbox("Template", list(S.templates))
        subj, body = S.templates[key]
        ns = st.text_input("Subject", subj, key=f"ts_{key}")
        nb = st.text_area("Body", body, height=240, key=f"tb_{key}")
        st.caption("Placeholders: {name} {job} {company} {date} {time} {mode} {link} {panel} {salary} {joining} {feedback_line} {dept} {count} {candidates}")
        if st.button("Save template"):
            S.templates[key] = (ns, nb); st.toast("Saved")
        st.markdown("**Preview**")
        kw = {**DEFAULT_KW, **dict(name="Ayesha Malik", job="Frontend Developer", company=S.settings["company"], date="Mon, 02 Nov",
                                   time="11:00", mode="Online", panel="Sadam Ahmed", salary="150,000", joining="01 Dec",
                                   link="Join link: https://teams.microsoft.com/...", dept="IT", count=3, candidates="- Ayesha Malik (92% match)")}
        st.code(render(ns, **kw) + "\n\n" + render(nb, **kw))
    with t2:
        c1, c2, c3 = st.columns(3)
        jf = c1.selectbox("Job", [0] + [j["id"] for j in S.jobs], format_func=lambda i: "All jobs" if i == 0 else get_job(i)["title"], key="bm_j")
        sf = c2.multiselect("Stage", STAGES, default=["Shortlisted"], key="bm_s")
        tp = c3.selectbox("Template", [t for t in S.templates if t not in INTERNAL_TEMPLATES], key="bm_t")
        aud = S.df[S.df["stage"].isin(sf)]
        if jf:
            aud = aud[aud["job_id"] == jf]
        st.write(f"Audience: **{len(aud):,}** candidates")
        if st.button("Send bulk message", disabled=aud.empty, type="primary"):
            send_mail(aud.index, tp); st.success(f"{len(aud):,} messages queued (simulated)")
    with t3:
        if not S.outbox:
            st.info("Outbox khali hai.")
        else:
            ob = pd.DataFrame(S.outbox)
            f1, f2 = st.columns(2)
            f = f1.multiselect("Type", sorted(ob["type"].unique()), key="ob_f")
            au = f2.multiselect("Audience", ["Candidate", "Internal"], key="ob_a")
            if f:
                ob = ob[ob["type"].isin(f)]
            if au:
                ob = ob[ob["audience"].isin(au)]
            st.metric("Messages", f"{len(ob):,}")
            st.dataframe(ob[["time", "audience", "to", "name", "type", "subject", "status"]].iloc[::-1].head(500), hide_index=True)
            if len(ob):
                i = st.number_input("Open message # (latest first)", 1, min(len(ob), 500), 1)
                m = ob.iloc[::-1].iloc[int(i) - 1]
                st.code(f"To: {m['to']}\nSubject: {m['subject']}\n\n{m['body']}")
            st.download_button("⬇ Export outbox", ob.to_csv(index=False), "outbox.csv")


# =============================================================================
# PAGES - INSIGHTS
# =============================================================================
def page_analytics():
    header("Analytics & Reports", "Funnel · channels · New vs Existing · department turnaround · salary")
    df = S.df
    nm = new_mask(df)
    fun = pd.Series({"Total CVs": len(df), "AI screened": int(df["score"].notna().sum()),
                     "Shortlisted+": int(df["stage"].isin(ADV_STAGES).sum()),
                     "Interview+": int(df["stage"].isin(["Interview", "Offer", "Hired"]).sum()),
                     "Offer+": int(df["stage"].isin(["Offer", "Hired"]).sum()), "Hired": int((df["stage"] == "Hired").sum())})
    tth = np.mean([(e["hired_on"] - e["applied"]).days for e in S.employees]) if S.employees else 0
    dec = [(h["decided_on"] - h["sent_on"]).days for h in S.handoffs if h["decided_on"]]
    k = st.columns(5)
    k[0].metric("Screen → shortlist", f"{fun['Shortlisted+'] / max(fun['AI screened'], 1) * 100:.1f}%")
    k[1].metric("Offer → hire", f"{fun['Hired'] / max(fun['Offer+'], 1) * 100:.0f}%")
    k[2].metric("Avg time-to-hire", f"{tth:.0f} days")
    k[3].metric("Dept avg decision", f"{np.mean(dec):.1f} days" if dec else "-")
    k[4].metric("Hours saved (est.)", f"{int(df['score'].notna().sum() * 6 / 60):,} h")
    a, b = st.columns(2)
    a.markdown("##### Recruitment funnel"); a.bar_chart(fun)
    b.markdown("##### New vs Existing CVs by stage")
    b.bar_chart(pd.crosstab(df["stage"], np.where(nm, "New", "Existing")))
    c, d = st.columns(2)
    src = df.groupby("source").agg(Applications=("stage", "size"),
                                   Shortlisted=("stage", lambda s: int(s.isin(ADV_STAGES).sum())),
                                   Hired=("stage", lambda s: int((s == "Hired").sum())), AvgScore=("score", "mean")).round(1)
    c.markdown("##### Source / channel effectiveness"); c.dataframe(src)
    d.markdown("##### AI score distribution")
    d.bar_chart(pd.Series(np.histogram(df["score"].dropna(), bins=list(range(0, 101, 10)))[0], index=[f"{x}-{x + 10}" for x in range(0, 100, 10)]))
    e, f = st.columns(2)
    e.markdown("##### Applications by department"); e.bar_chart(df["dept"].value_counts())
    f.markdown("##### Talent scarcity - % CVs with required skills")
    req = sorted({s for j in S.jobs if j["status"] == "Open" for s in j["must"]})
    f.bar_chart(pd.Series({s: S.M[:, SK_IDX[s]].mean() * 100 for s in req}).sort_values())
    st.markdown("##### Salary analysis by department (expected vs AI market estimate vs budget)")
    sal = df.groupby("dept").agg(**{"Avg expected": ("salary", "mean"), "Avg AI estimate": ("ai_salary", "mean")}).round(0)
    sal["Avg budget (open jobs)"] = pd.Series({d_: np.mean([(j["sal_min"] + j["sal_max"]) / 2 for j in S.jobs if j["dept"] == d_]) for d_ in DEPTS if any(j["dept"] == d_ for j in S.jobs)})
    st.dataframe(sal, column_config={c_: st.column_config.NumberColumn(format="PKR %d") for c_ in sal.columns})
    st.download_button("⬇ Export channel summary (CSV)", src.to_csv(), "recruitment_summary.csv")


def page_notifications():
    header("Notifications", "Smart alerts · activity feed · department responses")
    st.markdown("#### Smart alerts")
    for sev, txt, pg, jid, lbl in compute_alerts() or [("low", "No alerts", "Dashboard", None, "")]:
        st.markdown(f"{'🔴' if sev == 'high' else '🟡' if sev == 'med' else '🟢'} {txt}")
    st.markdown("#### Department responses")
    dec = [h for h in S.handoffs if h["status"] != "Pending"]
    if not dec:
        st.caption("Abhi koi response nahi.")
    for h in dec[-8:][::-1]:
        st.markdown(f"{'✅' if h['status'] == 'Approved' else '❌' if h['status'] == 'Declined' else '⏸'} **{h['dept']}** {h['status'].lower()} {cname(h['cid'])} {('· ' + h['comment']) if h['comment'] else ''}")
    st.markdown("#### Activity feed")
    if st.button("Mark all read"):
        for e in S.events:
            e["read"] = True
        st.rerun()
    for e in S.events[:100]:
        st.markdown(f"{'🔵' if not e['read'] else '⚪'} `{e['time']}` {e['text']}")


# =============================================================================
# PAGES - ADMIN (Azure / backend readiness)
# =============================================================================
EVENT_CATALOG = [
    ("job.created / job.approved", "Requisition banta / approve hota hai", "Logic App: approval workflow (Teams approval)"),
    ("job.published", "Ad channels par publish hota hai", "Azure Function: Rozee.pk / LinkedIn / Indeed APIs"),
    ("cv.received", "Nayi CV aati hai (portal/email/upload)", "Function: Blob upload + Document Intelligence parse + SQL insert"),
    ("cv.screened", "Automation ne batch screen kiya", "Azure OpenAI agent re-ranking of top N"),
    ("candidate.shortlisted", "HR / AI ne shortlist kiya", "ACS Email: shortlist mail"),
    ("candidate.rejected", "Candidate reject hua", "ACS Email: regret mail (candidate ko response)"),
    ("candidate.forwarded_to_department", "Department head ko forward hua", "Teams / Outlook adaptive card to department head"),
    ("department.approved / declined", "Department ne decision diya", "Service Bus -> schedule interview / send regret"),
    ("interview.scheduled", "Interview schedule hua", "Graph API: Outlook calendar + Teams meeting"),
    ("offer.sent / offer.declined", "Offer bheji / decline hui", "ACS Email + DocuSign / e-sign"),
    ("candidate.hired", "Candidate hire hua", "HRIS record + IT onboarding ticket + payroll"),
]
SCHEMA = {
    "Jobs": [("id", "INT IDENTITY PRIMARY KEY"), ("title", "NVARCHAR(120)"), ("dept", "NVARCHAR(40)"), ("location", "NVARCHAR(60)"),
             ("headcount", "INT"), ("must_have_skills", "NVARCHAR(MAX)"), ("nice_to_have_skills", "NVARCHAR(MAX)"),
             ("min_exp", "DECIMAL(4,1)"), ("max_exp", "DECIMAL(4,1)"), ("min_education", "TINYINT"), ("salary_min", "INT"),
             ("salary_max", "INT"), ("status", "NVARCHAR(30)"), ("deadline", "DATE"), ("hiring_manager", "NVARCHAR(120)")],
    "Candidates": [("id", "INT IDENTITY PRIMARY KEY"), ("name", "NVARCHAR(120)"), ("email", "NVARCHAR(160) UNIQUE"), ("phone", "NVARCHAR(30)"),
                   ("city", "NVARCHAR(60)"), ("title", "NVARCHAR(120)"), ("dept", "NVARCHAR(40)"), ("exp_years", "DECIMAL(4,1)"),
                   ("education_level", "TINYINT"), ("expected_salary", "INT"), ("ai_estimated_salary", "INT"), ("skills", "NVARCHAR(MAX)"),
                   ("source", "NVARCHAR(40)"), ("applied_on", "DATE"), ("stage", "NVARCHAR(30)"),
                   ("job_id", "INT NULL FOREIGN KEY REFERENCES Jobs(id)"), ("ai_score", "DECIMAL(5,1) NULL"),
                   ("cv_blob_url", "NVARCHAR(400) NULL"), ("notes", "NVARCHAR(MAX) NULL")],
    "JobAds": [("id", "INT IDENTITY PRIMARY KEY"), ("job_id", "INT FOREIGN KEY REFERENCES Jobs(id)"), ("headline", "NVARCHAR(200)"),
               ("body", "NVARCHAR(MAX)"), ("channels", "NVARCHAR(200)"), ("status", "NVARCHAR(20)"), ("posted_on", "DATE NULL"), ("expires_on", "DATE")],
    "Handoffs": [("id", "INT IDENTITY PRIMARY KEY"), ("candidate_id", "INT FOREIGN KEY REFERENCES Candidates(id)"),
                 ("job_id", "INT FOREIGN KEY REFERENCES Jobs(id)"), ("department", "NVARCHAR(40)"), ("head", "NVARCHAR(120)"),
                 ("status", "NVARCHAR(20)"), ("sent_on", "DATE"), ("decided_on", "DATE NULL"), ("comment", "NVARCHAR(400) NULL")],
    "Interviews": [("id", "INT IDENTITY PRIMARY KEY"), ("candidate_id", "INT FOREIGN KEY REFERENCES Candidates(id)"), ("round", "NVARCHAR(30)"),
                   ("date", "DATE"), ("time", "NVARCHAR(5)"), ("mode", "NVARCHAR(10)"), ("panel", "NVARCHAR(300)"), ("link", "NVARCHAR(300) NULL"),
                   ("status", "NVARCHAR(20)"), ("scorecard_json", "NVARCHAR(MAX) NULL"), ("recommendation", "NVARCHAR(20) NULL")],
    "Offers": [("id", "INT IDENTITY PRIMARY KEY"), ("candidate_id", "INT FOREIGN KEY REFERENCES Candidates(id)"), ("job_id", "INT"),
               ("salary", "INT"), ("joining_date", "DATE"), ("status", "NVARCHAR(20)"), ("sent_on", "DATE")],
    "Employees": [("id", "INT IDENTITY PRIMARY KEY"), ("candidate_id", "INT"), ("name", "NVARCHAR(120)"), ("title", "NVARCHAR(120)"),
                  ("dept", "NVARCHAR(40)"), ("join_date", "DATE"), ("salary", "INT"), ("onboarding_json", "NVARCHAR(MAX)")],
    "Outbox": [("id", "BIGINT IDENTITY PRIMARY KEY"), ("sent_at", "DATETIME2"), ("audience", "NVARCHAR(12)"), ("to_email", "NVARCHAR(160)"),
               ("type", "NVARCHAR(40)"), ("subject", "NVARCHAR(250)"), ("body", "NVARCHAR(MAX)"), ("status", "NVARCHAR(30)")],
    "EventLog": [("id", "BIGINT IDENTITY PRIMARY KEY"), ("at", "DATETIME2"), ("event", "NVARCHAR(60)"), ("payload_json", "NVARCHAR(MAX)")],
}
AGENT_SYSTEM_PROMPT = """You are the Xloop Recruitment Agent. Given a JOB and a CANDIDATE, return ONLY valid JSON:
{"match_score": 0-100, "must_have_matched": [...], "must_have_missing": [...], "recommendation": "shortlist|review|reject",
 "expected_salary_estimate": {"low": int, "high": int, "currency": "PKR"}, "summary": "2 short sentences"}
Rules: be objective, never use gender/religion/age/ethnicity, justify with skills, experience and salary fit only."""


def agent_request(cid, job):
    c = S.df.loc[cid]
    return {"task": "score_candidate",
            "job": {"id": job["id"], "title": job["title"], "department": job["dept"], "must_have": job["must"], "nice_to_have": job["nice"],
                    "min_experience": job["min_exp"], "max_experience": job["max_exp"], "min_education": EDU[job["edu_min"]],
                    "budget": {"min": job["sal_min"], "max": job["sal_max"], "currency": "PKR"}, "location": job["location"]},
            "candidate": {"id": int(cid), "name": c["name"], "title": c["title"], "experience_years": float(c["exp"]), "education": EDU[c["edu"]],
                          "city": c["city"], "skills": c["skills"].split("|"), "expected_salary": int(c["salary"]),
                          "cv_url": f"https://<storage>.blob.core.windows.net/cvs/{int(cid)}.pdf"}}


def agent_response(cid, job):
    ex = explain(cid, job)
    c = S.df.loc[cid]
    rec = "shortlist" if ex["score"] >= S.auto["shortlist_at"] and ex["must"] >= job["min_must"] else ("reject" if ex["score"] < S.auto["reject_below"] else "review")
    return {"match_score": round(ex["score"], 1), "must_have_matched": ex["mm"], "must_have_missing": ex["mx"], "recommendation": rec,
            "expected_salary_estimate": {"low": int(c["ai_salary"] * 0.92), "high": int(c["ai_salary"] * 1.08), "currency": "PKR"},
            "summary": ai_summary(c, job, ex).replace("**", "")}


def schema_ddl():
    out = []
    for t, cols in SCHEMA.items():
        out.append(f"CREATE TABLE {t} (\n" + ",\n".join(f"    {c} {d}" for c, d in cols) + "\n);")
    return "\n\n".join(out)


def page_integrations():
    header("Integrations & Backend Readiness", "Azure (agent, database, email, automation) connect karne ke liye sab kuch tayyar")
    st.info("Abhi app **simulation mode** mein hai. Neeche har cheez ka mapping hai ke backend lagate waqt kaun sa function replace hoga.")
    t1, t2, t3, t4, t5 = st.tabs(["☁ Azure connections", "📡 Event bus", "🤖 AI agent contract", "🗄 Database schema", "✅ Go-live checklist"])
    with t1:
        mapping = {"Azure OpenAI / AI Foundry (AI agent)": "score_vec(), ai_summary(), generate_ad()",
                   "Azure SQL / Cosmos DB (database)": "persist(), generate_cvs() -> repository layer",
                   "Azure Blob Storage (CV files)": "parse_cv() (file save) + cv_blob_url",
                   "Azure Communication Services (email/SMS)": "send_mail(), send_internal()",
                   "Azure Document Intelligence (CV parsing)": "parse_cv()",
                   "Azure Service Bus / Event Grid (automation)": "publish_event() / run_automation()",
                   "Microsoft Entra ID (login / roles)": "S.settings['role'] / ROLE_PAGES"}
        for svc, keys in AZURE_SERVICES.items():
            ok = all(cfg(k) for k in keys)
            with st.container(border=True):
                a, b, c_ = st.columns([3, 3, 1.5])
                a.markdown(f"**{svc}**  \nReplace: `{mapping[svc]}`")
                b.markdown("<br>".join(f"{'✅' if cfg(k) else '⚪'} `{k}`" for k in keys), unsafe_allow_html=True)
                if c_.button("Test connection", key=f"tc_{svc}"):
                    st.toast("Configured - test code abhi implement nahi" if ok else "Not configured: secrets.toml mein keys daalein")
        st.markdown("**`.streamlit/secrets.toml` example**")
        st.code("\n".join(f'{k} = "..."' for ks in AZURE_SERVICES.values() for k in ks), language="toml")
    with t2:
        st.caption("Har important action ek event emit karta hai (JSON). Inhe Azure Service Bus / Event Grid / Logic Apps se jorna hai.")
        st.dataframe(pd.DataFrame(EVENT_CATALOG, columns=["Event", "Kab", "Azure action (suggested)"]), hide_index=True)
        st.markdown(f"**Live event log** ({len(S.eventlog)} events)")
        if S.eventlog:
            names = sorted({e["event"] for e in S.eventlog})
            f = st.multiselect("Filter", names, key="ev_f")
            rows = [e for e in S.eventlog if not f or e["event"] in f][:200]
            st.dataframe(pd.DataFrame([dict(time=e["time"], event=e["event"], payload=json.dumps(e["payload"])[:180]) for e in rows]), hide_index=True)
            if rows:
                i = st.number_input("Show payload # (latest first)", 1, len(rows), 1)
                st.code(json.dumps(rows[int(i) - 1], indent=2), language="json")
        else:
            st.caption("Abhi koi event nahi. Koi action karein (shortlist / reject / forward).")
    with t3:
        st.markdown("**System prompt**")
        st.code(AGENT_SYSTEM_PROMPT)
        jobs = [j for j in S.jobs if j["status"] == "Open"]
        jid = st.selectbox("Job", [j["id"] for j in jobs], format_func=lambda i: get_job(i)["title"], key="ag_j")
        cands = S.df[S.df["job_id"] == jid].sort_values("score", ascending=False).head(30)
        if cands.empty:
            st.info("Is job par candidates nahi.")
        else:
            cid = st.selectbox("Candidate", list(cands.index), format_func=cname, key="ag_c")
            job = get_job(jid)
            c1, c2 = st.columns(2)
            c1.markdown("**Request (app -> Azure OpenAI agent)**"); c1.code(json.dumps(agent_request(cid, job), indent=2), language="json")
            c2.markdown("**Response (simulated; agent yehi format return kare)**"); c2.code(json.dumps(agent_response(cid, job), indent=2), language="json")
    with t4:
        ddl = schema_ddl()
        st.caption("Azure SQL ke liye tayyar DDL. App ke dataframes/dicts is schema se match karte hain.")
        st.code(ddl, language="sql")
        st.download_button("⬇ Download schema.sql", ddl, "schema.sql")
    with t5:
        st.markdown("""
1. **Database**: Azure SQL par `schema.sql` chalayen -> `persist()` aur data load functions likhein (`generate_cvs` ki jagah SELECT).
2. **CV storage**: Blob container banayein -> `parse_cv()` mein upload + Document Intelligence call.
3. **AI agent**: Azure OpenAI deployment banayein -> `score_vec()` ke top-N par agent re-ranking, `generate_ad()` mein ad writer.
4. **Email**: Azure Communication Services -> `send_mail()` / `send_internal()` mein real send.
5. **Automation**: `publish_event()` se events Service Bus / Event Grid par bhejein; Azure Function / Logic App handlers: reject -> candidate email, approve -> department + calendar.
6. **Login & roles**: Microsoft Entra ID -> role ko `S.settings['role']` mein map karein.
7. **Secrets**: sab keys `.streamlit/secrets.toml` ya Azure Key Vault mein.
""")


def page_settings():
    header("Settings")
    st.markdown("#### Profile & company")
    S.settings["user"] = st.text_input("Your name", S.settings["user"])
    S.settings["company"] = st.text_input("Company name", S.settings["company"])
    S.settings["new_days"] = st.slider("A CV is called 'New' if applied within (days)", 1, 30, int(S.settings["new_days"]))
    st.caption("Role badalne ke liye sidebar ka 'View as role' use karein. Admin/HR Manager: sab · Recruiter: Integrations/Settings ke ilawa · Hiring Manager: limited pages.")
    st.markdown("#### Demo data")
    n = st.number_input("CVs to generate", 500, 20000, 5000, 500)
    if st.button("♻️ Reset & regenerate demo data"):
        for k in list(S.keys()):
            del S[k]
        S.n_seed = int(n)
        st.rerun()


# =============================================================================
# NAVIGATION
# =============================================================================
PAGE_DEFS = [
    ("Overview", "Dashboard", page_dashboard, ":material/dashboard:", "dashboard"),
    ("Sourcing", "Job Requisitions", page_jobs, ":material/work:", "requisitions"),
    ("Sourcing", "Job Ads & Careers", page_ads, ":material/campaign:", "job-ads"),
    ("Sourcing", "CV Database", page_cvdb, ":material/folder_shared:", "cv-database"),
    ("Screening", "AI Matching", page_matching, ":material/auto_awesome:", "ai-matching"),
    ("Screening", "Pipeline", page_pipeline, ":material/view_kanban:", "pipeline"),
    ("Selection", "Department Handoff", page_handoff, ":material/account_tree:", "department"),
    ("Selection", "Interviews", page_interviews, ":material/event:", "interviews"),
    ("Selection", "Offers & Onboarding", page_offers, ":material/handshake:", "offers"),
    ("Automation", "Automation", page_automation, ":material/bolt:", "automation"),
    ("Automation", "Communication", page_comm, ":material/mail:", "communication"),
    ("Insights", "Analytics", page_analytics, ":material/insights:", "analytics"),
    ("Insights", "Notifications", page_notifications, ":material/notifications:", "notifications"),
    ("Admin", "Integrations", page_integrations, ":material/cable:", "integrations"),
    ("Admin", "Settings", page_settings, ":material/settings:", "settings"),
]
ALL_PAGES = [p[1] for p in PAGE_DEFS]
ROLES = ["Admin", "HR Manager", "Recruiter", "Hiring Manager"]
ROLE_PAGES = {"Admin": ALL_PAGES, "HR Manager": ALL_PAGES,
              "Recruiter": [p for p in ALL_PAGES if p not in ("Settings", "Integrations")],
              "Hiring Manager": ["Dashboard", "Job Requisitions", "AI Matching", "Pipeline", "Department Handoff", "Interviews", "Notifications"]}

init()
st.markdown(CSS, unsafe_allow_html=True)
allowed = ROLE_PAGES[S.settings["role"]]
unread = sum(1 for e in S.events if not e["read"])
PG, sections = {}, {}
for sec, name, fn, icon, path in PAGE_DEFS:
    if name in allowed:
        title = f"Notifications ({unread})" if (name == "Notifications" and unread) else name
        PG[name] = st.Page(fn, title=title, icon=icon, url_path=path, default=(name == "Dashboard"))
        sections.setdefault(sec, []).append(PG[name])
pg = st.navigation(sections)
with st.sidebar:
    st.divider()
    ini = "".join(w[0] for w in S.settings["user"].split()[:2]).upper() or "U"
    st.markdown(f"<div style='display:flex;gap:10px;align-items:center'><div style='width:38px;height:38px;border-radius:50%;"
                f"background:#2563eb;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700'>{ini}</div>"
                f"<div><b>{S.settings['user']}</b><br><span style='font-size:12px;opacity:.7'>{S.settings['company']} · People &amp; Culture</span></div></div>",
                unsafe_allow_html=True)
    new_role = st.selectbox("View as role", ROLES, index=ROLES.index(S.settings["role"]), key="role_sel")
    if new_role != S.settings["role"]:
        S.settings["role"] = new_role
        st.rerun()
    st.caption("Mode: simulation (no backend connected)")
pg.run()