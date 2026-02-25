import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# -------------------------
# GROQ GENERATION FUNCTION
# -------------------------
def groq_generate(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a business intelligence AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        elif "error" in result:
            return f"Groq API Error: {result['error']['message']}"
        else:
            return f"Unexpected response: {result}"

    except Exception as e:
        return f"Exception occurred: {str(e)}"


# -------------------------
# HUGGING FACE LEAD SCORING
# -------------------------
def hf_lead_score(description):

    prompt = f"""
    Analyze this business lead and classify the buying intent.

    Lead:
    {description}

    Classify as one of:
    - High Intent
    - Medium Intent
    - Low Intent

    Respond with only one label.
    """

    result = groq_generate(prompt)

    if "High" in result:
        return {"score": 90, "intent": "High Intent"}
    elif "Medium" in result:
        return {"score": 65, "intent": "Medium Intent"}
    else:
        return {"score": 30, "intent": "Low Intent"}