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

# Gemini configuration optimized for short responses
generation_config = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 150,  # Reduced for shorter audio
    "response_mime_type": "text/plain",
}

# Create the model with new configuration
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="""You are a helpful Indian farmer assistant bot. 
    You provide SHORT, CONCISE, and PRACTICAL answers about farming, agriculture, crops, government schemes, and rural support.
    Always respond in the SAME language as the user's question.
    Keep responses under 2-3 sentences. Be direct and helpful.
    Focus on actionable advice for Indian farmers."""
)

def text_to_speech(text, language_code="hi-IN", speaker="anushka"):
    """Convert text to speech using Sarvam AI's TTS API."""
    url = "https://api.sarvam.ai/text-to-speech"

    payload = {
        "text": text,  # Changed from "inputs": [text] to "text": text
        "target_language_code": language_code,
        "speaker": speaker,
        "model": "bulbul:v2"
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

@app.route('/farmer_assistant', methods=['POST'])
def farmer_assistant():
    data = request.get_json()

    # Validate the input - now only needs text and language code
    if not data or "text" not in data or "language" not in data:
        return jsonify({"error": "Invalid input. Please provide text and language (e.g., 'hi-IN', 'te-IN')."}), 400

    user_question = data["text"]
    language_code = data["language"]  # Format: 'hi-IN', 'te-IN', 'ta-IN', etc.
    voice_model = data.get("voice_model", "anushka")  # Default voice model

    try:
        # Get AI response in the same language as user's question
        chat = model.start_chat(history=[])
        ai_response = chat.send_message(user_question)
        answer_text = ai_response.text.strip()

        # Generate speech in the same language
        audio_base64 = text_to_speech(answer_text, language_code, voice_model)

        if audio_base64:
            return jsonify({
                "question": user_question,
                "answer": answer_text,
                "audio_data": audio_base64
            })
        else:
            return jsonify({"error": "No audio data received."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
