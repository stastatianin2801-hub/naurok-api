from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random
import google.generativeai as genai

app = Flask(__name__)
# Дозволяємо запити з будь-якого домену для всіх методів
CORS(app, resources={r"/*": {"origins": "*"}})

# Отримання ключів з налаштувань Render
api_keys_str = os.environ.get("API_KEYS", "")
API_KEYS = api_keys_str.split(",") if api_keys_str else []

@app.route('/solve', methods=['POST', 'OPTIONS'])
def solve_question():
    # Обробка preflight-запиту браузера
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json
    if not data:
        return jsonify({"error": "Немає даних"}), 400
        
    question = data.get('question', '')
    options = data.get('options', '')
    
    if not API_KEYS:
        return jsonify({"error": "Ключі не налаштовані"}), 500
    
    try:
        # Випадковий вибір ключа
        current_key = random.choice(API_KEYS)
        genai.configure(api_key=current_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Ти — ШІ-помічник для тестів. 
        Питання: {question}
        Варіанти: {options}
        Вибери правильний варіант. Напиши ТІЛЬКИ текст правильної відповіді, без зайвих слів.
        """
        
        response = model.generate_content(prompt)
        ai_answer = response.text.strip()
        
        return jsonify({"answer": ai_answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return "Сервер працює! Використовуй /solve для запитів.", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
