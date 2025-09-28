Customer Support Voice AssistantThis project implements a conversational voice assistant powered by the Groq API for ultra-fast language model inference, coupled with ElevenLabs for high-quality Text-to-Speech (TTS) and SpeechRecognition for accurate Voice-to-Text (VTT). The application features a Python Flask backend and a modern, single-file HTML/JavaScript frontend (or React/JSX, as included in other files).🚀 FeaturesReal-Time Conversation: Leverage Groq's low-latency performance for a fluid, natural conversational experience.Multimodal Interaction: Seamlessly handles user voice input (VTT) and provides synthesized voice replies (TTS).Session Management: Maintains conversation history and context using unique session IDs stored on the client and server.Extensible Backend: Uses a LangGraph/ReAct structure in the Flask server (personal_assistant_server.py) for easy addition of more tools and functionality.⚙️ PrerequisitesTo run this project, you will need:Python 3.8+API Keys:Groq API Key: For accessing the LLM (e.g., Llama 3) and Whisper transcription.ElevenLabs API Key: For generating the high-quality voice response audio.FFmpeg: Required by the pydub library for handling audio conversion and format manipulation. You must have ffmpeg installed and accessible in your system's PATH.🛠️ Setup and Installation1. Configure Environment VariablesCreate a file named .env in the root directory of your project to store your API keys and configuration.# .env file
GROQ_API_KEY="YOUR_GROQ_API_KEY"
ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY"

2. Install Python DependenciesIt's highly recommended to use a virtual environment.# Create a virtual environment
python -m venv venv

# Activate the virtual environment (Linux/macOS)
source venv/bin/activate

# Activate the virtual environment (Windows)
.\venv\Scripts\activate

# Install required packages (assuming these are the main dependencies)
pip install Flask groq elevenlabs SpeechRecognition pydub python-dotenv langchain_core langgraph

3. Ensure FFmpeg is InstalledIf you encounter errors related to audio processing, confirm that FFmpeg is correctly installed on your system.▶️ Running the ApplicationThis project requires two separate terminals to run the backend server and serve the frontend client.Terminal 1: Start the Backend (Flask Server)Navigate to the project directory and run the Flask application:python personal_assistant_server.py

The server should start and listen on port 5000:* Running on [http://127.0.0.1:5000/](http://127.0.0.1:5000/) (Press CTRL+C to quit)

Terminal 2: Start the Frontend (HTTP Server)The client file (e.g., voice_assistant_client.html or the React app wrapper) must be served by a simple web server to access the microphone and make API requests. Navigate to the project directory in a new terminal and use Python's built-in server:python -m http.server 8000

The client server should start on port 8000:Serving HTTP on 0.0.0.0 port 8000 ([http://0.0.0.0:8000/](http://0.0.0.0:8000/)) ...

Access the AppOpen your web browser and navigate to:http://localhost:8000/voice_assistant_client.htmlClick the microphone button to start the conversation! You will likely need to grant microphone permissions to your browser.🏗️ Architecture OverviewThe voice assistant follows a standard client-server architecture:Client (voice_assistant_client.html or React Component):Handles the UI, microphone access, and audio recording.Sends recorded audio (WAV blob) and the current session ID to the Flask backend's /api/chat endpoint.Receives the AI's synthesized audio response and plays it back.Server (personal_assistant_server.py):Receives the audio file and session ID.VTT: Uses Groq's Whisper model via the groq client to transcribe the audio into text.Agent: The core logic is powered by a LangGraph agent using a ReAct pattern, which decides whether to use a tool (like add_task or web_search) or provide a direct conversational response.TTS: Uses the gTTS library to generate the audio response.Returns the generated audio, the user's transcription, and the updated session ID to the client.
