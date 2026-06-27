from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import random
import google.generativeai as genai

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

API_KEYS = [k.strip() for k in os.environ.get("API_KEYS", "").split(",") if k.strip()]

@app.route('/solve', methods=['POST'])
def solve_question():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400

        question = data.get('question', '').strip()
        options = data.get('options', '').strip()
        images_data = data.get('images', []) # 🔥 Отримуємо картинки від розширення

        if not options:
            return jsonify({"error": "Options missing"}), 400

        if not API_KEYS:
            return jsonify({"error": "API_KEYS не налаштовані на сервері"}), 500

        genai.configure(api_key=random.choice(API_KEYS))
        
        # Шукаємо модель, яка підтримує зір (серія 1.5)
        valid_model_name = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if '1.5' in m.name: # Моделі 1.5 (flash/pro) чудово бачать картинки
                    valid_model_name = m.name
                    break
                
        if not valid_model_name:
            valid_model_name = 'gemini-pro' # Запасний варіант, якщо 1.5 недоступна

        model = genai.GenerativeModel(valid_model_name)

        prompt = f"""
Ти — розумний помічник на тесті.
Питання: {question}
Варіанти відповідей: {options}

Якщо до питання додано зображення, уважно проаналізуй його, щоб знайти правильну відповідь.
Вибери **один** правильний варіант. 
Відповідай **тільки** текстом правильної відповіді, без пояснень, без нумерації.
"""
        
        # 🔥 ФОРМУЄМО ПАКЕТ ДАНИХ (ТЕКСТ + КАРТИНКИ) 🔥
        contents = [prompt]
        for img in images_data:
            contents.append({
                "mime_type": img["mime_type"],
                "data": img["data"]
            })

        # Відправляємо весь пакет у нейромережу
        response = model.generate_content(contents)
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
