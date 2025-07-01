import streamlit as st
import openai

st.title("🎤 Record and Transcribe Audio")

audio_file = st.audio_input("Record or upload your voice")

if audio_file is not None:
    st.audio(audio_file)
    st.write("Audio file received!")
    if st.button("Transcribe"):
        with st.spinner("Transcribing..."):
            # Save the audio to a temporary file
            with open("temp_audio.wav", "wb") as f:
                f.write(audio_file.getbuffer())
            # Transcribe using OpenAI Whisper
            with open("temp_audio.wav", "rb") as f:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
            st.write("**Transcription:**")
            st.write(transcript.text)