import streamlit as st
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from ai_services import groq_generate, hf_lead_score

st.set_page_config(page_title="MarketMind", layout="wide")

# =============================
# THEME
# =============================
st.markdown("""
<style>
.stApp { background-color: #0B0B0F; color: white; }
section[data-testid="stSidebar"] { background-color: #111114; }
h1 { color: #FFC300 !important; }
h2,h3,h4 { color: #FF6A00 !important; }
.stButton>button {
    background-color: #FF6A00;
    color: white;
    border-radius: 8px;
}
.stButton>button:hover {
    background-color: #FFC300;
    color: black;
}
</style>
""", unsafe_allow_html=True)

# =============================
# PAGE CONFIG
# =============================
DEFAULT_PAGE = "Dashboard"
VALID_PAGES = [
    "Dashboard", "Campaign", "Sales", "Lead",
    "Summary", "Research", "Chat",
    "History", "ChatHistory"
]

# =============================
# SESSION INIT
# =============================
for key, default in {
    "page": DEFAULT_PAGE,
    "tool_history": [],
    "chat_history": [],
    "current_chat": [],
    "selected_item": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.page not in VALID_PAGES:
    st.session_state.page = DEFAULT_PAGE

# =============================
# SAFE API WRAPPERS
# =============================
def safe_groq(prompt):
    try:
        return groq_generate(prompt)
    except Exception as e:
        return f"⚠️ Groq API Error:\n{str(e)}"

def safe_hf(description):
    try:
        return hf_lead_score(description)
    except Exception as e:
        return {"score": 0, "intent": f"Error: {str(e)}"}

# =============================
# HELPERS
# =============================
def save_tool_history(feature, user_input, output):
    now = datetime.datetime.now()
    st.session_state.tool_history.append({
        "feature": feature,
        "input": user_input,
        "output": output,
        "date": now.strftime("%Y-%m-%d"),
        "month": now.strftime("%Y-%m"),
        "time": now.strftime("%H:%M:%S")
    })

def save_chat_history():
    if st.session_state.current_chat:
        now = datetime.datetime.now()
        st.session_state.chat_history.append({
            "messages": st.session_state.current_chat.copy(),
            "date": now.strftime("%Y-%m-%d"),
            "month": now.strftime("%Y-%m"),
            "time": now.strftime("%H:%M:%S")
        })
        st.session_state.current_chat = []

def download_output(title, content):
    st.download_button(
        "⬇ Download",
        content,
        file_name=f"{title}_{datetime.datetime.now().strftime('%H%M%S')}.txt"
    )

def generate_pdf_report(title, text):
    filename = f"{title}.pdf"
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(text.replace("\n", "<br/>"), styles["Normal"]))
    doc.build(story)

    with open(filename, "rb") as f:
        st.download_button(
            f"📄 Download {title} PDF",
            f,
            file_name=filename,
            mime="application/pdf"
        )

def go(page, keep=False):
    if page in VALID_PAGES:
        st.session_state.page = page
        if not keep:
            st.session_state.selected_item = None
        st.rerun()

# =============================
# SIDEBAR
# =============================
st.sidebar.title("🚀 MarketMind")

nav_items = [
    ("Dashboard", "Dashboard"),
    ("Campaign Generator", "Campaign"),
    ("Sales Pitch", "Sales"),
    ("Lead Scoring", "Lead"),
    ("Executive Summary", "Summary"),
    ("Business Research", "Research"),
    ("AI Chat", "Chat")
]

for label, page in nav_items:
    if st.sidebar.button(label):
        go(page)

st.sidebar.markdown("---")
st.sidebar.subheader("History")

for idx, item in enumerate(reversed(st.session_state.tool_history)):
    if st.sidebar.button(f"{item['feature']} ({item['time']})", key=f"tool_{idx}"):
        st.session_state.selected_item = item
        go("History", keep=True)

for idx, chat in enumerate(reversed(st.session_state.chat_history)):
    if st.sidebar.button(f"💬 Chat ({chat['time']})", key=f"chat_{idx}"):
        st.session_state.selected_item = chat
        go("ChatHistory", keep=True)

# =============================
# ROUTER
# =============================
page = st.session_state.page

# =============================
# DASHBOARD
# =============================
if page == "Dashboard":

    st.title("📊 MarketMind Intelligence Dashboard")

    tool_data = st.session_state.tool_history
    chat_data = st.session_state.chat_history

    total_tools = len(tool_data)
    total_chats = len(chat_data)
    total_usage = total_tools + total_chats

    current_month = datetime.datetime.now().strftime("%Y-%m")

    monthly_usage = [
        item for item in tool_data if item["month"] == current_month
    ] + [
        chat for chat in chat_data if chat["month"] == current_month
    ]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Searches", total_tools)
    col2.metric("Total Chats", total_chats)
    col3.metric("This Month Activity", len(monthly_usage))

    most_used = "N/A"

    if tool_data:
        df = pd.DataFrame(tool_data)
        feature_counts = df["feature"].value_counts()

        st.subheader("📈 Feature Usage Distribution")
        fig, ax = plt.subplots()
        feature_counts.plot(kind="bar", ax=ax)
        st.pyplot(fig)

        most_used = feature_counts.idxmax()
        st.success(f"🔥 Most Used Feature: {most_used}")

    if total_usage > 0:

        productivity_score = min(100, total_usage * 5)
        st.metric("⚡ Productivity Score", f"{productivity_score}/100")

        # AI Usage Insight
        insight_prompt = f"""
        Analyze usage:
        Total Searches: {total_tools}
        Total Chats: {total_chats}
        Monthly Activity: {len(monthly_usage)}
        Suggest improvements.
        """
        insights = safe_groq(insight_prompt)

        st.subheader("🧠 AI Usage Insights")
        st.write(insights)
        generate_pdf_report("Analytics_Report", insights)

        # =============================
        # MOCK INVESTOR PITCH
        # =============================
        st.markdown("---")
        st.subheader("💼 Mock Investor Pitch Mode")

        if st.button("🚀 Generate Investor Pitch"):

            pitch_prompt = f"""
            Create a startup investor pitch for MarketMind,
            an AI-powered Sales & Marketing Intelligence Platform.

            Traction:
            - Total Usage: {total_usage}
            - Monthly Activity: {len(monthly_usage)}
            - Most Used Feature: {most_used}
            - Productivity Score: {productivity_score}

            Structure:
            1. Problem
            2. Solution
            3. Market Opportunity
            4. Traction
            5. Competitive Advantage
            6. Revenue Model
            7. Growth Plan
            8. Funding Ask

            Sound confident and investor-ready.
            """

            pitch = safe_groq(pitch_prompt)

            st.markdown("### 🎤 Investor Pitch Script")
            st.write(pitch)

            download_output("Investor_Pitch", pitch)
            generate_pdf_report("Investor_Pitch", pitch)

    else:
        st.info("Start using the platform to unlock analytics & investor pitch mode.")

# =============================
# HISTORY VIEW
# =============================
elif page == "History":
    item = st.session_state.selected_item
    if item:
        st.title(f"📜 {item['feature']}")
        st.write("### Input")
        st.write(item["input"])
        st.write("### Output")
        st.write(item["output"])
        download_output(item["feature"], item["output"])
        if st.button("⬅ Back"):
            go("Dashboard")
    else:
        go("Dashboard")

# =============================
# CHAT HISTORY VIEW
# =============================
elif page == "ChatHistory":
    chat = st.session_state.selected_item
    if chat:
        st.title("💬 Chat History")
        for msg in chat["messages"]:
            role = "You" if msg["role"] == "user" else "AI"
            st.write(f"**{role}:** {msg['content']}")
        if st.button("⬅ Back to Chat"):
            go("Chat")
    else:
        go("Dashboard")

# =============================
# CAMPAIGN
# =============================
elif page == "Campaign":
    st.title("Campaign Generator")
    product = st.text_input("Product")
    audience = st.text_area("Audience")
    if st.button("Generate"):
        prompt = f"Create marketing campaign for {product} targeting {audience}"
        result = safe_groq(prompt)
        st.write(result)
        download_output("Campaign", result)
        save_tool_history("Campaign", prompt, result)

# =============================
# SALES
# =============================
elif page == "Sales":
    st.title("Sales Pitch")
    product = st.text_input("Product")
    persona = st.text_area("Persona")
    if st.button("Generate"):
        prompt = f"Create sales pitch for {product} targeting {persona}"
        result = safe_groq(prompt)
        st.write(result)
        download_output("Sales_Pitch", result)
        save_tool_history("Sales", prompt, result)

# =============================
# LEAD
# =============================
elif page == "Lead":
    st.title("Lead Scoring")
    description = st.text_area("Lead Description")
    if st.button("Score"):
        result = safe_hf(description)
        output = f"Score: {result.get('score',0)} | Intent: {result.get('intent','')}"
        st.write(output)
        save_tool_history("Lead", description, output)

# =============================
# SUMMARY
# =============================
elif page == "Summary":
    st.title("Executive Summary")
    content = st.text_area("Content")
    if st.button("Generate"):
        result = safe_groq(f"Summarize: {content}")
        st.write(result)
        download_output("Summary", result)
        save_tool_history("Summary", content, result)

# =============================
# RESEARCH
# =============================
elif page == "Research":
    st.title("Business Research")
    query = st.text_input("Research Topic")
    if st.button("Search"):
        result = safe_groq(f"Business research on {query}")
        st.write(result)
        download_output("Research", result)
        save_tool_history("Research", query, result)

# =============================
# CHAT
# =============================
elif page == "Chat":
    st.title("💬 AI Chat")
    user_input = st.text_input("Message")
    if st.button("Send"):
        if user_input:
            st.session_state.current_chat.append({"role": "user", "content": user_input})
            context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.current_chat])
            response = safe_groq(context)
            st.session_state.current_chat.append({"role": "assistant", "content": response})
            st.rerun()
    for msg in st.session_state.current_chat:
        role = "You" if msg["role"] == "user" else "AI"
        st.write(f"**{role}:** {msg['content']}")
    if st.button("Save Chat"):
        save_chat_history()
        st.success("Chat saved.")