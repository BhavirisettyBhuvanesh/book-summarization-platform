import os
from dotenv import load_dotenv
from google import genai
from groq import Groq

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ── Function 1: Call Gemini ───────────────────────────────────────────────────
# This function takes a prompt (a text question/instruction) and sends it to
# the Gemini model. It returns the model's text response.
def call_gemini(prompt: str) -> str:
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",   # which Gemini model to use
        contents=prompt             # send the prompt
    )
    return response.text            # extract just the text from response


# ── Function 2: Call Groq ─────────────────────────────────────────────────────
# This function does the same thing but uses the Groq API with Llama model.
# It is only called when Gemini fails.
def call_groq(prompt: str) -> str:
    client = Groq(api_key=GROQ_API_KEY)                # create a Groq client
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",               # which Groq model to use
        messages=[
            {"role": "user", "content": prompt}        # send our prompt as a user message
        ]
    )
    return response.choices[0].message.content         # extract just the text from response


# ── Function 3: Generate Response (with fallback) ─────────────────────────────
# This is the MAIN function that all our RAG pipelines will call.
# It tries Gemini first. If Gemini fails for any reason (rate limit, error),
# it automatically switches to Groq. This is our fallback strategy.
def generate_response(prompt: str) -> dict:
    try:
        # Try Gemini first (primary LLM)
        answer = call_gemini(prompt)
        return {
            "answer": answer,
            "model_used": "gemini-2.5-flash"   # tells us which model answered
        }

    except Exception as gemini_error:
        # If Gemini fails, log the error and try Groq
        print(f"[Gemini failed] {gemini_error} -> Switching to Groq...")

        try:
            answer = call_groq(prompt)
            return {
                "answer": answer,
                "model_used": "groq-llama-3.3-70b"   # tells us which model answered
            }

        except Exception as groq_error:
            # If both fail, return an error message so the app doesn't crash
            print(f"[Groq also failed] {groq_error}")
            return {
                "answer": "Sorry, both AI models are currently unavailable. Please try again later.",
                "model_used": "none"
            }
