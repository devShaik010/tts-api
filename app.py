from flask import Flask, request, jsonify
import requests
import json
import google.generativeai as genai
from datetime import date
import os  # Import os module

app = Flask(__name__)

# Configure Google Gemini API
genai.configure(api_key="AIzaSyBF08DIZKTvWbzc-0Ga5dIywADXS9z0LVY")  # Replace with your actual API key
today = str(date.today())
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat()

# Gemini Pro model parameters
gf = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 528,
}

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()

    # Validate the input
    if not data or "text" not in data or "language" not in data or "target_language" not in data:
        return jsonify({"error": "Invalid input. Please provide text, language, and target_language."}), 400

    input_text = data["text"]
    input_language = data["language"]  # This should be in the format 'hi-IN', 'te-IN', etc.
    target_language = data["target_language"]  # This can be like 'telugu', 'hindi', etc.

    try:
        # Generate translation using the target language for Gemini
        language_request = f"Translate this from {input_language} to {target_language}: {input_text}!"
        response = chat.send_message(language_request, generation_config=gf)
        translated_text = response.text

        # Only return the translated text
        return jsonify({
            "translated_text": translated_text
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
