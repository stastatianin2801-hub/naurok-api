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

                # 🔥 НОВИЙ СУВОРИЙ ПРОМПТ 🔥
                prompt = f"""
Ти — надзвичайно точний помічник на тесті. Жодної креативності, тільки сувора логіка.
Питання: {question}
Варіанти відповідей: {options}

КРИТИЧНІ ПРАВИЛА ДЛЯ КАРТИНОК:
1. Я передаю тобі кілька картинок. Перед кожною є підпис (наприклад, "Картинка для Варіанту 1:").
2. Уважно проаналізуй КОЖНУ картинку окремо. Зрозумій, що на ній зображено.
3. Вибери ТІЛЬКИ ті варіанти, які на 100% відповідають питанню (наприклад, якщо свято весняне - беремо, якщо зимове, літнє чи осіннє - точно ігноруємо).

ФОРМАТ ВІДПОВІДІ (ТІЛЬКИ JSON):
- Якщо вибираєш текст: ["Текст 1", "Текст 2"]
- Якщо вибираєш картинки: ["Варіант 1", "Варіант 3", "Варіант 8"]
"""
                
                contents = [prompt]
                for img in images_data:
                    if "label" in img:
                        contents.append(img["label"])
                    contents.append({
                        "mime_type": img["mime_type"],
                        "data": img["data"]
                    })

                # 🔥 СНАЙПЕРСЬКИЙ РЕЖИМ (0.0 Креативності) 🔥
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
