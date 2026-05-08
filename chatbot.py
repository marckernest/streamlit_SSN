import streamlit as st
import openai
import os
import json
import time
import re
from dotenv import load_dotenv
from ssa_lookup import get_ssa_office_link
import tempfile

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
else:
    thread = client.beta.threads.retrieve(st.session_state.thread_id)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_service_info",
            "description": "Look up info about a senior service from a public database",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Name of the service to look up, e.g., 'Social Security'"
                    }
                },
                "required": ["service"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_ssa_office",
            "description": "Find the closest Social Security office given a U.S. city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ssa_office_link",
            "description": "Finds and returns the SSA office details for a ZIP code by scraping the SSA website and storing the result",
            "parameters": {
                "type": "object",
                "properties": {
                    "zipcode": {
                        "type": "string",
                        "description": "ZIP code of the user"
                    }
                },
                "required": ["zipcode"]
            }
        }
    }
]

ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
if not ASSISTANT_ID:
    assistant = client.beta.assistants.create(
        name="Senior Services Assistant",
        instructions="You are a helpful assistant that helps seniors understand and access government services like Social Security, pensions, and financial aid. Speak simply and clearly. Always use the provided tools to answer questions involving ZIP codes or office lookups. Never guess or rely on memory for SSA locations — always call the get_ssa_office_link tool for those cases.",
        tools=tools,
        model="gpt-4-1106-preview"
    )
    ASSISTANT_ID = assistant.id

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm here to help you access senior services like Social Security, pensions, and more. What do you need help with today?"}]

# Fix 12: Session-level rate limiting to prevent runaway API costs
MAX_API_CALLS_PER_SESSION = 50
if "api_call_count" not in st.session_state:
    st.session_state.api_call_count = 0

# Render chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if "ssa_intent" not in st.session_state:
    st.session_state.ssa_intent = False

# Voice output toggle
if "voice_output" not in st.session_state:
    st.session_state.voice_output = True  # Enabled by default

st.session_state.voice_output = st.checkbox("🔊 Enable Voice Output", value=st.session_state.voice_output)

def speak_text(text):
    # Fix 8: Use st.audio instead of unsafe raw HTML to avoid HTML injection
    try:
        tts_response = openai.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )
        st.audio(tts_response.content, format="audio/mp3", autoplay=True)
    except openai.OpenAIError:
        pass  # Voice output is best-effort; silently skip if TTS fails

def process_user_input(user_input):
    # Fix 12: Enforce session-level rate limit on chat API calls
    if st.session_state.api_call_count >= MAX_API_CALLS_PER_SESSION:
        st.warning("You have reached the maximum number of requests for this session.")
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    zip_match = re.search(r"\b(\d{5})\b", user_input)
    ssa_keywords = ("ssa" in user_input.lower() or "social security" in user_input.lower())

    if ssa_keywords:
        st.session_state.ssa_intent = True

    if zip_match and (ssa_keywords or st.session_state.ssa_intent):
        zipcode = zip_match.group(1)
        response_text = get_ssa_office_link(zipcode)
        st.session_state.api_call_count += 1
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.chat_message("assistant").write(response_text)
        if st.session_state.voice_output:
            speak_text(response_text)
        st.session_state.ssa_intent = False
    else:
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        with st.spinner("Thinking..."):
            # 120 iterations at 1 second each = ~2 minutes maximum wait
            max_poll_iterations = 120
            terminal_states = {"failed", "cancelled", "expired", "timed_out"}
            for _ in range(max_poll_iterations):
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                if run.status == "completed":
                    break
                if run.status in terminal_states:
                    st.error(f"The assistant could not complete the request (status: {run.status}). Please try again.")
                    return
                if run.status == "requires_action":
                    tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    if name == "get_service_info":
                        output = "Service lookup not implemented yet."
                    elif name == "find_ssa_office":
                        output = "City-based SSA lookup not implemented yet."
                    elif name == "get_ssa_office_link":
                        output = get_ssa_office_link(args["zipcode"])
                    else:
                        output = "Function not implemented."
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=[{
                            "tool_call_id": tool_call.id,
                            "output": output
                        }]
                    )
                time.sleep(1)
            else:
                st.error("The assistant timed out. Please try again.")
                return

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        last_message = messages.data[0]
        assistant_reply = last_message.content[0].text.value
        st.session_state.api_call_count += 1

        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
        st.chat_message("assistant").write(assistant_reply)
        if st.session_state.voice_output:
            speak_text(assistant_reply)

# --- Mobile-friendly voice input section ---
st.markdown("""
<div style="color:#FFD700; background:#222; padding:10px; border-radius:8px; margin-bottom:10px;">
<b>Tip for Mobile Users:</b> If you can't record directly, use your phone's voice memo app to record your question, then upload the audio file here.
</div>
""", unsafe_allow_html=True)

st.markdown("#### 🎤 Voice Input (Record or Upload)")
audio_file = st.audio_input("Record or upload your question (tap to upload on mobile)", key="audio_input")

if "audio_processed" not in st.session_state:
    st.session_state.audio_processed = False

if audio_file is not None and not st.session_state.audio_processed:
    st.audio(audio_file)
    # Fix 12: Enforce session-level rate limit on transcription calls
    if st.session_state.api_call_count >= MAX_API_CALLS_PER_SESSION:
        st.warning("You have reached the maximum number of requests for this session.")
    else:
        with st.spinner("Transcribing..."):
            # Fix 1: Use a secure per-request temp file instead of a shared hardcoded path
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            try:
                tmp.write(audio_file.getbuffer())
                tmp.flush()
                tmp.close()
                with open(tmp.name, "rb") as f:
                    transcript = openai.audio.transcriptions.create(
                        model="whisper-1",
                        file=f
                    )
                st.session_state.api_call_count += 1
            finally:
                os.remove(tmp.name)
            process_user_input(transcript.text)
        st.session_state.audio_processed = True

if audio_file is None and st.session_state.audio_processed:
    st.session_state.audio_processed = False

# --- Chat input ---
user_input = st.chat_input("Ask me anything about senior benefits and services.")
if user_input:
    process_user_input(user_input)

st.divider()
