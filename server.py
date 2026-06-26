from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random
import google.generativeai as genai

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Завантажуємо ключі
API_KEYS = [k.strip() for k in os.environ.get("API_KEYS", "").split(",") if k.strip()]

@app.route('/solve', methods=['POST'])
def solve_question():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400

        question = data.get('question', '').strip()
        options = data.get('options', '').strip()

        if not question or not options:
            return jsonify({"error": "Question or options missing"}), 400

        if not API_KEYS:
            return jsonify({"error": "API_KEYS не налаштовані на сервері"}), 500

        # Використовуємо випадковий ключ
        genai.configure(api_key=random.choice(API_KEYS))
        
        # 🔥 АВТОПОШУК МОДЕЛІ 🔥
        # Сервер сам запитає у Google, яка модель зараз доступна
        valid_model_name = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                valid_model_name = m.name
                break # Беремо першу ж робочу модель
                
        if not valid_model_name:
            return jsonify({"error": "Для твого ключа немає доступних моделей"}), 500

        # Використовуємо ту модель, яку знайшов код
        model = genai.GenerativeModel(valid_model_name)

        prompt = f"""
Ти — розумний помічник на тесті.
Питання: {question}
Варіанти відповідей: {options}

Вибери **один** правильний варіант. 
Відповідай **тільки** текстом правильної відповіді, без пояснень, без нумерації.
"""

        response = model.generate_content(prompt)
        answer = response.text.strip()

        return jsonify({"answer": answer})

    except Exception as e:
        print("=== Gemini Error ===")
        print(str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    return f"API is live! Keys configured: {len(API_KEYS)}"


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
