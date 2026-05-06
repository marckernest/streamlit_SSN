# Senior Services Chatbot

A Streamlit-powered AI chatbot that helps seniors understand and access government services such as Social Security, pensions, and financial aid. The assistant supports both text and voice input/output, and can look up the nearest Social Security Administration (SSA) office by ZIP code.

## Features

- **Conversational AI** – Powered by OpenAI's GPT-4 Assistants API with a friendly, plain-language interface designed for seniors.
- **SSA Office Locator** – Scrapes the official SSA website to find the closest Social Security office for any U.S. ZIP code.
- **Voice Input** – Record a question directly in the browser or upload an audio file (useful for mobile users). Audio is transcribed using OpenAI Whisper.
- **Voice Output** – Responses are read aloud using OpenAI Text-to-Speech (TTS), with a toggle to enable or disable it.
- **Persistent Conversation Threads** – Session state keeps the conversation context alive across multiple turns.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend / UI | [Streamlit](https://streamlit.io/) |
| LLM / Assistants | OpenAI GPT-4 (`gpt-4-1106-preview`) |
| Speech-to-Text | OpenAI Whisper (`whisper-1`) |
| Text-to-Speech | OpenAI TTS (`tts-1`, voice: `nova`) |
| Web Scraping | BeautifulSoup4 + Requests |
| Deployment | Docker, Fly.io, or Heroku/Procfile |

## Project Structure

```
.
├── chatbot.py                 # Main Streamlit app
├── ssa_lookup.py              # SSA office scraper (ZIP code → office details)
├── openai_utils.py            # OpenAI utility helpers
├── utils.py                   # General utility functions
├── audio_processor_example.py # Standalone audio transcription example
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker build configuration
├── fly.toml                   # Fly.io deployment configuration
├── Procfile                   # Heroku-style process file
└── runtime.txt                # Python runtime version pin
```

## Getting Started

### Prerequisites

- Python 3.12+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Local Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/marckernest/streamlit_SSN.git
   cd streamlit_SSN
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file in the project root:

   ```env
   OPENAI_API_KEY=sk-...
   # Optional: reuse an existing assistant instead of creating a new one each run
   OPENAI_ASSISTANT_ID=asst_...
   ```

4. **Run the app**

   ```bash
   streamlit run chatbot.py
   ```

   The app will be available at `http://localhost:8501`.

### Docker

```bash
docker build -t senior-services-chatbot .
docker run -p 8501:8501 --env-file .env senior-services-chatbot
```

### Fly.io Deployment

1. Install the [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) and log in.
2. Update `app` in `fly.toml` with your chosen app name.
3. Set your secrets:
   ```bash
   fly secrets set OPENAI_API_KEY=sk-...
   ```
4. Deploy:
   ```bash
   fly deploy
   ```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key used for GPT-4, Whisper, and TTS |
| `OPENAI_ASSISTANT_ID` | ❌ | ID of a pre-created OpenAI Assistant. If omitted, a new assistant is created automatically on first run. |

## How It Works

1. The user types a question or records/uploads audio in the Streamlit interface.
2. Audio input is transcribed via Whisper and treated as a text message.
3. If the message contains a ZIP code and references Social Security, `ssa_lookup.py` scrapes the SSA website directly and returns the nearest office details.
4. All other messages are routed through the OpenAI Assistants API, which can call registered tools (e.g., `get_ssa_office_link`) to answer questions.
5. The assistant's reply is displayed in the chat and optionally read aloud via TTS.

## License

This project does not currently include a license file. Please contact the repository owner for usage terms.
