import streamlit as st
import random
import time

st.set_page_config(page_title="Masood Ahmed Rajri 😂", page_icon="🤡", layout="centered")

# ---------- Custom CSS ----------
st.markdown("""
<style>
.big-title {
    font-size: 42px; font-weight: 900; text-align: center;
    background: linear-gradient(90deg, #ff0080, #ff8c00, #40e0d0);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.sub {text-align:center; font-size:18px; color:gray;}
.card {
    background:#fff3cd; padding:15px; border-radius:12px;
    border-left:6px solid #ff9800; font-size:18px; color:#000;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🤡 MASOOD AHMED RAJRI 🤡</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Official Trolling Portal – Sirf Masood ke liye</div>', unsafe_allow_html=True)
st.divider()

# ---------- Session State ----------
if "udhaar" not in st.session_state:
    st.session_state.udhaar = 0
if "nahi_count" not in st.session_state:
    st.session_state.nahi_count = 0

# ---------- Sidebar ----------
st.sidebar.title("🎮 Menu")
page = st.sidebar.radio("Kahan jana hai?", [
    "🏠 Home",
    "📊 Rajri Meter",
    "🔥 Roast Machine",
    "🦠 Virus Scan",
    "🧠 IQ Test",
    "💸 Udhaar Counter",
    "🙈 Button Pakro",
])

# ---------- HOME ----------
if page == "🏠 Home":
    st.header("Khush Aamdeed Masood Bhai! 🎉")
    st.write("Ye app **sirf aap ke liye** banayi gayi hai. Is mein har cheez 100% jhooti magar 100% mazedaar hai.")
    name = st.text_input("Apna naam likho:", "Masood Ahmed Rajri")
    if st.button("Mera Status Check Karo"):
        with st.spinner("Satellite se data aa raha hai..."):
            time.sleep(2)
        st.success(f"{name} ka status: **LEGEND (lekin sust wala)** 😎")
        st.balloons()

# ---------- RAJRI METER ----------
elif page == "📊 Rajri Meter":
    st.header("📊 Rajri Meter")
    st.write("Masood bhai ki sifaat ka scientific analysis:")
    stats = {
        "Sustti 😴": random.randint(85, 100),
        "Chai ka Nasha ☕": random.randint(90, 100),
        "Late Pohanchna ⏰": random.randint(88, 100),
        "Paisay Dena 💰": random.randint(0, 5),
        "Selfie ka Shauq 🤳": random.randint(80, 100),
        "Akal 🧠": random.randint(1, 15),
    }
    for k, v in stats.items():
        st.write(f"**{k}** — {v}%")
        st.progress(v)
    st.button("🔄 Dobara Scan Karo")
    st.caption("⚠️ Result har baar badal jata hai kyunke Masood bhi mood badalta rehta hai.")

# ---------- ROAST MACHINE ----------
elif page == "🔥 Roast Machine":
    st.header("🔥 Roast Machine")
    roasts = [
        "Masood itna late aata hai ke uski gari bhi keh ti hai: 'Bhai ab to jaldi kar'. ⏰",
        "Masood ka WiFi bhi us se tez chalta hai. 🐌",
        "Masood jab hanstaa hai to lagta hai generator start ho raha hai. 🔊",
        "Masood ne gym join kiya... sirf gym ki chai peenay ke liye. ☕",
        "Masood ki planning itni strong hai ke woh kal ka kaam parso par daal deta hai. 📅",
        "Google bhi Masood ke sawal sun kar kehta hai: 'Bhai tum khud soch lo'. 🤯",
        "Masood ne ek dafa jaldi uthne ki koshish ki thi... alarm ne bhi hairat se dekha. ⏰😲",
        "Masood ka phone 1% battery par bhi us se zyada active hota hai. 🔋",
        "Masood biryani dekh ke aise tez ho jata hai jaise Usain Bolt. 🍛🏃",
    ]
    if st.button("🔥 Mujhe Roast Karo!"):
        st.markdown(f'<div class="card">{random.choice(roasts)}</div>', unsafe_allow_html=True)
        st.snow()

# ---------- VIRUS SCAN ----------
elif page == "🦠 Virus Scan":
    st.header("🦠 Masood Virus Scanner")
    if st.button("Scan Shuru Karo"):
        bar = st.progress(0)
        status = st.empty()
        msgs = [
            "Dimagh scan ho raha hai...",
            "Sustti ka virus mila! 🦠",
            "Chai ke 47 cups detect hue ☕",
            "Udhaar wali files corrupt hain 💸",
            "Selfie folder: 9,999 photos 🤳",
            "Akal ka folder khaali mila... 📂",
        ]
        for i in range(100):
            time.sleep(0.04)
            bar.progress(i + 1)
            status.info(msgs[min(i // 17, len(msgs) - 1)])
        st.error("❌ 6 Viruses mile: Sustti, Late-Latifi, Udhaar-itis, Selfie-mania, Chai-Addiction, Bhoolna.exe")
        st.warning("💊 Ilaaj: Roz subah 6 baje uthna aur sab ko chai pilana.")

# ---------- IQ TEST ----------
elif page == "🧠 IQ Test":
    st.header("🧠 Masood ka IQ Test")
    q1 = st.radio("1) 2 + 2 = ?", ["4", "22", "Chai", "Pata nahi yaar"], index=None)
    q2 = st.radio("2) Pakistan ki capital?", ["Islamabad", "Shikarpur", "Biryani", "Rajri House"], index=None)
    q3 = st.radio("3) Sab se pyari cheez?", ["Dost", "Neend", "Chai", "Sab kuch"], index=None)

    if st.button("Result Dikhao"):
        with st.spinner("Calculating..."):
            time.sleep(2)
        st.metric("Masood ka IQ", f"{random.randint(-5, 7)} 🧠")
        st.error("Result: Aap ka dimagh abhi 'Loading...' par hai.")
        st.caption("Note: Result chahe kuch bhi ho, answer 'Chai' hi sahi tha. ☕")

# ---------- UDHAAR COUNTER ----------
elif page == "💸 Udhaar Counter":
    st.header("💸 Udhaar Counter")
    col1, col2 = st.columns(2)
    if col1.button("➕ Masood ne udhaar liya"):
        st.session_state.udhaar += random.choice([100, 200, 500, 1000])
    if col2.button("♻️ Reset (khwab mein)"):
        st.session_state.udhaar = 0
    st.metric("Total Udhaar", f"Rs. {st.session_state.udhaar}")
    if st.session_state.udhaar > 2000:
        st.error("🚨 Masood ko bank se call aa rahi hai!")
    elif st.session_state.udhaar > 0:
        st.warning("Wapsi ki date: 'Agle mahine pakka' 😅")

# ---------- BUTTON PAKRO ----------
elif page == "🙈 Button Pakro":
    st.header("🙈 Kya Masood bhai handsome hain?")
    st.write("Sach sach batao:")
    col1, col2 = st.columns(2)
    if col1.button("✅ Haan"):
        st.success("Shabash! Aap ko 1 chai inaam mein! ☕")
        st.balloons()
    nahi_texts = ["❌ Nahi", "❌ Pakka Nahi?", "❌ Soch lo...", "❌ Last chance", "❌ Chalo Haan kar do"]
    idx = min(st.session_state.nahi_count, len(nahi_texts) - 1)
    if col2.button(nahi_texts[idx]):
        st.session_state.nahi_count += 1
        if st.session_state.nahi_count >= len(nahi_texts):
            st.error("Zabardasti 'Haan' kar diya gaya hai! 😂")
            st.session_state.nahi_count = 0
        else:
            st.warning("Galat jawab! Dobara koshish karo 😏")

st.divider()
st.caption("Made with ❤️ & 🤡 by Sadam | Sab kuch mazaak hai, Masood bhai mind na karna! 😄")