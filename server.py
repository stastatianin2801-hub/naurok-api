from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random
import google.generativeai as genai

app = Flask(__name__)
# Дозволяємо запити з будь-якого джерела
CORS(app)

# Обробка OPTIONS запитів (для вирішення CORS preflight)
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        return '', 200

# Отримання ключів
api_keys_str = os.environ.get("API_KEYS", "")
API_KEYS = api_keys_str.split(",") if api_keys_str else []

@app.route('/solve', methods=['POST', 'OPTIONS'])
def solve_question():
    data = request.json
    print(f"DEBUG: Отримано запит! Метод: {request.method}")
    print(f"DEBUG: Дані: {data}")
    if not data:
        return jsonify({"error": "No data"}), 400
        
    question = data.get('question', '')
    options = data.get('options', '')
    
    if not API_KEYS:
        return jsonify({"error": "Ключі не налаштовані"}), 500
    
    try:
        genai.configure(api_key=random.choice(API_KEYS))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Питання: {question}
        Варіанти: {options}
        Вибери правильний варіант. Напиши ТІЛЬКИ текст правильної відповіді.
        """
        
        response = model.generate_content(prompt)
        return jsonify({"answer": response.text.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return "API is live!", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
