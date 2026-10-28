
"""
Xloop - Recruitment Management Dashboard (Frontend)
People & Culture Department
 
Run:
    pip install streamlit pandas
    streamlit run xloop_dashboard.py
 
Note: Abhi sab data st.session_state mein hai (mock). Backend, AI agent,
automation aur database baad mein "BACKEND HOOK" wali jaghon par lag jayenge.
"""
import random
from datetime import date, datetime, timedelta
 
import pandas as pd
import streamlit as st
 
st.set_page_config(page_title="Xloop | Recruitment Dashboard", page_icon="♾️", layout="wide")
 
TODAY = date(2026, 10, 28)
STAGES = ["Applied", "Shortlisted", "On Hold", "Interview", "Offered", "Hired", "Rejected"]
DEPARTMENTS = ["IT", "Finance", "HR", "Marketing", "Operations", "Sales"]
ALL_SKILLS = ["React", "JavaScript", "Node.js", "HTML", "CSS", "Python", "SQL", "Excel", "Power BI",
              "Recruitment", "Communication", "UI/UX", "Figma", "Django", "Accounting", "SEO", "Sales"]
 
# ----------------------------------------------------------------------------
# CSS
# ----------------------------------------------------------------------------
st.markdown(
    """
<style>
.block-container {padding-top: 1.2rem; max-width: 1400px;}
[data-testid="stSidebar"] {background: #0f1b3d;}
[data-testid="stSidebar"] * {color: #e8ecf8 !important;}
.hdr {background: linear-gradient(90deg,#10235c,#1b3a8a); color: #fff; padding: 18px 26px;
      border-radius: 14px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;}
.hdr h2 {margin: 0; font-size: 26px; color:#fff;} .hdr p {margin: 2px 0 0; opacity: .8; font-size: 14px;}
.hdr .right {text-align: right; font-weight: 600;}
.step {border-radius: 12px; padding: 12px 12px 8px; min-height: 150px; border: 1px solid #e3e7f1;}
.step h4 {margin: 0 0 6px; font-size: 14px;} .step ul {padding-left: 16px; margin: 0; font-size: 12px; color:#444;}
.s1{background:#eaf1ff}.s2{background:#eef0ff}.s3{background:#e8f9ef}.s4{background:#eaf7ff}
.s5{background:#f3ecff}.s6{background:#e6f8f3}.s7{background:#fff6e5}
.num {display:inline-block; width:22px; height:22px; border-radius:50%; background:#2b59d6; color:#fff;
      text-align:center; line-height:22px; font-size:12px; margin-right:6px;}
.metric {border-radius: 14px; padding: 16px 18px; border: 1px solid #e3e7f1;}
.metric .l {font-size: 13px; color: #555;} .metric .v {font-size: 30px; font-weight: 700; color:#111;}
.metric .d {font-size: 12px; color: #16a34a; font-weight: 600;}
.m1{background:#eaf1ff}.m2{background:#e8f9ef}.m3{background:#f3ecff}.m4{background:#fff3e0}
.chip {display:inline-block; padding: 2px 10px; margin: 2px 4px 2px 0; border-radius: 999px;
       background:#eaf1ff; color:#1e40af; font-size: 12px; border:1px solid #c7d6f7;}
.match {background:#dcfce7; color:#166534; padding:3px 10px; border-radius:8px; font-weight:700; font-size:13px;}
.badge {padding:2px 10px; border-radius:8px; font-size:12px; font-weight:600;}
.b-Applied{background:#dcfce7;color:#166534}.b-Shortlisted{background:#ede9fe;color:#5b21b6}
.b-On.Hold,.b-OnHold{background:#fef3c7;color:#92400e}.b-Interview{background:#dbeafe;color:#1e40af}
.b-Offered{background:#ffedd5;color:#9a3412}.b-Hired{background:#bbf7d0;color:#14532d}
.b-Rejected{background:#fee2e2;color:#991b1b}
.foot {background:#f1f0ff; border-radius:12px; padding:10px 18px; margin-top:22px; color:#333; font-size:14px;}
</style>
""",
    unsafe_allow_html=True,
)
 
 
# ----------------------------------------------------------------------------
# Mock data (BACKEND HOOK: replace with database queries later)
# ----------------------------------------------------------------------------
def init_state():
    if "ready" in st.session_state:
        return
    jobs = [
        dict(id=1, title="Web Developer", department="IT", skills=["React", "JavaScript", "Node.js", "HTML", "CSS"],
             min_exp=3, sal_min=120000, sal_max=160000, manager="Sadam Ahmed", status="Open", created=date(2026, 10, 10)),
        dict(id=2, title="Data Analyst", department="Finance", skills=["Python", "SQL", "Excel", "Power BI"],
             min_exp=3, sal_min=100000, sal_max=140000, manager="Sadam Ahmed", status="Open", created=date(2026, 10, 12)),
        dict(id=3, title="HR Associate", department="HR", skills=["Recruitment", "Communication", "Excel"],
             min_exp=2, sal_min=80000, sal_max=110000, manager="Sadam Ahmed", status="Open", created=date(2026, 10, 14)),
        dict(id=4, title="UI/UX Designer", department="Marketing", skills=["Figma", "UI/UX", "HTML", "CSS"],
             min_exp=2, sal_min=90000, sal_max=130000, manager="Sadam Ahmed", status="Open", created=date(2026, 10, 15)),
        dict(id=5, title="Backend Developer", department="IT", skills=["Python", "Django", "SQL", "Node.js"],
             min_exp=3, sal_min=130000, sal_max=180000, manager="Sadam Ahmed", status="On Hold", created=date(2026, 10, 5)),
    ]
    raw = [
        ("Ayesha Malik", 1, ["React", "JavaScript", "Node.js", "HTML", "CSS"], 4, "Karachi", 20, "New"),
        ("Hassan Shah", 2, ["Python", "SQL", "Excel", "Power BI"], 3, "Lahore", 19, "Existing"),
        ("Zain Raza", 3, ["Recruitment", "Communication", "Excel"], 2, "Islamabad", 18, "New"),
        ("Sana Khan", 4, ["Figma", "UI/UX", "HTML"], 3, "Karachi", 17, "Existing"),
        ("Muhammad Bilal", 5, ["Python", "Django", "SQL"], 5, "Hyderabad", 16, "New"),
        ("Fatima Noor", 1, ["React", "HTML", "CSS"], 2, "Lahore", 15, "New"),
        ("Usman Ali", 2, ["SQL", "Excel"], 1, "Sukkur", 14, "Existing"),
        ("Hina Tariq", 3, ["Recruitment", "Communication"], 4, "Karachi", 13, "New"),
        ("Ahmed Raza", 5, ["Node.js", "SQL", "Python"], 4, "Multan", 12, "Existing"),
        ("Mariam Siddiqui", 4, ["Figma", "UI/UX", "CSS", "HTML"], 5, "Islamabad", 11, "New"),
        ("Kamran Javed", 1, ["JavaScript", "HTML", "CSS"], 1, "Larkana", 10, "New"),
        ("Rabia Aslam", 2, ["Python", "SQL", "Power BI", "Excel"], 6, "Lahore", 9, "Existing"),
    ]
    stage_seed = ["Shortlisted", "Shortlisted", "Applied", "Applied", "Interview", "Applied",
                  "Rejected", "On Hold", "Applied", "Hired", "Applied", "Offered"]
    cands = []
    for i, (n, jid, sk, ex, city, ago, src) in enumerate(raw, start=1):
        job = next(j for j in jobs if j["id"] == jid)
        cands.append(dict(
            id=i, name=n, job_id=jid, position=job["title"], department=job["department"], skills=sk, exp=ex,
            city=city, applied=TODAY - timedelta(days=ago - 8 if ago > 8 else 0) - timedelta(days=0),
            source=src, stage=stage_seed[i - 1], email=n.lower().replace(" ", ".") + "@mail.com",
            sal_min=job["sal_min"] - 5000 * (3 - min(ex, 3)), sal_max=job["sal_max"] - 5000 * (3 - min(ex, 3)),
            notes=[], cv_name=f"{n.replace(' ', '_')}_CV.pdf",
        ))
    st.session_state.jobs = jobs
    st.session_state.cands = cands
    st.session_state.interviews = [
        dict(id=1, cand_id=5, date=TODAY + timedelta(days=2), time="11:00", interviewer="Sadam Ahmed",
             mode="Onsite", status="Scheduled", feedback=""),
    ]
    st.session_state.notifs = [
        dict(id=1, text="New CV received: Ayesha Malik (Web Developer)", channel="In-app", read=False, time="09:15"),
        dict(id=2, text="Interview scheduled with Muhammad Bilal", channel="Email", read=False, time="09:30"),
        dict(id=3, text="Hassan Shah shortlisted", channel="SMS", read=False, time="10:05"),
    ]
    st.session_state.settings = dict(email=True, sms=True, inapp=True, role="HR - People & Culture", auto_notify=True)
    st.session_state.ready = True
 
 
init_state()
S = st.session_state
 
 
# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def notify(text, channel="In-app"):
    """BACKEND HOOK: trigger automation (email/SMS/n8n/etc.) here later."""
    if not S.settings["auto_notify"]:
        return
    ok = {"Email": S.settings["email"], "SMS": S.settings["sms"], "In-app": S.settings["inapp"]}
    for ch in ["In-app", "Email", "SMS"]:
        if ch == channel or channel == "All":
            if ok[ch]:
                S.notifs.insert(0, dict(id=len(S.notifs) + 1, text=text, channel=ch, read=False,
                                        time=datetime.now().strftime("%H:%M")))
 
 
def job_of(c):
    return next((j for j in S.jobs if j["id"] == c["job_id"]), None)
 
 
def match_pct(c):
    """BACKEND HOOK: replace with AI agent scoring later."""
    j = job_of(c)
    if not j:
        return 50
    overlap = len(set(c["skills"]) & set(j["skills"])) / max(len(j["skills"]), 1)
    exp_score = min(c["exp"] / max(j["min_exp"], 1), 1.0)
    return int(round(overlap * 75 + exp_score * 25))
 
 
def missing_skills(c):
    j = job_of(c)
    return [s for s in j["skills"] if s not in c["skills"]] if j else []
 
 
def set_stage(cid, stage):
    c = next(x for x in S.cands if x["id"] == cid)
    c["stage"] = stage
    chan = {"Shortlisted": "SMS", "Rejected": "Email", "Offered": "Email", "Hired": "All", "Interview": "Email"}.get(stage, "In-app")
    notify(f"{c['name']} moved to {stage}", chan)
 
 
def badge(stage):
    return f"<span class='badge b-{stage.replace(' ', '')}'>{stage}</span>"
 
 
def chips(items):
    return "".join(f"<span class='chip'>{s}</span>" for s in items)
 
 
def exp_band(e):
    return "0-2 yrs" if e <= 2 else ("3-5 yrs" if e <= 5 else "6+ yrs")
 
 
def cands_df(cands):
    return pd.DataFrame([dict(Name=c["name"], Position=c["position"], Department=c["department"],
                              Applied=c["applied"], Source=c["source"], Stage=c["stage"],
                              Match=f"{match_pct(c)}%") for c in cands])
 
 
def header(title, sub="Smarter Hiring  |  Faster Process  |  Better Talent"):
    st.markdown(
        f"<div class='hdr'><div><h2>♾️ Xloop &nbsp;|&nbsp; {title}</h2><p>{sub}</p></div>"
        f"<div class='right'>People &amp; Culture Department<br><span style='font-weight:400;font-size:13px'>"
        f"Automate • Filter • Hire • Grow</span></div></div>", unsafe_allow_html=True)
 
 
def filter_bar(key):
    c1, c2, c3, c4, c5 = st.columns([2.2, 1.4, 1.4, 1.4, 1.4])
    kw = c1.text_input("Search by keyword", key=f"kw_{key}", placeholder="Name, skill, position...")
    dep = c2.selectbox("Department", ["All"] + DEPARTMENTS, key=f"dep_{key}")
    sk = c3.selectbox("Subject / Skills", ["All"] + ALL_SKILLS, key=f"sk_{key}")
    exp = c4.selectbox("Experience Level", ["All", "0-2 yrs", "3-5 yrs", "6+ yrs"], key=f"ex_{key}")
    dt = c5.selectbox("Date Applied", ["All", "Last 7 days", "Last 14 days", "Newest first", "Oldest first"], key=f"dt_{key}")
    c6, c7 = st.columns([1, 1])
    pos = c6.selectbox("Position", ["All"] + sorted({j["title"] for j in S.jobs}), key=f"pos_{key}")
    src = c7.selectbox("New / Existing CV", ["All", "New", "Existing"], key=f"src_{key}")
 
    out = list(S.cands)
    if kw:
        k = kw.lower()
        out = [c for c in out if k in c["name"].lower() or k in c["position"].lower()
               or any(k in s.lower() for s in c["skills"])]
    if dep != "All": out = [c for c in out if c["department"] == dep]
    if sk != "All": out = [c for c in out if sk in c["skills"]]
    if exp != "All": out = [c for c in out if exp_band(c["exp"]) == exp]
    if pos != "All": out = [c for c in out if c["position"] == pos]
    if src != "All": out = [c for c in out if c["source"] == src]
    if dt == "Last 7 days": out = [c for c in out if (TODAY - c["applied"]).days <= 7]
    elif dt == "Last 14 days": out = [c for c in out if (TODAY - c["applied"]).days <= 14]
    elif dt == "Newest first": out.sort(key=lambda c: c["applied"], reverse=True)
    elif dt == "Oldest first": out.sort(key=lambda c: c["applied"])
    return out
 
 
def candidate_detail(cid, key):
    c = next(x for x in S.cands if x["id"] == cid)
    m = match_pct(c)
    top = st.columns([4, 1])
    top[0].markdown(f"### {c['name']}")
    top[0].caption(f"{c['position']} | {c['exp']}+ yrs exp | {c['city']} | {c['email']}")
    top[1].markdown(f"<span class='match'>Match {m}%</span>", unsafe_allow_html=True)
    st.markdown(badge(c["stage"]), unsafe_allow_html=True)
 
    t1, t2, t3, t4 = st.tabs(["Summary", "Skills", "Experience", "Documents"])
    with t1:
        st.write(f"**Expected Salary:** PKR {c['sal_min']//1000}K - {c['sal_max']//1000}K")
        st.markdown("**Key Skills**<br>" + chips(c["skills"]), unsafe_allow_html=True)
        st.write(f"**Experience:** {c['exp']}+ years")
    with t2:
        st.markdown("**Matched skills**<br>" + chips([s for s in c["skills"] if s in (job_of(c) or {}).get("skills", [])]),
                    unsafe_allow_html=True)
        ms = missing_skills(c)
        st.markdown("**Missing skills (AI)**<br>" + (chips(ms) if ms else "None 🎉"), unsafe_allow_html=True)
    with t3:
        j = job_of(c)
        need = j["min_exp"] if j else 0
        st.progress(min(c["exp"] / max(need, 1), 1.0), text=f"{c['exp']} yrs vs {need} yrs required")
    with t4:
        st.write(f"📄 {c['cv_name']}")
        st.download_button("Download CV (sample)", data=f"CV of {c['name']}\nSkills: {', '.join(c['skills'])}",
                           file_name=c["cv_name"].replace(".pdf", ".txt"), key=f"dl_{key}_{cid}")
 
    b = st.columns(5)
    if b[0].button("⭐ Shortlist", key=f"sl_{key}_{cid}", type="primary", use_container_width=True):
        set_stage(cid, "Shortlisted"); st.rerun()
    if b[1].button("✖ Reject", key=f"rj_{key}_{cid}", use_container_width=True):
        set_stage(cid, "Rejected"); st.rerun()
    if b[2].button("⏸ Hold", key=f"hd_{key}_{cid}", use_container_width=True):
        set_stage(cid, "On Hold"); st.rerun()
    if b[3].button("📅 Interview", key=f"iv_{key}_{cid}", use_container_width=True):
        S[f"sched_{key}_{cid}"] = True
    if b[4].button("💼 Offer", key=f"of_{key}_{cid}", use_container_width=True):
        set_stage(cid, "Offered"); st.rerun()
 
    if S.get(f"sched_{key}_{cid}"):
        with st.container(border=True):
            st.markdown("**Schedule interview**")
            d1, d2, d3, d4 = st.columns(4)
            d = d1.date_input("Date", TODAY + timedelta(days=3), key=f"d_{key}_{cid}")
            t = d2.time_input("Time", datetime.strptime("11:00", "%H:%M").time(), key=f"t_{key}_{cid}")
            who = d3.text_input("Interviewer", "Sadam Ahmed", key=f"w_{key}_{cid}")
            mode = d4.selectbox("Mode", ["Onsite", "Online", "Phone"], key=f"m_{key}_{cid}")
            if st.button("Confirm interview", key=f"ci_{key}_{cid}"):
                S.interviews.append(dict(id=len(S.interviews) + 1, cand_id=cid, date=d, time=t.strftime("%H:%M"),
                                         interviewer=who, mode=mode, status="Scheduled", feedback=""))
                set_stage(cid, "Interview")
                notify(f"Interview scheduled for {c['name']} on {d} {t.strftime('%H:%M')}", "Email")
                S[f"sched_{key}_{cid}"] = False
                st.rerun()
 
    st.markdown("**Recruiter notes**")
    for n in c["notes"]:
        st.caption(f"📝 {n}")
    nn = st.text_input("Add note", key=f"nn_{key}_{cid}")
    if st.button("Save note", key=f"sn_{key}_{cid}") and nn:
        c["notes"].append(f"{datetime.now():%d %b %H:%M} - {nn}")
        st.rerun()
 
 
# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
NAV = ["Dashboard", "Jobs", "Candidates", "CV Database", "Shortlisted", "Interviews",
       "Notifications", "Hiring & Onboarding", "Reports", "Settings"]
NAV_ICONS = {
    "Dashboard": "<rect x='3' y='3' width='7' height='7'/><rect x='14' y='3' width='7' height='7'/><rect x='14' y='14' width='7' height='7'/><rect x='3' y='14' width='7' height='7'/>",
    "Jobs": "<rect x='2' y='7' width='20' height='14' rx='2'/><path d='M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16'/>",
    "Candidates": "<path d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M23 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/>",
    "CV Database": "<ellipse cx='12' cy='5' rx='9' ry='3'/><path d='M21 12c0 1.66-4 3-9 3s-9-1.34-9-3'/><path d='M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5'/>",
    "Shortlisted": "<polygon points='12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2'/>",
    "Interviews": "<rect x='3' y='4' width='18' height='18' rx='2'/><line x1='16' y1='2' x2='16' y2='6'/><line x1='8' y1='2' x2='8' y2='6'/><line x1='3' y1='10' x2='21' y2='10'/>",
    "Notifications": "<path d='M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9'/><path d='M13.73 21a2 2 0 0 1-3.46 0'/>",
    "Hiring & Onboarding": "<path d='M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/><circle cx='8.5' cy='7' r='4'/><polyline points='17 11 19 13 23 9'/>",
    "Reports": "<line x1='12' y1='20' x2='12' y2='10'/><line x1='18' y1='20' x2='18' y2='4'/><line x1='6' y1='20' x2='6' y2='16'/>",
    "Settings": "<line x1='4' y1='21' x2='4' y2='14'/><line x1='4' y1='10' x2='4' y2='3'/><line x1='12' y1='21' x2='12' y2='12'/><line x1='12' y1='8' x2='12' y2='3'/><line x1='20' y1='21' x2='20' y2='16'/><line x1='20' y1='12' x2='20' y2='3'/><line x1='1' y1='14' x2='7' y2='14'/><line x1='9' y1='8' x2='15' y2='8'/><line x1='17' y1='16' x2='23' y2='16'/>",
}
_icon_css = "".join(
    f"""section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-of-type({i}) > div:last-child::before
    {{-webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{NAV_ICONS[n]}</svg>");
      mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{NAV_ICONS[n]}</svg>");}}\n"""
    for i, n in enumerate(NAV, start=1))
st.markdown(
    """<style>
section[data-testid="stSidebar"] {background: linear-gradient(180deg,#0b1533 0%,#101f4a 100%); border-right: 1px solid #1c2c5c;}
section[data-testid="stSidebar"] > div {padding-top: 0.5rem;}
.brand {display:flex; align-items:center; gap:12px; padding: 10px 8px 18px; border-bottom:1px solid rgba(255,255,255,.08); margin-bottom:14px;}
.brand .logo {width:40px; height:40px; border-radius:11px; background:linear-gradient(135deg,#3b82f6,#7c3aed);
  display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:800; color:#fff !important;}
.brand .t1 {font-size:20px; font-weight:700; letter-spacing:.3px; line-height:1.1; color:#fff !important;}
.brand .t2 {font-size:11px; opacity:.65; letter-spacing:.6px; text-transform:uppercase;}
.navlbl {font-size:11px; letter-spacing:1.2px; text-transform:uppercase; opacity:.5; padding: 4px 10px 8px;}
section[data-testid="stSidebar"] div[role="radiogroup"] {gap: 2px;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label {width:100%; padding: 10px 12px; border-radius: 10px;
  cursor:pointer; transition: background .15s; border-left: 3px solid transparent; margin:0;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {display:none !important;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {background: rgba(255,255,255,.07);}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background: linear-gradient(90deg, rgba(59,130,246,.28), rgba(59,130,246,.06)); border-left: 3px solid #60a5fa;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:last-child {display:flex; align-items:center; gap:12px;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label p {font-size:14.5px; font-weight:500; margin:0; color:#cfd8f3 !important;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {color:#fff !important; font-weight:600;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:last-child::before {
  content:""; width:18px; height:18px; flex:0 0 18px; background-color:#9fb2e6;
  -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat; -webkit-mask-size:contain; mask-size:contain;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) > div:last-child::before {background-color:#93c5fd;}
.usercard {display:flex; align-items:center; gap:10px; padding:12px; margin-top:26px; border-radius:12px;
  background: rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.08);}
.usercard .av {width:36px; height:36px; border-radius:50%; background:#2563eb; display:flex; align-items:center;
  justify-content:center; font-weight:700; color:#fff !important;}
.usercard .n {font-size:13.5px; font-weight:600; color:#fff !important; line-height:1.2;}
.usercard .r {font-size:11.5px; opacity:.65;}
""" + _icon_css + "</style>",
    unsafe_allow_html=True,
)
 
unread = sum(1 for n in S.notifs if not n["read"])
 
 
def nav_label(n):
    return f"{n}  ({unread})" if (n == "Notifications" and unread) else n
 
 
with st.sidebar:
    st.markdown(
        "<div class='brand'><div class='logo'>X</div><div><div class='t1'>Xloop</div>"
        "<div class='t2'>People &amp; Culture</div></div></div><div class='navlbl'>Recruitment Workspace</div>",
        unsafe_allow_html=True)
    page = st.radio("Menu", NAV, format_func=nav_label, label_visibility="collapsed", key="nav")
    st.markdown(
        f"<div class='usercard'><div class='av'>SA</div><div><div class='n'>Sadam Ahmed</div>"
        f"<div class='r'>{S.settings['role']}</div></div></div>", unsafe_allow_html=True)
# ----------------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------------
if page == "Dashboard":
    header("Recruitment Dashboard")
    steps = [("Job Requisition", ["Create new job opening", "Add skills & experience", "Set salary range", "Assign manager"]),
             ("CV Collection", ["Upload / Import CVs", "Auto-extract info", "Track new & existing", "Central database"]),
             ("Smart Filtering", ["By subject/skills", "By date", "By department", "By experience"]),
             ("AI Suggests Best CVs", ["Analyzes matching CVs", "Ranks candidates", "Shows expected salary", "Match %"]),
             ("Review & Shortlist", ["View profiles", "Compare skills", "Shortlist / Reject", "Add notes"]),
             ("Notifications", ["Email", "SMS / In-app", "Interview schedule", "Status updates"]),
             ("Hire & Onboard", ["Move to offer", "Send offer letter", "Onboard employee", "Update records"])]
    cols = st.columns(7)
    for i, (t, items) in enumerate(steps, start=1):
        cols[i - 1].markdown(
            f"<div class='step s{i}'><h4><span class='num'>{i}</span>{t}</h4><ul>"
            + "".join(f"<li>{x}</li>" for x in items) + "</ul></div>", unsafe_allow_html=True)
    st.write("")
 
    total = len(S.cands)
    new = sum(1 for c in S.cands if c["source"] == "New")
    short = sum(1 for c in S.cands if c["stage"] == "Shortlisted")
    hired = sum(1 for c in S.cands if c["stage"] == "Hired")
    m = st.columns(4)
    for col, cls, lbl, val, d in zip(m, ["m1", "m2", "m3", "m4"],
                                     ["Total Applications", "New CVs", "Shortlisted", "Hired"],
                                     [total, new, short, hired], ["↑ 12%", "↑ 18%", "↑ 10%", "↑ 5%"]):
        col.markdown(f"<div class='metric {cls}'><div class='l'>{lbl}</div><div class='v'>{val}</div>"
                     f"<div class='d'>{d}</div></div>", unsafe_allow_html=True)
    st.write("")
 
    left, right = st.columns([2.1, 1])
    with left:
        with st.container(border=True):
            st.markdown("#### 🔎 Filters")
            filtered = filter_bar("dash")
        st.markdown("#### Recent CVs (New & Existing)")
        st.dataframe(cands_df(filtered), use_container_width=True, hide_index=True)
 
        st.markdown("#### Top Suggested Candidates (AI)")
        ranked = sorted(filtered, key=match_pct, reverse=True)[:4]
        for c in ranked:
            with st.container(border=True):
                a, b, d = st.columns([3, 1, 2])
                a.markdown(f"**{c['name']}**  \n{c['position']} · {c['exp']}+ yrs")
                b.markdown(f"<span class='match'>Match {match_pct(c)}%</span>", unsafe_allow_html=True)
                d.caption(f"Expected: PKR {c['sal_min']//1000}K - {c['sal_max']//1000}K")
    with right:
        st.markdown("#### 👤 Candidate Detail")
        if filtered:
            opts = {f"{c['name']} ({match_pct(c)}%)": c["id"] for c in sorted(filtered, key=match_pct, reverse=True)}
            pick = st.selectbox("Select candidate", list(opts), key="dash_pick")
            with st.container(border=True):
                candidate_detail(opts[pick], "dash")
        else:
            st.info("Filters ke mutabiq koi candidate nahi mila.")
    st.markdown("<div class='foot'>From Manual Work to Smart Hiring — Save Time | Reduce Effort | Find the Right Talent</div>",
                unsafe_allow_html=True)
 
elif page == "Jobs":
    header("Job / Vacancy Management")
    with st.expander("➕ Create new vacancy", expanded=False):
        with st.form("job_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            title = c1.text_input("Position title")
            dep = c2.selectbox("Department", DEPARTMENTS)
            mgr = c3.text_input("Hiring manager", "Sadam Ahmed")
            skills = st.multiselect("Required skills / subject", ALL_SKILLS)
            c4, c5, c6 = st.columns(3)
            mexp = c4.number_input("Min experience (yrs)", 0, 20, 2)
            smin = c5.number_input("Salary min (PKR)", 0, 2000000, 80000, step=5000)
            smax = c6.number_input("Salary max (PKR)", 0, 2000000, 120000, step=5000)
            if st.form_submit_button("Create vacancy", type="primary"):
                if title:
                    S.jobs.append(dict(id=max(j["id"] for j in S.jobs) + 1, title=title, department=dep, skills=skills,
                                       min_exp=mexp, sal_min=smin, sal_max=smax, manager=mgr, status="Open", created=TODAY))
                    notify(f"New vacancy created: {title}", "In-app")
                    st.success("Vacancy create ho gayi ✅"); st.rerun()
                else:
                    st.error("Position title zaroori hai.")
    st.markdown("#### All vacancies")
    for j in S.jobs:
        apps = sum(1 for c in S.cands if c["job_id"] == j["id"])
        with st.container(border=True):
            a, b, c_, d = st.columns([3, 3, 1.5, 1.5])
            a.markdown(f"**{j['title']}**  \n{j['department']} · Manager: {j['manager']}")
            b.markdown(chips(j["skills"]) + f"<br><small>{j['min_exp']}+ yrs · PKR {j['sal_min']//1000}K-{j['sal_max']//1000}K</small>",
                       unsafe_allow_html=True)
            c_.metric("Applicants", apps)
            new_status = d.selectbox("Status", ["Open", "On Hold", "Closed"], index=["Open", "On Hold", "Closed"].index(j["status"]),
                                     key=f"js_{j['id']}")
            if new_status != j["status"]:
                j["status"] = new_status; st.rerun()
 
elif page == "Candidates":
    header("Candidate Management")
    filtered = filter_bar("cand")
    stage_f = st.multiselect("Stage", STAGES, default=STAGES, key="cand_stage")
    filtered = [c for c in filtered if c["stage"] in stage_f]
    l, r = st.columns([1.6, 1])
    with l:
        st.dataframe(cands_df(filtered), use_container_width=True, hide_index=True)
    with r:
        if filtered:
            pick = st.selectbox("Open profile", [f"{c['id']} - {c['name']}" for c in filtered], key="cand_pick")
            with st.container(border=True):
                candidate_detail(int(pick.split(" - ")[0]), "cand")
 
elif page == "CV Database":
    header("CV Database")
    t1, t2 = st.tabs(["⬆️ Upload / Import CV", "🔍 Search CV Database"])
    with t1:
        up = st.file_uploader("Upload CV (PDF / DOCX / TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=False)
        # BACKEND HOOK: AI/NLP CV parser goes here
        ex_name, ex_sk, ex_exp = "", [], 2
        if up is not None:
            text = ""
            if up.name.endswith(".txt"):
                text = up.read().decode("utf-8", errors="ignore")
            ex_name = up.name.rsplit(".", 1)[0].replace("_", " ").replace("CV", "").strip().title()
            ex_sk = [s for s in ALL_SKILLS if s.lower() in (text + " " + up.name).lower()]
            st.success("Key information auto-extract ho gayi (demo). Neeche check karke save karein.")
        with st.form("cv_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Candidate name", ex_name)
            email = c2.text_input("Email")
            city = c3.text_input("City", "Karachi")
            jtitle = st.selectbox("Applying for", [f"{j['id']} - {j['title']}" for j in S.jobs])
            skills = st.multiselect("Skills", ALL_SKILLS, default=ex_sk)
            exp = st.number_input("Experience (yrs)", 0, 30, ex_exp)
            if st.form_submit_button("Save to CV database", type="primary") and name:
                j = next(x for x in S.jobs if x["id"] == int(jtitle.split(" - ")[0]))
                S.cands.append(dict(id=max(c["id"] for c in S.cands) + 1, name=name, job_id=j["id"], position=j["title"],
                                    department=j["department"], skills=skills, exp=int(exp), city=city, applied=TODAY,
                                    source="New", stage="Applied", email=email or "n/a", sal_min=j["sal_min"],
                                    sal_max=j["sal_max"], notes=[], cv_name=up.name if up else f"{name}_CV.pdf"))
                notify(f"New CV received: {name} ({j['title']})", "In-app")
                st.success("CV save ho gayi ✅"); st.rerun()
    with t2:
        res = filter_bar("cvdb")
        st.caption(f"{len(res)} CV(s) found")
        st.dataframe(cands_df(res), use_container_width=True, hide_index=True)
        if res:
            pick = st.selectbox("CV preview", [f"{c['id']} - {c['name']}" for c in res], key="cv_prev")
            c = next(x for x in S.cands if x["id"] == int(pick.split(" - ")[0]))
            with st.container(border=True):
                st.markdown(f"**{c['name']}** — {c['position']} ({c['city']})")
                st.markdown(chips(c["skills"]), unsafe_allow_html=True)
                st.write(f"Experience: {c['exp']} yrs | Applied: {c['applied']} | File: {c['cv_name']}")
                st.write("**CV history:** Applied → " + c["stage"])
 
elif page == "Shortlisted":
    header("Shortlisted Candidates")
    sl = [c for c in S.cands if c["stage"] == "Shortlisted"]
    if not sl:
        st.info("Abhi koi shortlisted candidate nahi.")
    for c in sorted(sl, key=match_pct, reverse=True):
        with st.container(border=True):
            a, b, d = st.columns([3, 1, 3])
            a.markdown(f"**{c['name']}** · {c['position']}  \n{c['exp']}+ yrs · PKR {c['sal_min']//1000}K-{c['sal_max']//1000}K")
            b.markdown(f"<span class='match'>{match_pct(c)}%</span>", unsafe_allow_html=True)
            x = d.columns(3)
            if x[0].button("📅 Interview", key=f"sli_{c['id']}"):
                S.interviews.append(dict(id=len(S.interviews) + 1, cand_id=c["id"], date=TODAY + timedelta(days=3),
                                         time="11:00", interviewer="Sadam Ahmed", mode="Onsite", status="Scheduled", feedback=""))
                set_stage(c["id"], "Interview"); st.rerun()
            if x[1].button("⏸ Hold", key=f"slh_{c['id']}"):
                set_stage(c["id"], "On Hold"); st.rerun()
            if x[2].button("✖ Reject", key=f"slr_{c['id']}"):
                set_stage(c["id"], "Rejected"); st.rerun()
 
elif page == "Interviews":
    header("Interview Management")
    names = {c["id"]: c["name"] for c in S.cands}
    with st.expander("➕ Schedule new interview"):
        with st.form("iv_form", clear_on_submit=True):
            c1, c2, c3, c4, c5 = st.columns(5)
            who = c1.selectbox("Candidate", [f"{c['id']} - {c['name']}" for c in S.cands if c["stage"] not in ("Hired", "Rejected")])
            d = c2.date_input("Date", TODAY + timedelta(days=2))
            t = c3.time_input("Time", datetime.strptime("11:00", "%H:%M").time())
            iw = c4.text_input("Interviewer", "Sadam Ahmed")
            mode = c5.selectbox("Mode", ["Onsite", "Online", "Phone"])
            if st.form_submit_button("Schedule", type="primary"):
                cid = int(who.split(" - ")[0])
                S.interviews.append(dict(id=len(S.interviews) + 1, cand_id=cid, date=d, time=t.strftime("%H:%M"),
                                         interviewer=iw, mode=mode, status="Scheduled", feedback=""))
                set_stage(cid, "Interview"); notify(f"Interview scheduled for {names[cid]} on {d}", "Email")
                st.rerun()
    st.markdown("#### Interview list")
    for iv in sorted(S.interviews, key=lambda x: (x["date"], x["time"])):
        with st.container(border=True):
            a, b, c_ = st.columns([3, 2, 3])
            a.markdown(f"**{names.get(iv['cand_id'])}**  \n📅 {iv['date']} {iv['time']} · {iv['mode']}")
            b.write(f"Interviewer: {iv['interviewer']}")
            iv["status"] = c_.selectbox("Status", ["Scheduled", "Completed", "Cancelled", "No-show"],
                                        index=["Scheduled", "Completed", "Cancelled", "No-show"].index(iv["status"]),
                                        key=f"ivs_{iv['id']}")
            iv["feedback"] = st.text_input("Feedback", iv["feedback"], key=f"ivf_{iv['id']}")
            if st.button("🔔 Send reminder", key=f"ivr_{iv['id']}"):
                notify(f"Reminder: interview with {names.get(iv['cand_id'])} on {iv['date']} {iv['time']}", "All")
                st.toast("Reminder bhej diya gaya")
 
elif page == "Notifications":
    header("Automatic Notifications")
    c1, c2 = st.columns([1, 1])
    if c1.button("✅ Mark all as read"):
        for n in S.notifs: n["read"] = True
        st.rerun()
    if c2.button("🗑️ Clear all"):
        S.notifs = []; st.rerun()
    for n in S.notifs:
        icon = {"Email": "✉️", "SMS": "💬", "In-app": "🔔"}[n["channel"]]
        st.markdown(f"{'🔵' if not n['read'] else '⚪'} {icon} **{n['channel']}** · {n['time']} — {n['text']}")
 
elif page == "Hiring & Onboarding":
    header("Hiring & Onboarding")
    offered = [c for c in S.cands if c["stage"] == "Offered"]
    hired = [c for c in S.cands if c["stage"] == "Hired"]
    st.markdown("#### Offers pending")
    if not offered: st.info("Koi pending offer nahi.")
    for c in offered:
        with st.container(border=True):
            a, b = st.columns([4, 2])
            a.markdown(f"**{c['name']}** · {c['position']} · Offer: PKR {c['sal_max']//1000}K")
            if b.button("✅ Accept & Hire", key=f"hire_{c['id']}", type="primary"):
                set_stage(c["id"], "Hired"); st.rerun()
    st.markdown("#### Onboarding checklist")
    items = ["Offer letter signed", "Documents collected", "Employee record created", "Laptop & email assigned", "Orientation scheduled"]
    for c in hired:
        with st.expander(f"👤 {c['name']} — {c['position']}", expanded=True):
            done = sum(st.checkbox(it, key=f"ob_{c['id']}_{i}") for i, it in enumerate(items))
            st.progress(done / len(items), text=f"{done}/{len(items)} complete")
 
elif page == "Reports":
    header("Reports & Analytics")
    df = pd.DataFrame([dict(Department=c["department"], Stage=c["stage"], Position=c["position"],
                            Applied=c["applied"], Source=c["source"], Match=match_pct(c)) for c in S.cands])
    a, b = st.columns(2)
    a.markdown("#### Applications by department")
    a.bar_chart(df.groupby("Department").size())
    b.markdown("#### Hiring funnel (by stage)")
    b.bar_chart(df["Stage"].value_counts().reindex(STAGES).fillna(0))
    c, d = st.columns(2)
    c.markdown("#### CV statistics (New vs Existing)")
    c.bar_chart(df["Source"].value_counts())
    d.markdown("#### Applications over time")
    d.line_chart(df.groupby("Applied").size())
    st.markdown("#### Recruitment performance")
    k = st.columns(4)
    k[0].metric("Shortlist rate", f"{(df['Stage'].isin(['Shortlisted','Interview','Offered','Hired']).mean()*100):.0f}%")
    k[1].metric("Avg match %", f"{df['Match'].mean():.0f}%")
    k[2].metric("Open vacancies", sum(1 for j in S.jobs if j["status"] == "Open"))
    k[3].metric("Avg time-to-hire", "18 days")
    st.download_button("⬇️ Export report (CSV)", df.to_csv(index=False), "recruitment_report.csv")
 
elif page == "Settings":
    header("Settings")
    st.markdown("#### Notification channels")
    S.settings["email"] = st.toggle("Email notifications", S.settings["email"])
    S.settings["sms"] = st.toggle("SMS notifications", S.settings["sms"])
    S.settings["inapp"] = st.toggle("In-app notifications", S.settings["inapp"])
    S.settings["auto_notify"] = st.toggle("Auto-trigger notifications", S.settings["auto_notify"])
    st.markdown("#### Role-based access (optional)")
    S.settings["role"] = st.selectbox("Current role", ["HR - People & Culture", "Hiring Manager", "Interviewer", "Admin"],
                                      index=["HR - People & Culture", "Hiring Manager", "Interviewer", "Admin"].index(S.settings["role"]))
    st.markdown("#### Data")
    if st.button("♻️ Reset demo data"):
        for k_ in list(S.keys()): del S[k_]
        st.rerun()
    st.info("Backend, AI agent, automation aur database baad mein yahan connect honge.")
 

