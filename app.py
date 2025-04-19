from flask import Flask, request, jsonify
import requests
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Google Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Updated Gemini configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the model with new configuration
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b",
    generation_config=generation_config,
)

# Initialize chat session
chat = model.start_chat(history=[])

def text_to_speech(text, language_code="hi-IN", speaker="meera"):
    """Convert text to speech using Sarvam AI's TTS API."""
    url = "https://api.sarvam.ai/text-to-speech"

    payload = {
        "inputs": [text],
        "target_language_code": language_code,
        "speaker": speaker,
        "model": "bulbul:v1"
    }

    headers = {
        "api-subscription-key": os.getenv('SARVAM_API_KEY'),
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        response_data = response.json()

        if "audios" in response_data and response_data["audios"]:
            return response_data["audios"][0]  # Return the base64 audio string
        else:
            return None  # No audio data received

    except requests.exceptions.RequestException as e:
        return f"Error occurred: {e}"

@app.route('/translate_and_speak', methods=['POST'])
def translate_and_speak():
    data = request.get_json()

    # Validate the input
    if not data or "text" not in data or "language" not in data or "target_language" not in data:
        return jsonify({"error": "Invalid input. Please provide text, language, and target_language."}), 400

    input_text = data["text"]
    input_language = data["language"]  # This should be in the format 'hi-IN', 'te-IN', etc.
    target_language = data["target_language"]  # This can be like 'telugu', 'hindi', etc.
    voice_model = data.get("voice_model", "meera")  # Default voice model if not provided

    try:
        # Generate translation using the target language for Gemini
        language_request = f"Translate this from {input_language} to {target_language}: {input_text}!"
        response = chat.send_message(language_request)
        translated_text = response.text

        # Generate speech using the input language for Sarvam AI
        audio_base64 = text_to_speech(translated_text, input_language, voice_model)

        if audio_base64:
            return jsonify({
                "translated_text": translated_text,
                "audio_data": audio_base64
            })
        else:
            return jsonify({"error": "No audio data received."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
