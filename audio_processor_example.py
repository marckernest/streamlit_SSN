import os
import tempfile
import streamlit as st
import openai

st.title("🎤 Record and Transcribe Audio")

audio_file = st.audio_input("Record or upload your voice")

if audio_file is not None:
    st.audio(audio_file)
    if st.button("Transcribe"):
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
            except openai.OpenAIError as e:
                st.error(f"Transcription failed: {e}")
                transcript = None
            finally:
                os.remove(tmp.name)
            if transcript:
                st.write("**Transcription:**")
                st.write(transcript.text)