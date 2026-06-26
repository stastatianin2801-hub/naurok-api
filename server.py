import os
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
# Дозволяємо запити з будь-яких сайтів
CORS(app, resources={r"/solve": {"origins": "*"}})

# 🔑 ПУЛ КЛЮЧІВ: створи ще 3-4 безкоштовних акаунти Google і впиши ключі сюди
# Сервер сам прочитає ключі з налаштувань Render, а не з коду
api_keys_str = os.environ.get("API_KEYS", "")
API_KEYS = api_keys_str.split(",") if api_keys_str else []


@app.route('/solve', methods=['POST'])
def solve_question():
    data = request.json
    question = data.get('question')
    options = data.get('options')
    
    # 🎲 Магія: при кожному запиті беремо випадковий ключ із пулу
    if not API_KEYS:
        return jsonify({"error": "Ключі не налаштовані"}), 500
    current_key = random.choice(API_KEYS)
    genai.configure(api_key=current_key)
    
    # Використовуємо модель, яка в тебе стабільно запрацювала
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Ти розумний помічник. Тобі дається питання з тесту і варіанти відповідей. 
    Твоя задача: вибрати правильний варіант і написати ТІЛЬКИ його точний текст. 
    Без пояснень, без крапок в кінці, без зайвих символів. Тільки текст правильної відповіді.
    
    Питання: {question}
    Варіанти відповідей: {options}
    """
    
    try:
        response = model.generate_content(prompt)
        ai_answer = response.text.strip()
        print(f"🤖 Відповідь від ключа {current_key[-4:]}: {ai_answer}")
        return jsonify({"answer": ai_answer})
    except Exception as e:
        print(f"❌ Помилка API: {e}")
        return jsonify({"error": "Помилка ШІ"}), 500

if __name__ == '__main__':
    # ☁️ Налаштування для хмари: беремо той порт, який видасть сервер
    port = int(os.environ.get('PORT', 5000))
    # host='0.0.0.0' обов'язково потрібен, щоб сервер було видно в інтернеті
    app.run(host='0.0.0.0', port=port)
