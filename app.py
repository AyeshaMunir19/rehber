import time
import streamlit as st
from google import genai

st.set_page_config(page_title="REHBER", page_icon="🌸")

# ---------- Soft styling touches ----------
st.markdown(
    """
    <style>
       div.stButton > button {
        border-radius: 999px;
        padding: 0.6rem 1.8rem;
        font-weight: 600;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #F3C9D5;
        border-radius: 12px;
        background: #FFFDF9;
    }
    div[data-baseweb="textarea"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E7B3C4 !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="textarea"] textarea {
        background-color: #FFFFFF !important;
    }
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {
        color: #7A5560 !important;
        opacity: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Friendly labels -> values used in the prompt ----------
LANGUAGES = {
    "🇬🇧 English": "English",
    "🇵🇰 اردو": "Urdu",
    "🇹🇷 Türkçe": "Turkish",
}
BACKGROUNDS = {
    "Just starting": "Little / Basic",
    "I know the basics": "Some",
    "I'm comfortable with it": "Strong",
}
STYLES = {
    "🌱 Keep it simple": "Simple Explanations",
    "🪜 Step-by-step": "Step-by-Step",
    "🔎 Go deeper": "Detailed",
    "💡 Use examples": "Example-Based",
}

# ---------- Sidebar: learning profile ----------
st.sidebar.title("🌸 REHBER")
st.sidebar.caption("Your Personal Learning Guide")
st.sidebar.subheader("✨ YOUR LEARNING PROFILE")

subject = st.sidebar.selectbox(
    "📚 What are you learning?",
    ["Mathematics", "Physics", "Programming", "Chemistry", "Biology"],
)
level = st.sidebar.selectbox(
    "🌱 Your level",
    ["Beginner", "Intermediate", "Advanced"],
)
background_label = st.sidebar.selectbox(
    "🧠 What do you already know?",
    list(BACKGROUNDS.keys()),
)
language_label = st.sidebar.selectbox(
    "🌐 How should I explain it?",
    list(LANGUAGES.keys()),
)
style_label = st.sidebar.selectbox(
    "✨ How should I teach you?",
    list(STYLES.keys()),
)

# The values the prompt builder uses
background = BACKGROUNDS[background_label]
language = LANGUAGES[language_label]
style = STYLES[style_label]
style_name = style_label.split(" ", 1)[1]  # the label without its emoji


# ---------- Prompt builder ----------
def build_prompt(subject, level, background, language, style, question):
    style_guidance = {
        "Simple Explanations": "Keep it short and easy to follow, using everyday words and simple analogies.",
        "Step-by-Step": "Teach it as a numbered sequence. Each step covers one small idea. Do not write long essay paragraphs.",
        "Detailed": "Go deep: cover the reasoning, edge cases, and how the parts connect.",
        "Example-Based": "Teach mainly through 2 or 3 concrete examples, with short explanations around them.",
    }
    structure_guidance = {
        "Simple Explanations": "Use short markdown headings such as ### 🧭 The Big Idea, ### 💡 In Simple Words, ### 🌍 Example, ### ⭐ Key Takeaway. Only include the sections that are useful.",
        "Step-by-Step": "Use ONLY these headings: ### Step 1: <short title>, ### Step 2: <short title>, and so on (usually 4 to 6 steps), and finish with ### ⭐ Key Takeaway. Put any formula or code inside the step where it belongs. Do not add other sections.",
        "Detailed": "Use short markdown headings such as ### 🧭 The Big Idea, ### 🧮 Key Concept / Formula, ### 🌍 Example, ### ⭐ Key Takeaway. Only include the sections that are useful.",
        "Example-Based": "Use short markdown headings such as ### 🧭 The Big Idea, ### 🌍 Example 1, ### 🌍 Example 2, ### ⭐ Key Takeaway. Only include the sections that are useful.",
    }
    return f"""You are Rehber, a patient, encouraging personal learning guide.

The student is studying: {subject}
Their learning level: {level}
Their background knowledge: {background}
Their preferred language: {language}
Their preferred explanation style: {style}

Student question:
{question}

Generate an educational explanation appropriate for this learner.

Rules:
- Write the ENTIRE response in {language}.
- Style instruction: {style_guidance[style]}
- Structure instruction: {structure_guidance[style]}
- Start teaching right away. Skip long greetings and do not refer to yourself as an AI or a chatbot.
- Let the learner's level and background shape the lesson silently. Never mention their settings (level, background, style) out loud.
- Adapt the complexity, terminology, depth, examples, and structure to the learner.
- Explain any unfamiliar terminology.
- Prioritize factual accuracy. Double-check technical terms before using them, and do not mix up similar-sounding concepts. If you are unsure about something, say so instead of guessing.
- Actually teach the concept. Do not just repeat the question.
- Do not add step labels inside code comments.
"""


# ---------- "Why is this explained this way?" text ----------
def build_why_text(level, background, language, style):
    level_notes = {
        "Beginner": "simpler terminology and everyday ideas",
        "Intermediate": "a balance of clear ideas and some technical detail",
        "Advanced": "deeper reasoning and more technical detail",
    }
    background_notes = {
        "Little / Basic": "explaining new terms as they appear",
        "Some": "building on the basics you already know",
        "Strong": "skipping the basics and going straight to the deeper ideas",
    }
    style_notes = {
        "Simple Explanations": "keeping everything short and easy to follow",
        "Step-by-Step": "breaking the idea into ordered steps",
        "Detailed": "covering the topic in depth",
        "Example-Based": "teaching through concrete examples",
    }
    return (
        "You selected:\n\n"
        f"- 🌱 {level}\n"
        f"- 🧠 {background_label}\n"
        f"- 🌐 {language}\n"
        f"- ✨ {style_name}\n\n"
        f"So your guide is using {level_notes[level]}, "
        f"{background_notes[background]}, and {style_notes[style]}, "
        f"written in {language}."
    )


# ---------- Talking to the model ----------
def get_explanation(prompt):
    """Returns (answer, error_message). One of them is always None."""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None, "🔑 The API key is missing. Please check your secrets.toml file."

    client = genai.Client(api_key=api_key)
    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.7-flash"]

    for model_name in models_to_try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response.text:
                    return response.text, None
            except Exception as e:
                print(f"API error ({model_name}, try {attempt + 1}): {e}")
                time.sleep(2)

    return None, "Something went wrong while getting your explanation. Please try again."


# ---------- Main page ----------
st.title("✨ What are we learning today?")
st.write("Understand it your way.")

st.markdown("#### 💬 What would you like to understand?")
st.write("Ask anything you're learning about, and I'll explain it your way.")

question = st.text_area(
    "Your question",
    placeholder="Try: Explain Newton's Second Law with a real-life example...",
    height=150,
    label_visibility="collapsed",
)

st.caption(
    "Try asking:  📐 Explain derivatives simply  ·  "
    "🌱 Why does photosynthesis happen?  ·  💻 Help me understand recursion"
)

if st.button("✨ Teach Me", type="primary"):
    if question.strip() == "":
        st.warning("🌷 Please enter a question first.")
    else:
        prompt = build_prompt(subject, level, background, language, style, question)
        with st.spinner("✨ Preparing your lesson..."):
            answer, error = get_explanation(prompt)
        if error:
            st.error(error)
        else:
            st.subheader("📖 Your Explanation")
            st.caption(
                f"Tailored for {subject} • {level} • {background_label} • "
                f"{language} • {style_name}"
            )
            with st.expander("✨ Why is this explained this way?"):
                st.markdown(build_why_text(level, background, language, style))
            st.markdown(answer)