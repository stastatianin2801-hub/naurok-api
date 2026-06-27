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
        
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        good_models = [
            'models/gemini-2.5-flash',
            'models/gemini-2.0-flash',
            'models/gemini-flash-latest',
            'models/gemini-2.5-pro'
        ]
        
        valid_model_name = None
        for model_name in good_models:
            if model_name in available_models:
                valid_model_name = model_name
                break
                
        if not valid_model_name and available_models:
            valid_model_name = available_models[0]

        if not valid_model_name:
            return jsonify({"error": "Не знайдено жодної моделі"}), 500

        model = genai.GenerativeModel(valid_model_name)

        # 🔥 ОНОВЛЕНИЙ, СУВОРИЙ ПРОМПТ 🔥
        prompt = f"""
Ти — розумний помічник на тесті.
Питання: {question}
Варіанти відповідей: {options}

КРИТИЧНІ ПРАВИЛА:
1. Якщо до питання додано картинку, вона є ГОЛОВНИМ критерієм. Відповідай ТІЛЬКИ те, що зображено на фото, навіть якщо інші текстові варіанти теж є правильними за загальним смислом.
2. Звертай увагу на число: якщо питання в однині ("Вкажіть назву", "Оберіть") — повертай СУВОРО 1 варіант. Якщо в множині ("Оберіть малюнки") — повертай всі правильні.

ФОРМАТ ВІДПОВІДІ (ТІЛЬКИ JSON):
- Текстові варіанти: ["Точний текст"]
- Картинки-варіанти: ["Варіант 1", "Варіант 2"]
"""
        
        contents = [prompt]
        for img in images_data:
            if "label" in img:
                contents.append(img["label"])
            contents.append({
                "mime_type": img["mime_type"],
                "data": img["data"]
            })

        response = model.generate_content(contents)
        
        answer = response.text.replace('```json', '').replace('```', '').strip()

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
