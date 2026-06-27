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
        images_data = data.get('images', []) 

        if not options:
            return jsonify({"error": "Options missing"}), 400

        if not API_KEYS:
            return jsonify({"error": "API_KEYS не налаштовані на сервері"}), 500

        genai.configure(api_key=random.choice(API_KEYS))
        
        # 🔥 РОЗУМНИЙ ФІЛЬТР МОДЕЛЕЙ 🔥
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # VIP-список стабільних моделей, які мають комп'ютерний зір
        good_models = [
            'models/gemini-1.5-flash-latest',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro-latest',
            'models/gemini-1.5-pro',
            'models/gemini-pro-vision'
        ]
        
        valid_model_name = None
        for model_name in good_models:
            if model_name in available_models:
                valid_model_name = model_name
                break
                
        # Запасний варіант, якщо VIP-список не спрацював (шукаємо 1.5, але без слова robotics)
        if not valid_model_name:
            for am in available_models:
                if '1.5' in am and 'robotics' not in am and 'preview' not in am:
                    valid_model_name = am
                    break

        if not valid_model_name:
            return jsonify({"error": "Не знайдено підходящої моделі для картинок"}), 500

        print(f"=== Використовуємо модель: {valid_model_name} ===")
        model = genai.GenerativeModel(valid_model_name)

        prompt = f"""
Ти — розумний помічник на тесті.
Питання: {question}
Варіанти відповідей: {options}

Якщо до питання додано зображення, уважно проаналізуй його, щоб знайти правильну відповідь.
Вибери **один** правильний варіант. 
Відповідай **тільки** текстом правильної відповіді, без пояснень, без нумерації.
"""
        
        contents = [prompt]
        for img in images_data:
            contents.append({
                "mime_type": img["mime_type"],
                "data": img["data"]
            })

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
