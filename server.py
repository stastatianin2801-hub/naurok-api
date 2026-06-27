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

        random.shuffle(API_KEYS)
        last_error = ""

        for api_key in API_KEYS:
            try:
                genai.configure(api_key=api_key)
                
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
                    raise Exception("Не знайдено жодної моделі")

                model = genai.GenerativeModel(valid_model_name)

                # 🔥 УНІВЕРСАЛЬНИЙ ПРОМПТ ДЛЯ ВСІХ ТИПІВ ТЕСТІВ 🔥
                prompt = f"""
Ти — математично точний помічник на тесті.
Питання: {question}
Варіанти відповідей: {options}

УНІВЕРСАЛЬНІ ПРАВИЛА:
1. Якщо до питання є картинка (підпис "Зображення до питання:"), уважно проаналізуй її. Вона є ГОЛОВНОЮ підказкою!
2. Якщо варіанти відповідей — це текст (наприклад "Пролісок", "Крокус"), ти ПОВИНЕН повернути точний текст правильного варіанту.
3. Якщо варіанти відповідей — це картинки (наприклад "[Картинка]"), ти ПОВИНЕН повернути номери правильних варіантів (наприклад "Варіант 1").
4. Звертай увагу на однину/множину в питанні. Якщо просять обрати один варіант — повертай суворо один!

ФОРМАТ ВІДПОВІДІ (ТІЛЬКИ JSON):
- Для текстових варіантів: ["Пролісок"] або ["Варіант А", "Варіант Б"]
- Для варіантів-картинок: ["Варіант 1"] або ["Варіант 2", "Варіант 4"]
"""
                
                contents = [prompt]
                for img in images_data:
                    if "label" in img:
                        contents.append(img["label"])
                    contents.append({
                        "mime_type": img["mime_type"],
                        "data": img["data"]
                    })

                # Залишаємо нульову температуру для максимальної точності
                response = model.generate_content(
                    contents,
                    generation_config={"temperature": 0.0}
                )
                
                answer = response.text.replace('```json', '').replace('```', '').strip()

                return jsonify({"answer": answer})

            except Exception as e:
                error_msg = str(e)
                print(f"❌ Помилка: {error_msg}")
                if "429" in error_msg or "quota" in error_msg.lower():
                    last_error = error_msg
                    continue 
                else:
                    return jsonify({"error": error_msg}), 500

        return jsonify({"error": f"Всі {len(API_KEYS)} ключів вичерпали ліміт! Зачекай хвилину. Деталі: {last_error}"}), 429

    except Exception as e:
        print("=== Server Error ===")
        print(str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return f"API is live! Keys configured: {len(API_KEYS)}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
