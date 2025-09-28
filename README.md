# 🎙️ Customer Support Voice Assistant  

A conversational **voice assistant** powered by the **Groq API** for ultra-fast language model inference, **ElevenLabs** for high-quality Text-to-Speech (TTS), and **SpeechRecognition** for accurate Voice-to-Text (VTT).  

The project features a **Python Flask backend** and a **modern single-file HTML/JavaScript frontend** (with optional React/JSX version).  

---

## 🚀 Features  

- **Real-Time Conversation** → Leverages Groq’s low-latency performance for fluid, natural conversation.  
- **Multimodal Interaction** → Handles user **voice input (VTT)** and provides **synthesized voice replies (TTS)**.  
- **Session Management** → Maintains conversation history & context with unique session IDs.  
- **Extensible Backend** → Built with **LangGraph/ReAct structure** for easy addition of tools and functionality.  

---

## ⚙️ Prerequisites  

To run this project, you’ll need:  

- Python **3.8+**  
- **API Keys**:  
  - Groq API Key → For accessing LLMs (e.g., Llama 3) and Whisper transcription.  
  - ElevenLabs API Key → For generating TTS audio.  
- **FFmpeg** → Required by `pydub` for audio conversion. Must be installed and added to your system’s `PATH`.  

---

## 🛠️ Setup & Installation  

### 1. Configure Environment Variables  

Create a `.env` file in the root directory:  

```ini
# .env
GROQ_API_KEY="YOUR_GROQ_API_KEY"
ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY"
# Create a virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate
```



