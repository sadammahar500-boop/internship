
"""
XLOOP - Complete Recruitment Suite (Frontend + simulated engine)
People & Culture Department
 
Run:
    pip install -r requirements.txt
    streamlit run xloop_recruitment_suite.py
 
Abhi data st.session_state mein hai (5000 demo CVs auto-generate hoti hain).
Backend / database / LLM agent / real email baad mein "BACKEND HOOK" par lagenge.
"""
import io
import re
import random
import time
from datetime import date, datetime, timedelta
 
import numpy as np
import pandas as pd
import streamlit as st
 
st.set_page_config(page_title="Xloop | Recruitment Suite", page_icon="♾️", layout="wide")
S = st.session_state
TODAY = date.today()
 
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
CITIES = ["Karachi", "Lahore", "Islamabad", "Hyderabad", "Sukkur", "Larkana", "Multan", "Faisalabad", "Peshawar"]
EDU = {1: "Matric", 2: "Intermediate", 3: "Bachelors", 4: "Masters", 5: "PhD"}
STAGES = ["Applied", "Talent Pool", "Shortlisted", "Interview", "Offer", "Hired", "Rejected", "On Hold"]
SOURCES = ["Rozee.pk", "LinkedIn", "Company Website", "Referral", "Mustakbil", "Walk-in", "Indeed"]
PANEL = ["Sadam Ahmed", "Ayesha Khan", "Imran Qureshi", "Nida Farooq", "Bilal Ahmed"]
ROUNDS = ["HR Screening", "Technical", "Managerial", "Final"]
FIRST = ["Ayesha", "Hassan", "Zain", "Sana", "Bilal", "Fatima", "Usman", "Hina", "Ahmed", "Mariam", "Kamran", "Rabia",
         "Ali", "Noor", "Hamza", "Iqra", "Saad", "Maham", "Faisal", "Zara", "Omar", "Laiba", "Danish", "Aiman", "Asad", "Sidra"]
LAST = ["Malik", "Shah", "Raza", "Khan", "Siddiqui", "Noor", "Ali", "Tariq", "Javed", "Aslam", "Memon", "Chandio",
        "Soomro", "Qureshi", "Ansari", "Baloch", "Mirza", "Sheikh", "Butt", "Abbasi"]
ONBOARD_TASKS = ["Offer letter signed", "CNIC & documents collected", "Employee record created",
                 "Laptop & accounts provisioned", "Email & system access", "Orientation scheduled",
                 "Payroll registration", "Probation plan shared"]
DEFAULT_WEIGHTS = dict(skills=45, exp=25, edu=10, salary=10, loc=10)
 
DEFAULT_TEMPLATES = {
    "Application received": ("We received your application for {job}",
        "Dear {name},\n\nThank you for applying for {job} at {company}. Our team is reviewing your profile and "
        "we will update you shortly.\n\nRegards,\nPeople & Culture, {company}"),
    "Shortlisted": ("You have been shortlisted for {job}",
        "Dear {name},\n\nGood news! Your profile has been shortlisted for {job}. Our team will contact you soon "
        "with interview details.\n\nRegards,\nPeople & Culture, {company}"),
    "Interview invitation": ("Interview invitation - {job}",
        "Dear {name},\n\nYou are invited for an interview for {job}.\nDate: {date}\nTime: {time}\nMode: {mode}\n"
        "Panel: {panel}\n\nPlease confirm your availability.\n\nRegards,\nPeople & Culture, {company}"),
    "Interview reminder": ("Reminder: interview for {job}",
        "Dear {name},\n\nThis is a reminder for your interview for {job} on {date} at {time} ({mode}).\n\n"
        "Regards,\nPeople & Culture, {company}"),
    "Regret / rejection": ("Update on your application - {job}",
        "Dear {name},\n\nThank you for your interest in {company}. After careful review we will not be moving "
        "forward with your application for {job}. We will keep your CV for future openings.\n\nBest wishes,\n"
        "People & Culture, {company}"),
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
}
 
 
class SD(dict):
    def __missing__(self, k):
        return "{" + k + "}"
 
 
def render(t, **kw):
    return t.format_map(SD(**kw))
 
 
def nowstr():
    return datetime.now().strftime("%d %b %H:%M")
 
 
# =============================================================================
# DATA GENERATION (BACKEND HOOK: replace with DB / job-portal APIs)
# =============================================================================
def generate_cvs(n, start_id, seed, max_age=90, bias=1.6, jobs_by_dept=None, fresh=False):
    r = random.Random(seed)
    base = dict(IT=70000, Finance=55000, HR=48000, Marketing=52000, Sales=48000, Operations=50000)
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
        sal = int(round((base[dept] + exp * 8000) * r.uniform(0.8, 1.3), -3))
        fn, ln = r.choice(FIRST), r.choice(LAST)
        email = r.choice(seen[-400:]) if (seen and r.random() < 0.015) else f"{fn}.{ln}{cid}@mail.com".lower()
        seen.append(email)
        lvl = "Senior " if exp >= 6 else ("Junior " if exp < 2 else "")
        age = 0 if fresh else int(max_age * (r.random() ** bias))
        jids = (jobs_by_dept or {}).get(dept, [])
        pooled = (not jids) or r.random() < 0.12
        rows.append(dict(
            id=cid, name=f"{fn} {ln}", email=email, phone="03" + "".join(r.choice("0123456789") for _ in range(9)),
            city=r.choice(CITIES), title=lvl + r.choice(TITLES[dept]), dept=dept, exp=exp, edu=edu, salary=sal,
            skills="|".join(sorted(sk)), source=r.choice(SOURCES),
            applied=pd.Timestamp(TODAY - timedelta(days=age)),
            stage="Talent Pool" if pooled else "Applied", job_id=0 if pooled else r.choice(jids),
            score=np.nan, acked=age > 10 or pooled, tags="", notes=""))
    return pd.DataFrame(rows).set_index("id")
 
 
def default_jobs():
    def J(i, title, dept, must, nice, mn, mx, edu, smin, smax, loc, hc, status, dl):
        return dict(id=i, title=title, dept=dept, must=must, nice=nice, min_exp=mn, max_exp=mx, edu_min=edu,
                    sal_min=smin, sal_max=smax, location=loc, headcount=hc, status=status,
                    deadline=TODAY + timedelta(days=dl), manager="Sadam Ahmed", created=TODAY - timedelta(days=20),
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
 
 
# =============================================================================
# AI MATCHING ENGINE (vectorised - 5000 CVs in milliseconds)
# BACKEND HOOK: swap/extend with embeddings + LLM re-ranking later
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
    txt += f"; {c['exp']} yrs experience vs {job['min_exp']}+ required"
    txt += "; salary expectation within budget." if c["salary"] <= job["sal_max"] else \
        f"; expects PKR {c['salary']:,} which is above the PKR {job['sal_max']:,} cap."
    return txt
 
 
def suggested_offer(c, job):
    return int(min(max(c["salary"], job["sal_min"]), job["sal_max"]))
 
 
# =============================================================================
# ACTIONS: stage moves, emails, events
# =============================================================================
def ev(text, kind="info"):
    S.events.insert(0, dict(time=nowstr(), text=text, kind=kind, read=False))
 
 
def send_mail(ids, key, extra=None):
    """BACKEND HOOK: replace with SMTP / SendGrid / WhatsApp API."""
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
        kw = dict(name=name, job=job, company=S.settings["company"], **(extra or {}))
        rows.append(dict(time=ts, to=email, name=name, type=key, subject=render(subj, **kw),
                         body=render(body, **kw), job=job, status="Sent (simulated)"))
    S.outbox.extend(rows)
 
 
STAGE_MAIL = {"Shortlisted": "Shortlisted", "Rejected": "Regret / rejection", "Hired": "Welcome onboard"}
 
 
def move(ids, stage, reason="", email="auto", extra=None):
    ids = list(ids)
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
 
 
def goto(page, job_id=None):
    S.nav = page
    if job_id:
        S.mj_pref = job_id
 
 
# =============================================================================
# AUTOMATION ENGINE
# =============================================================================
def send_due_reminders():
    n = 0
    now = datetime.now()
    for iv in S.interviews:
        if iv["status"] != "Scheduled" or iv["reminded"]:
            continue
        when = datetime.combine(iv["date"], datetime.strptime(iv["time"], "%H:%M").time())
        if timedelta(0) <= when - now <= timedelta(hours=S.auto["reminder_hours"]):
            send_mail([iv["cid"]], "Interview reminder",
                      dict(date=iv["date"].strftime("%A, %d %b"), time=iv["time"], mode=iv["mode"]))
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
    res = dict(screened=0, shortlisted=0, rejected=0, review=0, pooled=0, acked=0, reminders=0, followups=0, skipped=0)
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
        existing = int(((df["job_id"] == jid) & (df["stage"] == "Shortlisted")).sum())
        room = max(0, a["max_shortlist"] - existing)
        cand = idx[ok]
        sl_ids = cand[np.argsort(-s[ok])][:room]
        rej_ids = idx[rej]
        rest = idx[(~rej) & (~idx.isin(sl_ids))]
        move(rej_ids, "Rejected", "AI auto-screen")
        move(sl_ids, "Shortlisted", f"AI auto-shortlist (>={a['shortlist_at']}%)")
        if a["pool_rest"]:
            move(rest, "Talent Pool", "AI auto-screen: keep for future", email=None)
            res["pooled"] += len(rest)
        else:
            res["review"] += len(rest)
        res["screened"] += len(idx)
        res["shortlisted"] += len(sl_ids)
        res["rejected"] += len(rej_ids)
        if a["notify_hr"] and not quiet:
            ev(f"{job['title']}: {len(sl_ids)} auto-shortlisted, {len(rej_ids)} auto-rejected, {len(rest)} need review", "success")
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
    jid = int(S.df.at[cid, "job_id"])
    S.interviews.append(dict(id=len(S.interviews) + 1, cid=cid, job_id=jid, round=rnd, date=d, time=t, mode=mode,
                             panel=list(panel), status="Scheduled", scores=None, rec="", comment="", reminded=False))
    move([cid], "Interview", f"{rnd} on {d}", email=None)
    if not silent:
        send_mail([cid], "Interview invitation", dict(date=d.strftime("%A, %d %b %Y"), time=t, mode=mode, panel=", ".join(panel)))
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
    S.employees.append(dict(id=len(S.employees) + 1, cid=cid, name=c["name"], title=job["title"], dept=job["dept"],
                            join=joining, salary=salary, hired_on=TODAY, applied=c["applied"].date(),
                            tasks={t: (i < 2) for i, t in enumerate(ONBOARD_TASKS)}))
 
 
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
            al.append(("med", f"'{j['title']}' is waiting for approval", "Jobs", None, "Open"))
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
    S.settings = dict(company="Xloop", role="HR Manager", user="Sadam Ahmed")
    S.jobs = default_jobs()
    S.hist, S.outbox, S.events, S.interviews, S.offers, S.employees, S.autolog = {}, [], [], [], [], [], []
    S.templates = dict(DEFAULT_TEMPLATES)
    S.auto = dict(send_emails=True, ack=True, shortlist_at=80, reject_below=40, reject_knockout=True, max_shortlist=15,
                  pool_rest=False, run_on_import=True, reminder_hours=24, followup_days=3, notify_hr=True)
    S.ver, S.last_run, S.mj_pref = 0, None, 1
    by_dept = {}
    for j in S.jobs:
        if j["status"] == "Open":
            by_dept.setdefault(j["dept"], []).append(j["id"])
    S.df = generate_cvs(n, 1, 42, jobs_by_dept=by_dept)
    rebuild_matrix()
    run_automation(only_before=TODAY - timedelta(days=10), quiet=True)
    # seed an active pipeline
    for k, j in enumerate([x for x in S.jobs if x["status"] == "Open"]):
        sl = S.df[(S.df["job_id"] == j["id"]) & (S.df["stage"] == "Shortlisted")].sort_values("score", ascending=False)
        ids = list(sl.index[:3])
        if len(ids) >= 2:
            schedule_interview(ids[0], "Technical", TODAY - timedelta(days=2), "11:00", "Online", PANEL[:2], silent=True, override=True)
            S.interviews[-1].update(status="Completed", scores=dict(Technical=4, Communication=4, **{"Problem Solving": 5, "Culture Fit": 4}), rec="Hire", comment="Strong candidate.")
            schedule_interview(ids[1], "HR Screening", TODAY + timedelta(days=1 + k % 3), f"{10 + k % 5}:00", "Onsite", PANEL[1:3], silent=True, override=True)
        if len(ids) >= 3 and k % 3 == 0:
            move([ids[2]], "Offer", "Seed", email=None)
            sal = suggested_offer(S.df.loc[ids[2]], j)
            S.offers.append(dict(id=len(S.offers) + 1, cid=ids[2], job_id=j["id"], salary=sal, joining=TODAY + timedelta(days=30),
                                 status="Sent", sent_on=TODAY - timedelta(days=4), letter=offer_letter(ids[2], j, sal, TODAY + timedelta(days=30))))
        if len(ids) >= 3 and k % 4 == 1:
            move([ids[2]], "Hired", "Seed", email=None)
            make_employee(ids[2], suggested_offer(S.df.loc[ids[2]], j), TODAY + timedelta(days=14))
    S.events, S.autolog = [], []
    ev("Welcome to Xloop Recruitment Suite", "info")
    S.ready = True
 
 
# =============================================================================
# UI HELPERS
# =============================================================================
def badge(stage):
    col = dict(Applied="#dbeafe|#1e40af", Shortlisted="#ede9fe|#5b21b6", Interview="#cffafe|#155e75", Offer="#ffedd5|#9a3412",
               Hired="#bbf7d0|#14532d", Rejected="#fee2e2|#991b1b", **{"On Hold": "#fef3c7|#92400e", "Talent Pool": "#e5e7eb|#374151"})[stage]
    bg, fg = col.split("|")
    return f"<span style='background:{bg};color:{fg};padding:2px 10px;border-radius:8px;font-size:12px;font-weight:600'>{stage}</span>"
 
 
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
                         "Exp": sub["exp"].values, "Education": sub["edu"].map(EDU).values, "City": sub["city"].values,
                         "Exp. Salary": sub["salary"].values, "Skills": sub["skills"].str.replace("|", ", ", regex=False).values,
                         "Source": sub["source"].values, "Applied": sub["applied"].dt.date.values,
                         "Stage": sub["stage"].values, "Match %": sub["score"].round(0).values})
 
 
PROG = st.column_config.ProgressColumn("Match %", min_value=0, max_value=100, format="%.0f")
 
 
def candidate_card(cid, key, job_override=None):
    c = S.df.loc[cid]
    job = job_override or get_job(int(c["job_id"]))
    st.markdown(f"### {c['name']}")
    st.caption(f"{c['title']} · {c['exp']} yrs · {EDU[c['edu']]} · {c['city']} · {c['email']} · {c['phone']}")
    st.markdown(badge(c["stage"]) + f" &nbsp; <small>Source: {c['source']} · Applied {c['applied']:%d %b %Y}</small>", unsafe_allow_html=True)
    st.markdown("**Skills**<br>" + chips(c["skills"].split("|")), unsafe_allow_html=True)
    if job:
        ex = explain(cid, job)
        st.info(ai_summary(c, job, ex))
        t1, t2 = st.tabs([f"Match vs {job['title']}", "Skill gap"])
        with t1:
            for k, lbl in [("skills", "Skills"), ("exp", "Experience"), ("edu", "Education"), ("salary", "Salary fit"), ("loc", "Location")]:
                st.progress(min(max(ex["comps"][k], 0.0), 1.0), text=f"{lbl}: {ex['comps'][k] * 100:.0f}%")
            st.write(f"**Suggested offer:** PKR {suggested_offer(c, job):,} (expects PKR {c['salary']:,})")
        with t2:
            st.markdown("**Must-have matched**<br>" + chips(ex["mm"], "g"), unsafe_allow_html=True)
            st.markdown("**Must-have missing**<br>" + chips(ex["mx"], "r"), unsafe_allow_html=True)
            st.markdown("**Nice-to-have matched**<br>" + chips(ex["nm"], "g"), unsafe_allow_html=True)
    b = st.columns(5)
    for col, (lbl, stg) in zip(b, [("⭐ Shortlist", "Shortlisted"), ("✖ Reject", "Rejected"), ("⏸ Hold", "On Hold"),
                                   ("🗂 Talent pool", "Talent Pool"), ("💼 To offer", "Offer")]):
        if col.button(lbl, key=f"{key}_{stg}_{cid}"):
            move([cid], stg, "Manual action")
            st.rerun()
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
# PAGES
# =============================================================================
def page_dashboard():
    header("Recruitment Command Center", "Automate • Filter • Hire • Grow")
    if S.get("flash"):
        st.success(S.pop("flash"))
    df = S.df
    pend = int(((df["stage"] == "Applied") & df["score"].isna() & (df["job_id"] > 0)).sum())
    new7 = int((df["applied"] >= pd.Timestamp(TODAY - timedelta(days=7))).sum())
    cnt = df["stage"].value_counts()
    openj = sum(1 for j in S.jobs if j["status"] == "Open")
    upcoming = sum(1 for iv in S.interviews if iv["status"] == "Scheduled")
    offers = sum(1 for o in S.offers if o["status"] in ("Draft", "Sent"))
    r1 = st.columns(4)
    for col, (a, b, c_, t) in zip(r1, [("Total CVs in database", f"{len(df):,}", "all sources", "k1"),
                                       ("New (last 7 days)", f"{new7:,}", "incoming", "k2"),
                                       ("Awaiting AI screening", f"{pend:,}", "run automation", "k3"),
                                       ("Open positions", openj, f"{len(S.jobs)} requisitions", "k4")]):
        col.markdown(kpi(a, b, c_, t), unsafe_allow_html=True)
    st.write("")
    r2 = st.columns(4)
    for col, (a, b, c_, t) in zip(r2, [("Shortlisted", f"{cnt.get('Shortlisted', 0):,}", "ready for interview", "k3"),
                                       ("Interviews scheduled", upcoming, "upcoming", "k1"),
                                       ("Offers pending", offers, "awaiting reply", "k4"),
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
            a, b = st.columns([5, 1.3])
            a.markdown(f"{'🔴' if sev == 'high' else '🟡'} {txt}")
            b.button(lbl, key=f"al_{i}", on_click=goto, args=(pg, jid))
    with right:
        st.markdown("#### ⚙️ Automation")
        lr = S.last_run
        st.caption("Last run: " + (f"{lr['time']} · {lr['screened']} screened" if lr else "not run yet"))
        if st.button("▶ Run automation now", type="primary", key="dash_run"):
            with st.spinner("Screening CVs..."):
                r = run_automation()
            S.flash = (f"{r['screened']:,} CVs screened · {r['shortlisted']} shortlisted · "
                       f"{r['rejected']} rejected · {r['acked']} acknowledged · {r['seconds']}s")
            st.rerun()
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.markdown("##### Hiring funnel")
    c1.bar_chart(pd.Series({s: int(cnt.get(s, 0)) for s in ["Applied", "Shortlisted", "Interview", "Offer", "Hired"]}))
    c2.markdown("##### Applications - last 30 days")
    last = df[df["applied"] >= pd.Timestamp(TODAY - timedelta(days=30))]
    c2.line_chart(last.groupby(last["applied"].dt.date).size())
    c3.markdown("##### Source mix")
    c3.bar_chart(df["source"].value_counts())
    st.markdown("#### Open positions")
    ct = df.groupby(["job_id", "stage"]).size().unstack(fill_value=0)
    rows = []
    for j in S.jobs:
        g = ct.loc[j["id"]] if j["id"] in ct.index else pd.Series(dtype=int)
        rows.append({"Position": j["title"], "Dept": j["dept"], "Status": j["status"], "Applicants": int(g.sum()),
                     "Shortlisted": int(g.get("Shortlisted", 0)), "Interview": int(g.get("Interview", 0)),
                     "Hired / Headcount": f"{int(g.get('Hired', 0))}/{j['headcount']}", "Days left": (j["deadline"] - TODAY).days})
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    st.markdown("#### ⭐ Top AI picks")
    jobs_open = [j for j in S.jobs if j["status"] == "Open"]
    pj = st.selectbox("Position", [j["id"] for j in jobs_open], format_func=lambda i: get_job(i)["title"], key="dash_pj")
    top = df[(df["job_id"] == pj) & df["stage"].isin(["Applied", "Shortlisted"])].sort_values("score", ascending=False).head(5)
    for cid, c in top.iterrows():
        a, b, d = st.columns([3, 3, 1])
        a.markdown(f"**{c['name']}** · {c['title']}")
        b.progress(min(float(c["score"]) / 100, 1.0) if pd.notna(c["score"]) else 0.0,
                   text=f"{c['score']:.0f}% match · {c['exp']} yrs" if pd.notna(c["score"]) else "Not screened yet")
        d.markdown(badge(c["stage"]), unsafe_allow_html=True)
 
 
def page_jobs():
    header("Job Requisitions", "Create → Approve → Auto-match talent")
    can_approve = S.settings["role"] in ("Admin", "HR Manager")
    t1, t2 = st.tabs(["All requisitions", "➕ New requisition"])
    with t2:
        with st.form("job_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            title = c1.text_input("Position title")
            dept = c2.selectbox("Department", DEPTS)
            loc = c3.selectbox("Location", CITIES + ["Remote"])
            hc = c4.number_input("Headcount", 1, 50, 1)
            must = st.multiselect("Must-have skills", SKILLS)
            nice = st.multiselect("Nice-to-have skills", SKILLS)
            c5, c6, c7, c8 = st.columns(4)
            mn = c5.number_input("Min experience (yrs)", 0.0, 30.0, 2.0)
            mx = c6.number_input("Max experience (yrs)", 0.0, 40.0, 8.0)
            edu = c7.selectbox("Min education", list(EDU), index=2, format_func=lambda k: EDU[k])
            dl = c8.date_input("Closing date", TODAY + timedelta(days=30))
            c9, c10, c11 = st.columns(3)
            smin = c9.number_input("Salary min (PKR)", 0, 3000000, 80000, 5000)
            smax = c10.number_input("Salary max (PKR)", 0, 3000000, 130000, 5000)
            mgr = c11.text_input("Hiring manager", S.settings["user"])
            with st.expander("Scoring weights"):
                w = {k: st.slider(k.title(), 0, 100, v, key=f"nw_{k}") for k, v in DEFAULT_WEIGHTS.items()}
            if st.form_submit_button("Submit for approval", type="primary"):
                if title and must:
                    S.jobs.append(dict(id=max(j["id"] for j in S.jobs) + 1, title=title, dept=dept, must=must, nice=nice,
                                       min_exp=mn, max_exp=mx, edu_min=edu, sal_min=smin, sal_max=smax, location=loc,
                                       headcount=hc, status="Pending Approval", deadline=dl, manager=mgr, created=TODAY,
                                       weights=w, min_must=0.6))
                    ev(f"New requisition '{title}' submitted for approval", "info")
                    st.success("Requisition submit ho gayi. Approval ke baad AI talent pool match karega.")
                else:
                    st.error("Title aur kam az kam ek must-have skill zaroori hai.")
    with t1:
        for j in S.jobs:
            with st.container(border=True):
                a, b, c_ = st.columns([3.2, 2.5, 2.3])
                a.markdown(f"**{j['title']}**  \n{j['dept']} · {j['location']} · {j['headcount']} opening(s) · "
                           f"PKR {j['sal_min'] // 1000}K-{j['sal_max'] // 1000}K · closes {j['deadline']:%d %b}")
                b.markdown("Must: " + chips(j["must"], "g") + "<br>Nice: " + chips(j["nice"]), unsafe_allow_html=True)
                c_.markdown(f"**{j['status']}** · {(S.df['job_id'] == j['id']).sum():,} applicants")
                x = st.columns(5)
                if j["status"] in ("Pending Approval", "Draft"):
                    if x[0].button("✅ Approve & open" if can_approve else "🔒 Needs HR Manager", key=f"ap_{j['id']}", disabled=not can_approve):
                        j["status"] = "Open"
                        sc, must, _ = score_vec(j)
                        good = int(((sc >= S.auto["shortlist_at"]) & (must >= j["min_must"]) & S.df["stage"].isin(["Talent Pool", "Applied"]).values).sum())
                        ev(f"'{j['title']}' approved. AI found {good} strong matches in the CV database.", "success")
                        st.rerun()
                if j["status"] == "Open" and x[1].button("⏸ Hold", key=f"ho_{j['id']}"):
                    j["status"] = "On Hold"; st.rerun()
                if j["status"] in ("On Hold", "Closed") and x[1].button("▶ Reopen", key=f"ro_{j['id']}"):
                    j["status"] = "Open"; st.rerun()
                if j["status"] != "Closed" and x[2].button("⛔ Close", key=f"cl_{j['id']}"):
                    j["status"] = "Closed"; st.rerun()
                x[3].button("🎯 Find best CVs", key=f"fb_{j['id']}", on_click=goto, args=("AI Matching", j["id"]))
 
 
def page_matching():
    header("AI Talent Matching", "Poori CV database ko scan karke best candidates suggest karta hai")
    jobs = [j for j in S.jobs if j["status"] != "Closed"]
    ids = [j["id"] for j in jobs]
    idx = ids.index(S.mj_pref) if S.mj_pref in ids else 0
    jid = st.selectbox("Select position", ids, index=idx, format_func=lambda i: f"{get_job(i)['title']} · {get_job(i)['dept']} · {get_job(i)['status']}")
    S.mj_pref = jid
    job = get_job(jid)
    c1, c2, c3 = st.columns([1.4, 2, 1])
    scope = c1.radio("Scan", ["Applicants of this job", "Entire CV database"], key=f"sc_{jid}")
    stg = c2.multiselect("Include stages", STAGES, default=["Applied", "Talent Pool", "Shortlisted", "On Hold"], key=f"stg_{jid}")
    topn = c3.slider("Show top", 10, 200, 50, 10, key=f"tn_{jid}")
    with st.expander("⚙️ Scoring weights & knockout rules"):
        wc = st.columns(5)
        w = {k: wc[i].slider(k.title(), 0, 100, int(job["weights"][k]), key=f"w_{jid}_{k}") for i, k in enumerate(DEFAULT_WEIGHTS)}
        k1, k2, k3 = st.columns(3)
        min_must = k1.slider("Min must-have skill coverage %", 0, 100, int(job["min_must"] * 100), key=f"mm_{jid}") / 100
        cities = k2.multiselect("Only cities", CITIES, key=f"ct_{jid}")
        cap = k3.checkbox("Exclude if expected salary > cap +10%", key=f"cap_{jid}")
    t0 = time.perf_counter()
    sc, must, _ = score_vec(job, w)
    df = S.df
    mask = df["stage"].isin(stg).to_numpy(copy=True)
    if scope.startswith("Applicants"):
        mask &= (df["job_id"].values == jid)
    if cities:
        mask &= df["city"].isin(cities).values
    if cap:
        mask &= df["salary"].values <= job["sal_max"] * 1.1
    res = pd.DataFrame({"score": sc, "must": must * 100}, index=df.index)[mask]
    res["ko"] = res["must"] < min_must * 100
    res = res.sort_values("score", ascending=False)
    ms = (time.perf_counter() - t0) * 1000
    k = st.columns(5)
    for col, (l, v) in zip(k, [("CVs scanned", f"{int(mask.sum()):,}"), ("Excellent (≥85)", int((res.score >= 85).sum())),
                               ("Good (70-85)", int(((res.score >= 70) & (res.score < 85)).sum())),
                               ("Knockouts", int(res.ko.sum())), ("Match time", f"{ms:.0f} ms")]):
        col.metric(l, v)
    h = np.histogram(res["score"], bins=list(range(0, 101, 10)))[0]
    st.bar_chart(pd.Series(h, index=[f"{a}-{a + 10}" for a in range(0, 100, 10)]), height=150)
    top = res.head(topn)
    if top.empty:
        st.warning("Is filter par koi candidate nahi mila.")
        return
    sub = S.df.loc[top.index]
    tbl = pd.DataFrame({"Select": False, "ID": top.index, "Rank": range(1, len(top) + 1), "Name": sub["name"].values,
                        "Title": sub["title"].values, "Exp": sub["exp"].values, "Education": sub["edu"].map(EDU).values,
                        "City": sub["city"].values, "Exp. Salary": sub["salary"].values, "Match %": top["score"].round(1).values,
                        "Must-have %": top["must"].round(0).values,
                        "Flag": np.where(top["ko"], "⚠ must-have gap", "OK"), "Stage": sub["stage"].values})
    ed = st.data_editor(tbl, hide_index=True, key=f"med_{jid}_{S.ver}_{topn}", column_config={"Match %": PROG},
                        disabled=[c for c in tbl.columns if c != "Select"])
    sel = [int(i) for i in ed.loc[ed["Select"], "ID"]]
    st.caption(f"{len(sel)} selected")
    b = st.columns(4)
    if b[0].button("⭐ Shortlist selected", disabled=not sel):
        S.df.loc[sel, "job_id"] = jid
        move(sel, "Shortlisted", f"AI Matching: {job['title']}"); st.rerun()
    if b[1].button("✖ Reject selected", disabled=not sel):
        move(sel, "Rejected", "AI Matching"); st.rerun()
    if b[2].button("✉ Invite to apply (talent pool)", disabled=not sel):
        S.df.loc[sel, "job_id"] = jid
        move(sel, "Shortlisted", "Invited from talent pool", email="Invite to apply"); st.rerun()
    kk = b[3].number_input("Auto-shortlist top K", 1, 100, 10, label_visibility="collapsed")
    if b[3].button(f"🚀 Auto-shortlist top {kk}"):
        cand = top[(~top["ko"]) & S.df.loc[top.index, "stage"].isin(["Applied", "Talent Pool"])].head(kk).index
        S.df.loc[cand, "job_id"] = jid
        move(cand, "Shortlisted", f"Auto top-{kk}: {job['title']}", email="Invite to apply" if scope != "Applicants of this job" else "auto")
        ev(f"{len(cand)} candidates auto-shortlisted for {job['title']}", "success"); st.rerun()
    st.download_button("⬇ Export ranked list (CSV)", tbl.drop(columns="Select").to_csv(index=False), f"ranked_{job['title'].replace(' ', '_')}.csv")
    st.divider()
    tabs = st.tabs(["👤 Candidate deep-dive", "⚖️ Compare"])
    with tabs[0]:
        pick = st.selectbox("Open candidate", list(top.index[:50]), format_func=lambda i: f"{cname(i)} · {top.at[i, 'score']:.0f}%", key=f"pk_{jid}")
        candidate_card(pick, "mt", job)
    with tabs[1]:
        cmp_ids = st.multiselect("Pick 2-3 candidates", list(top.index[:50]), max_selections=3, format_func=cname, key=f"cmp_{jid}")
        if len(cmp_ids) >= 2:
            rows = {}
            for i in cmp_ids:
                ex = explain(i, job, w)
                c = S.df.loc[i]
                rows[c["name"]] = {"Match %": round(ex["score"], 1), "Experience": f"{c['exp']} yrs", "Education": EDU[c["edu"]],
                                   "Must-have": f"{len(ex['mm'])}/{len(job['must'])}", "Missing": ", ".join(ex["mx"]) or "-",
                                   "Nice-to-have": f"{len(ex['nm'])}/{len(job['nice'])}", "Expected salary": f"PKR {c['salary']:,}",
                                   "City": c["city"], "Stage": c["stage"]}
            st.dataframe(pd.DataFrame(rows))
 
 
def cv_filters(p):
    df = S.df
    a = st.columns([2, 1.2, 1.4, 1.2])
    kw = a[0].text_input("Keyword (name, title, skill, email)", key=p + "kw")
    dept = a[1].selectbox("Department", ["All"] + DEPTS, key=p + "dp")
    skl = a[2].multiselect("Skills", SKILLS, key=p + "sk")
    mode = a[3].radio("Skill match", ["ALL", "ANY"], horizontal=True, key=p + "sm")
    b = st.columns([1.5, 1, 1.3, 1.3, 1.3])
    er = b[0].slider("Experience (yrs)", 0.0, 25.0, (0.0, 25.0), key=p + "ex")
    emin = b[1].selectbox("Min education", list(EDU), format_func=lambda k: EDU[k], key=p + "ed")
    city = b[2].multiselect("City", CITIES, key=p + "ci")
    src = b[3].multiselect("Source", SOURCES, key=p + "so")
    when = b[4].selectbox("Applied", ["Any time", "Last 24h", "Last 7 days", "Last 30 days"], key=p + "wh")
    stg = st.multiselect("Stage", STAGES, default=STAGES, key=p + "st")
    m = df["stage"].isin(stg).values & df["exp"].between(*er).values & (df["edu"].values >= emin)
    if kw:
        m &= (df["name"].str.contains(kw, case=False, regex=False) | df["title"].str.contains(kw, case=False, regex=False) |
              df["skills"].str.contains(kw, case=False, regex=False) | df["email"].str.contains(kw, case=False, regex=False)).values
    if dept != "All":
        m &= (df["dept"].values == dept)
    if skl:
        cols = S.M[:, [SK_IDX[s] for s in skl]] > 0
        m &= cols.all(axis=1) if mode == "ALL" else cols.any(axis=1)
    if city:
        m &= df["city"].isin(city).values
    if src:
        m &= df["source"].isin(src).values
    days = {"Last 24h": 1, "Last 7 days": 7, "Last 30 days": 30}.get(when)
    if days:
        m &= (df["applied"] >= pd.Timestamp(TODAY - timedelta(days=days))).values
    return df[m]
 
 
def add_candidates(new):
    new = new[~new["email"].isin(S.df["email"])]
    new = new[~new["email"].duplicated()]
    if new.empty:
        return 0
    start = int(S.df.index.max()) + 1
    new.index = range(start, start + len(new))
    new.index.name = "id"
    S.df = pd.concat([S.df, new])
    rebuild_matrix()
    ev(f"{len(new)} new CVs imported", "info")
    if S.auto["run_on_import"]:
        run_automation()
    return len(new)
 
 
def parse_cv(name, data):
    text = ""
    if name.lower().endswith(".txt"):
        text = data.decode("utf-8", errors="ignore")
    elif name.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
        except Exception:
            text = ""
    elif name.lower().endswith(".docx"):
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
    return dict(name=nm or "Unknown", email=em.group(0) if em else f"{re.sub(r'[^a-z]', '', nm.lower()) or 'cv'}{random.randint(100, 999)}@unknown.com",
                phone=ph.group(0) if ph else "", city=city, title="Candidate", dept="IT" if sk and sk[0] in DEPT_SKILLS["IT"] else "HR",
                exp=float(ex.group(1)) if ex else 1.0, edu=edu, salary=60000, skills="|".join(sk))
 
 
def best_job_for(ids):
    best, bj = np.full(len(S.df), -1.0), np.zeros(len(S.df), int)
    for j in S.jobs:
        if j["status"] != "Open":
            continue
        sc, _, _ = score_vec(j)
        better = sc > best
        best, bj = np.where(better, sc, best), np.where(better, j["id"], bj)
    pos = S.df.index.get_indexer(ids)
    return bj[pos]
 
 
def page_cvdb():
    header("CV Database", f"{len(S.df):,} CVs · bulk import, advanced search, duplicate control")
    t1, t2, t3 = st.tabs(["🔍 Search & manage", "⬆ Import CVs", "👯 Duplicates"])
    with t1:
        with st.container(border=True):
            sub = cv_filters("db_")
        st.markdown(f"**{len(sub):,}** of {len(S.df):,} CVs match")
        ps = st.selectbox("Rows per page", [25, 50, 100], key="db_ps")
        pages = max(1, -(-len(sub) // ps))
        pg = st.number_input("Page", 1, pages, 1, key="db_pg")
        view = sub.iloc[(pg - 1) * ps: pg * ps]
        st.dataframe(view_df(view), hide_index=True, column_config={"Match %": PROG})
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
                    d = parse_cv(f.name, f.read())
                    d.update(source="Company Website", applied=pd.Timestamp(TODAY), stage="Applied", job_id=0, score=np.nan,
                             acked=False, tags="", notes="")
                    rows.append(d)
                    bar.progress((i + 1) / len(files))
                new = pd.DataFrame(rows)
                n0 = int(S.df.index.max()) + 1
                n = add_candidates(new)
                if n:
                    ids = list(range(n0, n0 + n))
                    jids = best_job_for(ids) if assign.startswith("Auto") else [int(assign.split(" - ")[0])] * n
                    S.df.loc[ids, "job_id"] = jids
                    run_automation() if S.auto["run_on_import"] else None
                st.success(f"{n} CV import hui ({len(files) - n} duplicate skip).")
        with c2:
            st.markdown("##### Simulate bulk inflow (portal / email import)")
            n = st.number_input("How many new CVs?", 50, 10000, 500, 50)
            if st.button("📥 Generate & auto-process"):
                by_dept = {}
                for j in S.jobs:
                    if j["status"] == "Open":
                        by_dept.setdefault(j["dept"], []).append(j["id"])
                new = generate_cvs(int(n), 0, random.randint(1, 10**6), max_age=0, jobs_by_dept=by_dept, fresh=True)
                new["acked"] = False
                new["stage"] = "Applied"
                new.loc[new["job_id"] == 0, "job_id"] = [random.choice(sum(by_dept.values(), [])) for _ in range((new["job_id"] == 0).sum())]
                added = add_candidates(new)
                st.success(f"{added:,} CVs aaye aur automation ne process kar di (Dashboard dekhein).")
    with t3:
        d = S.df[S.df["email"].duplicated(keep=False)].sort_values("email")
        st.write(f"**{len(d)}** duplicate rows found (same email).")
        if not d.empty:
            st.dataframe(view_df(d).assign(Email=d["email"].values), hide_index=True)
            if st.button("🧹 Remove duplicates (keep earliest)"):
                S.df = S.df[~S.df["email"].duplicated(keep="first")]
                rebuild_matrix(); st.rerun()
 
 
def page_pipeline():
    header("Candidate Pipeline", "Stage-wise tracking & bulk moves")
    df = S.df
    jf = st.selectbox("Position", [0] + [j["id"] for j in S.jobs], format_func=lambda i: "All positions" if i == 0 else get_job(i)["title"])
    base = df if jf == 0 else df[df["job_id"] == jf]
    cnt = base["stage"].value_counts()
    cols = st.columns(len(STAGES))
    for c, s in zip(cols, STAGES):
        c.metric(s, f"{int(cnt.get(s, 0)):,}")
    stage = st.radio("Stage", STAGES, horizontal=True, index=2)
    sub = base[base["stage"] == stage].sort_values("score", ascending=False)
    if stage == "Applied":
        only_review = st.checkbox("Only borderline CVs needing manual review (already screened)", True)
        if only_review:
            sub = sub[sub["score"].notna()]
    st.caption(f"Showing top 200 of {len(sub):,}")
    v = view_df(sub.head(200))
    v.insert(0, "Select", False)
    ed = st.data_editor(v, hide_index=True, key=f"pl_{stage}_{jf}_{S.ver}", column_config={"Match %": PROG},
                        disabled=[c for c in v.columns if c != "Select"])
    sel = [int(i) for i in ed.loc[ed["Select"], "ID"]]
    a, b, c_ = st.columns([2, 1.5, 1.5])
    tgt = a.selectbox("Move selected to", [s for s in STAGES if s != stage], key="pl_tg")
    mail = b.checkbox("Send email", True)
    if c_.button(f"Move {len(sel)} candidate(s)", disabled=not sel, type="primary"):
        move(sel, tgt, "Pipeline bulk move", email="auto" if mail else None); st.rerun()
    if len(sub):
        pick = st.selectbox("Open profile", list(sub.head(200).index), format_func=lambda i: f"{cname(i)} · {sub.at[i, 'score']:.0f}%" if pd.notna(sub.at[i, 'score']) else cname(i), key="pl_pick")
        with st.container(border=True):
            candidate_card(pick, "pl")
 
 
def page_interviews():
    header("Interview Management", "Schedule • Panel • Scorecards • Reminders")
    t1, t2, t3 = st.tabs(["📆 Agenda", "➕ Schedule", "📝 Scorecards & ranking"])
    with t1:
        c = st.columns(3)
        if c[0].button("🔔 Send due reminders (next %dh)" % S.auto["reminder_hours"]):
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
                a.markdown(f"**{iv['time']}** · {cname(iv['cid'])} · {iv['round']} · {iv['mode']}  \nPanel: {', '.join(iv['panel'])}")
                if b.button("✔ Completed", key=f"ic_{iv['id']}"):
                    iv["status"] = "Completed"; st.rerun()
                if d.button("✖ Cancel", key=f"ix_{iv['id']}"):
                    iv["status"] = "Cancelled"; st.rerun()
    with t2:
        st.markdown("##### Single interview")
        pool = S.df[S.df["stage"].isin(["Shortlisted", "Interview"])].sort_values("score", ascending=False).head(300)
        if pool.empty:
            st.info("Pehle candidates shortlist karein.")
        else:
            a = st.columns(5)
            cid = a[0].selectbox("Candidate", list(pool.index), format_func=lambda i: f"{cname(i)} ({S.df.at[i, 'score']:.0f}%)" if pd.notna(S.df.at[i, 'score']) else cname(i))
            rnd = a[1].selectbox("Round", ROUNDS)
            d = a[2].date_input("Date", TODAY + timedelta(days=2))
            t = a[3].time_input("Time", datetime.strptime("11:00", "%H:%M").time())
            mode = a[4].selectbox("Mode", ["Onsite", "Online", "Phone"])
            pn = st.multiselect("Panel", PANEL, default=PANEL[:2])
            ts = t.strftime("%H:%M")
            cf = conflicts_for(d, ts, pn)
            if cf:
                st.warning("Conflict: " + ", ".join(set(sum([c["panel"] for c in cf], [])) & set(pn)) + " already has an interview at this time.")
            if st.button("Schedule & notify", disabled=bool(cf), type="primary"):
                schedule_interview(cid, rnd, d, ts, mode, pn); st.success("Scheduled ✅"); st.rerun()
        st.divider()
        st.markdown("##### 🤖 Auto-schedule all shortlisted candidates of a job")
        jobs = [j for j in S.jobs if j["status"] == "Open"]
        b = st.columns(5)
        jid = b[0].selectbox("Position", [j["id"] for j in jobs], format_func=lambda i: get_job(i)["title"], key="as_j")
        rnd2 = b[1].selectbox("Round", ROUNDS, key="as_r")
        start = b[2].date_input("Start date", TODAY + timedelta(days=1), key="as_d")
        mins = b[3].selectbox("Slot (mins)", [30, 45, 60], index=1)
        mode2 = b[4].selectbox("Mode", ["Onsite", "Online", "Phone"], key="as_m")
        pn2 = st.multiselect("Panel", PANEL, default=PANEL[:2], key="as_p")
        sl = S.df[(S.df["job_id"] == jid) & (S.df["stage"] == "Shortlisted")].sort_values("score", ascending=False)
        st.caption(f"{len(sl)} shortlisted candidates · slots 10:00-17:00, lunch 13-14, weekends skipped, panel conflicts avoided")
        if st.button(f"📅 Auto-schedule {len(sl)} candidates", disabled=sl.empty or not pn2):
            n = auto_schedule(list(sl.index), rnd2, start, pn2, mode2, mins)
            ev(f"{n} interviews auto-scheduled for {get_job(jid)['title']}", "success"); st.success(f"{n} interviews schedule + invitations sent"); st.rerun()
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
            if st.button(f"💼 Move {len(hire)} recommended candidate(s) to Offer", disabled=not hire):
                move(hire, "Offer", "Interview recommended", email=None); st.rerun()
 
 
def page_offers():
    header("Offers & Onboarding", "Offer letter → Acceptance → Employee record → Checklist")
    t1, t2, t3 = st.tabs(["💼 Offers", "✅ Onboarding", "👥 Employees"])
    with t1:
        noffer = S.df[(S.df["stage"] == "Offer") & (~S.df.index.isin([o["cid"] for o in S.offers if o["status"] in ("Draft", "Sent")]))]
        for cid in noffer.index[:20]:
            job = get_job(int(S.df.at[cid, "job_id"]))
            if not job:
                continue
            with st.form(f"of_{cid}"):
                st.markdown(f"**Create offer: {cname(cid)}** · {job['title']}")
                a, b = st.columns(2)
                sal = a.number_input("Monthly salary (PKR)", 0, 3000000, suggested_offer(S.df.loc[cid], job), 5000)
                jn = b.date_input("Joining date", TODAY + timedelta(days=30))
                if st.form_submit_button("Generate & send offer"):
                    S.offers.append(dict(id=len(S.offers) + 1, cid=cid, job_id=job["id"], salary=sal, joining=jn, status="Sent",
                                         sent_on=TODAY, letter=offer_letter(cid, job, sal, jn)))
                    send_mail([cid], "Job offer", dict(salary=f"{sal:,}", joining=jn.strftime("%d %b %Y")))
                    st.rerun()
        st.markdown("##### All offers")
        if not S.offers:
            st.info("Abhi koi offer nahi.")
        for o in S.offers:
            with st.container(border=True):
                a, b, c_, d = st.columns([3, 1.5, 2.5, 2])
                a.markdown(f"**{cname(o['cid'])}** · {get_job(o['job_id'])['title'] if get_job(o['job_id']) else ''}  \nPKR {o['salary']:,} · join {o['joining']:%d %b}")
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
                        move([o["cid"]], "Talent Pool", "Offer declined", email=None); st.rerun()
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
 
 
def page_automation():
    header("Automation Center", "Rules jo HR ka manual kaam khud karte hain")
    a = S.auto
    st.graphviz_chart("""digraph { rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#eaf1ff", fontsize=11];
      A [label="New CV\\n(portal/email/upload)"]; B [label="Acknowledgement\\nemail"]; C [label="AI scoring\\nvs job"];
      D [label="Score >= shortlist %\\n+ must-haves", fillcolor="#dcfce7"]; E [label="Score < reject %\\nor knockout", fillcolor="#fee2e2"];
      F [label="Borderline:\\nmanual review", fillcolor="#fef3c7"]; G [label="Shortlist email\\n+ HR alert"]; H [label="Regret email"];
      I [label="Auto-schedule\\ninterviews"]; J [label="Reminders &\\noffer follow-ups"];
      A->B->C; C->D; C->E; C->F; D->G->I->J; E->H; }""")
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
            st.markdown("##### Communication & triggers")
            a["send_emails"] = st.checkbox("Send candidate emails automatically", a["send_emails"])
            a["ack"] = st.checkbox("Acknowledgement email on new application", a["ack"])
            a["notify_hr"] = st.checkbox("Notify HR of automation results", a["notify_hr"])
            a["run_on_import"] = st.checkbox("Run automation automatically after CV import", a["run_on_import"])
            a["reminder_hours"] = st.number_input("Interview reminder (hours before)", 1, 72, a["reminder_hours"])
            a["followup_days"] = st.number_input("Offer follow-up after (days)", 1, 14, a["followup_days"])
    x, y = st.columns([1, 1])
    rs = y.checkbox("Re-screen already scored applicants")
    if x.button("▶ Run automation now", type="primary"):
        with st.spinner("Processing..."):
            r = run_automation(rescreen=rs)
        st.success(f"{r['screened']:,} CVs screened in {r['seconds']}s")
    if S.autolog:
        st.markdown("##### Run history")
        st.dataframe(pd.DataFrame(S.autolog), hide_index=True)
 
 
def page_comm():
    header("Communication Center", "Templates • Bulk messaging • Outbox")
    t1, t2, t3 = st.tabs(["✉ Templates", "📣 Bulk message", "📤 Outbox"])
    with t1:
        key = st.selectbox("Template", list(S.templates))
        subj, body = S.templates[key]
        ns = st.text_input("Subject", subj, key=f"ts_{key}")
        nb = st.text_area("Body", body, height=220, key=f"tb_{key}")
        st.caption("Placeholders: {name} {job} {company} {date} {time} {mode} {panel} {salary} {joining}")
        if st.button("Save template"):
            S.templates[key] = (ns, nb); st.toast("Saved")
        st.markdown("**Preview**")
        st.code(render(ns, name="Ayesha Malik", job="Frontend Developer", company=S.settings["company"]) + "\n\n" +
                render(nb, name="Ayesha Malik", job="Frontend Developer", company=S.settings["company"], date="Mon, 02 Nov", time="11:00", mode="Online", panel="Sadam Ahmed", salary="150,000", joining="01 Dec"))
    with t2:
        c1, c2, c3 = st.columns(3)
        jf = c1.selectbox("Job", [0] + [j["id"] for j in S.jobs], format_func=lambda i: "All jobs" if i == 0 else get_job(i)["title"], key="bm_j")
        sf = c2.multiselect("Stage", STAGES, default=["Shortlisted"], key="bm_s")
        tp = c3.selectbox("Template", list(S.templates), key="bm_t")
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
            f = st.multiselect("Type", sorted(ob["type"].unique()), key="ob_f")
            if f:
                ob = ob[ob["type"].isin(f)]
            st.metric("Messages", f"{len(ob):,}")
            st.dataframe(ob[["time", "to", "name", "type", "subject", "status"]].iloc[::-1].head(500), hide_index=True)
            st.download_button("⬇ Export outbox", ob.to_csv(index=False), "outbox.csv")
 
 
def page_analytics():
    header("Analytics & Reports")
    df = S.df
    fun = pd.Series({"Total CVs": len(df), "AI screened": int(df["score"].notna().sum()),
                     "Shortlisted+": int(df["stage"].isin(["Shortlisted", "Interview", "Offer", "Hired"]).sum()),
                     "Interview+": int(df["stage"].isin(["Interview", "Offer", "Hired"]).sum()),
                     "Offer+": int(df["stage"].isin(["Offer", "Hired"]).sum()), "Hired": int((df["stage"] == "Hired").sum())})
    tth = np.mean([(e["hired_on"] - e["applied"]).days for e in S.employees]) if S.employees else 0
    k = st.columns(4)
    k[0].metric("Screen → shortlist", f"{fun['Shortlisted+'] / max(fun['AI screened'], 1) * 100:.1f}%")
    k[1].metric("Offer → hire", f"{fun['Hired'] / max(fun['Offer+'], 1) * 100:.0f}%")
    k[2].metric("Avg time-to-hire", f"{tth:.0f} days")
    k[3].metric("Hours saved (est.)", f"{int(df['score'].notna().sum() * 6 / 60):,} h")
    a, b = st.columns(2)
    a.markdown("##### Recruitment funnel"); a.bar_chart(fun)
    b.markdown("##### Applications by department"); b.bar_chart(df["dept"].value_counts())
    c, d = st.columns(2)
    src = df.groupby("source").agg(Applications=("stage", "size"),
                                   Shortlisted=("stage", lambda s: int(s.isin(["Shortlisted", "Interview", "Offer", "Hired"]).sum())),
                                   Hired=("stage", lambda s: int((s == "Hired").sum())), AvgScore=("score", "mean")).round(1)
    c.markdown("##### Source effectiveness"); c.dataframe(src)
    d.markdown("##### AI score distribution")
    d.bar_chart(pd.Series(np.histogram(df["score"].dropna(), bins=list(range(0, 101, 10)))[0], index=[f"{x}-{x + 10}" for x in range(0, 100, 10)]))
    e, f = st.columns(2)
    e.markdown("##### Most common skills in database")
    e.bar_chart(pd.Series(S.M.sum(axis=0), index=SKILLS).sort_values(ascending=False).head(15))
    f.markdown("##### Talent scarcity - % CVs with required skills")
    req = sorted({s for j in S.jobs if j["status"] == "Open" for s in j["must"]})
    f.bar_chart(pd.Series({s: S.M[:, SK_IDX[s]].mean() * 100 for s in req}).sort_values())
    st.download_button("⬇ Export summary (CSV)", src.to_csv(), "recruitment_summary.csv")
 
 
def page_notifications():
    header("Notifications", "Smart alerts + activity feed")
    st.markdown("#### Smart alerts")
    for sev, txt, pg, jid, lbl in compute_alerts() or [("low", "No alerts", "Dashboard", None, "")]:
        st.markdown(f"{'🔴' if sev == 'high' else '🟡' if sev == 'med' else '🟢'} {txt}")
    st.markdown("#### Activity feed")
    if st.button("Mark all read"):
        for e in S.events:
            e["read"] = True
        st.rerun()
    for e in S.events[:100]:
        st.markdown(f"{'🔵' if not e['read'] else '⚪'} `{e['time']}` {e['text']}")
 
 
def page_settings():
    header("Settings")
    st.markdown("#### User & role (role-based access)")
    roles = ["Admin", "HR Manager", "Recruiter", "Hiring Manager"]
    S.settings["role"] = st.selectbox("Current role", roles, index=roles.index(S.settings["role"]))
    S.settings["user"] = st.text_input("Your name", S.settings["user"])
    S.settings["company"] = st.text_input("Company name", S.settings["company"])
    st.caption("Admin/HR Manager: sab kuch · Recruiter: Settings ke ilawa · Hiring Manager: Dashboard, Jobs, AI Matching, Pipeline, Interviews, Notifications")
    st.markdown("#### Backend connections (coming soon)")
    st.text_input("Database URL (PostgreSQL)", placeholder="postgresql://user:pass@host/db")
    st.text_input("LLM / AI agent API key", type="password")
    st.text_input("SMTP / Email provider")
    st.markdown("#### Demo data")
    n = st.number_input("CVs to generate", 500, 20000, 5000, 500)
    if st.button("♻️ Reset & regenerate demo data"):
        keep = S.settings
        for k in list(S.keys()):
            del S[k]
        S.n_seed = int(n)
        st.rerun()
 
 
# =============================================================================
# CSS + NAVIGATION
# =============================================================================
NAV = ["Dashboard", "Jobs", "AI Matching", "CV Database", "Pipeline", "Interviews", "Offers & Onboarding",
       "Automation", "Communication", "Analytics", "Notifications", "Settings"]
ICONS = {
    "Dashboard": "<rect x='3' y='3' width='7' height='7'/><rect x='14' y='3' width='7' height='7'/><rect x='14' y='14' width='7' height='7'/><rect x='3' y='14' width='7' height='7'/>",
    "Jobs": "<rect x='2' y='7' width='20' height='14' rx='2'/><path d='M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16'/>",
    "AI Matching": "<polygon points='13 2 3 14 12 14 11 22 21 10 12 10 13 2'/>",
    "CV Database": "<ellipse cx='12' cy='5' rx='9' ry='3'/><path d='M21 12c0 1.66-4 3-9 3s-9-1.34-9-3'/><path d='M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5'/>",
    "Pipeline": "<polygon points='22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3'/>",
    "Interviews": "<rect x='3' y='4' width='18' height='18' rx='2'/><line x1='16' y1='2' x2='16' y2='6'/><line x1='8' y1='2' x2='8' y2='6'/><line x1='3' y1='10' x2='21' y2='10'/>",
    "Offers & Onboarding": "<path d='M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='8.5' cy='7' r='4'/><polyline points='17 11 19 13 23 9'/>",
    "Automation": "<polyline points='23 4 23 10 17 10'/><polyline points='1 20 1 14 7 14'/><path d='M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15'/>",
    "Communication": "<path d='M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z'/><polyline points='22,6 12,13 2,6'/>",
    "Analytics": "<line x1='12' y1='20' x2='12' y2='10'/><line x1='18' y1='20' x2='18' y2='4'/><line x1='6' y1='20' x2='6' y2='16'/>",
    "Notifications": "<path d='M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9'/><path d='M13.73 21a2 2 0 0 1-3.46 0'/>",
    "Settings": "<line x1='4' y1='21' x2='4' y2='14'/><line x1='4' y1='10' x2='4' y2='3'/><line x1='12' y1='21' x2='12' y2='12'/><line x1='12' y1='8' x2='12' y2='3'/><line x1='20' y1='21' x2='20' y2='16'/><line x1='20' y1='12' x2='20' y2='3'/><line x1='1' y1='14' x2='7' y2='14'/><line x1='9' y1='8' x2='15' y2='8'/><line x1='17' y1='16' x2='23' y2='16'/>",
}
ROLE_PAGES = {"Admin": NAV, "HR Manager": NAV, "Recruiter": [p for p in NAV if p != "Settings"],
              "Hiring Manager": ["Dashboard", "Jobs", "AI Matching", "Pipeline", "Interviews", "Notifications"]}
 
 
def inject_css(allowed):
    icon_css = "".join(
        f"""section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type({i}) > div:last-child::before
        {{-webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{ICONS[n]}</svg>");
          mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{ICONS[n]}</svg>");}}\n"""
        for i, n in enumerate(allowed, start=1))
    st.markdown("""<style>
.block-container {padding-top: 1.1rem; max-width: 1450px;}
section[data-testid="stSidebar"] {background: linear-gradient(180deg,#0b1533 0%,#101f4a 100%); border-right: 1px solid #1c2c5c;}
section[data-testid="stSidebar"] * {color: #e8ecf8;}
.hdr {background: linear-gradient(90deg,#10235c,#1b3a8a); color:#fff; padding:16px 26px; border-radius:14px;
      display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;}
.hdr h2 {margin:0; font-size:25px; color:#fff;} .hdr p {margin:2px 0 0; opacity:.8; font-size:14px;}
.hdr .right {text-align:right; font-weight:600; color:#fff;} .hdr .right span {font-weight:400; font-size:13px; opacity:.85;}
.kpi {border-radius:14px; padding:14px 18px; border:1px solid rgba(120,130,160,.25);}
.kpi .l {font-size:13px; opacity:.75;} .kpi .v {font-size:30px; font-weight:700;} .kpi .s {font-size:12px; opacity:.6;}
.k1{background:rgba(59,130,246,.12)} .k2{background:rgba(34,197,94,.12)} .k3{background:rgba(139,92,246,.12)} .k4{background:rgba(249,115,22,.12)}
.brand {display:flex; align-items:center; gap:12px; padding:10px 8px 18px; border-bottom:1px solid rgba(255,255,255,.08); margin-bottom:14px;}
.brand .logo {width:40px; height:40px; border-radius:11px; background:linear-gradient(135deg,#3b82f6,#7c3aed);
  display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:800; color:#fff !important;}
.brand .t1 {font-size:20px; font-weight:700; line-height:1.1; color:#fff !important;}
.brand .t2 {font-size:11px; opacity:.65; letter-spacing:.6px; text-transform:uppercase;}
.navlbl {font-size:11px; letter-spacing:1.2px; text-transform:uppercase; opacity:.5; padding:4px 10px 8px;}
section[data-testid="stSidebar"] div[role="radiogroup"] {gap:1px;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label {width:100%; padding:8px 12px; border-radius:10px; cursor:pointer;
  transition:background .15s; border-left:3px solid transparent; margin:0;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {display:none !important;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {background:rgba(255,255,255,.07);}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background:linear-gradient(90deg,rgba(59,130,246,.28),rgba(59,130,246,.06)); border-left:3px solid #60a5fa;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:last-child {display:flex; align-items:center; gap:12px;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label p {font-size:14.5px; font-weight:500; margin:0; color:#cfd8f3 !important;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {color:#fff !important; font-weight:600;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:last-child::before {content:""; width:18px; height:18px; flex:0 0 18px;
  background-color:#9fb2e6; -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat; -webkit-mask-size:contain; mask-size:contain;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) > div:last-child::before {background-color:#93c5fd;}
.usercard {display:flex; align-items:center; gap:10px; padding:12px; margin-top:22px; border-radius:12px;
  background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.08);}
.usercard .av {width:36px; height:36px; border-radius:50%; background:#2563eb; display:flex; align-items:center;
  justify-content:center; font-weight:700; color:#fff !important;}
.usercard .n {font-size:13.5px; font-weight:600; color:#fff !important;} .usercard .r {font-size:11.5px; opacity:.65;}
""" + icon_css + "</style>", unsafe_allow_html=True)
 
 
# =============================================================================
# MAIN
# =============================================================================
init()
allowed = ROLE_PAGES[S.settings["role"]]
inject_css(allowed)
if S.get("nav") not in allowed:
    S.nav = "Dashboard"
unread = sum(1 for e in S.events if not e["read"])
with st.sidebar:
    st.markdown("<div class='brand'><div class='logo'>X</div><div><div class='t1'>Xloop</div>"
                "<div class='t2'>People &amp; Culture</div></div></div><div class='navlbl'>Recruitment Suite</div>", unsafe_allow_html=True)
    page = st.radio("Menu", allowed, key="nav", label_visibility="collapsed",
                    format_func=lambda n: f"{n}  ({unread})" if (n == "Notifications" and unread) else n)
    initials = "".join(w[0] for w in S.settings["user"].split()[:2]).upper() or "U"
    st.markdown(f"<div class='usercard'><div class='av'>{initials}</div><div><div class='n'>{S.settings['user']}</div>"
                f"<div class='r'>{S.settings['role']}</div></div></div>", unsafe_allow_html=True)
 
{"Dashboard": page_dashboard, "Jobs": page_jobs, "AI Matching": page_matching, "CV Database": page_cvdb,
 "Pipeline": page_pipeline, "Interviews": page_interviews, "Offers & Onboarding": page_offers,
 "Automation": page_automation, "Communication": page_comm, "Analytics": page_analytics,
 "Notifications": page_notifications, "Settings": page_settings}[page]()
 

