"""Quick smoke test: verify Gemini + Groq LLM imports and chain work."""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv()

# Alias GEMINI_API_KEY to GOOGLE_API_KEY if needed
if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

try:
    from langchain_groq import ChatGroq
    from langchain_google_genai import ChatGoogleGenerativeAI

    print(f"GROQ_API_KEY present   : {bool(os.getenv('GROQ_API_KEY'))}")
    print(f"GOOGLE_API_KEY present : {bool(os.getenv('GOOGLE_API_KEY'))}")

    # Matches engine.py: Groq primary, Gemini fallback
    llm_primary = ChatGroq(model="qwen/qwen3.6-27b", temperature=0.4)
    llm_fallback = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.4)

    print("\n[PASS] Both LLMs instantiated successfully.")
    print("   Primary  : Groq   -> qwen/qwen3.6-27b")
    print("   Fallback : Gemini -> gemini-3.6-flash")

    print("\n--- Testing Gemini (Primary) ---")
    resp = llm_primary.invoke("Say OK in exactly one word.")
    print(f"Gemini response: {resp.content}")

    print("\n--- Testing Groq Qwen (Fallback) ---")
    resp2 = llm_fallback.invoke("Say OK in exactly one word.")
    print(f"Groq Qwen response: {resp2.content}")

    print("\n[ALL PASS] Both models working. Fallback chain ready.")

except Exception as e:
    print(f"\n[FAIL] Error: {e}")
    import traceback; traceback.print_exc()
