from flask import Flask, jsonify, send_from_directory
import speech_recognition as sr
import threading
import time
import os

app = Flask(__name__, static_folder='', static_url_path='')

last_item = {"id": None, "name": "", "price": 0}

ITEMS = {
    "veg burger": {
        "id": 1,
        "name": "Veg Burger",
        "price": 80,
        "image": "https://i.imgur.com/3ZQ3ZVv.png",
        "ingredients": ["Lettuce", "Tomato", "Patty", "Bun", "Sauce"]
    },
    "paneer pizza": {
        "id": 2,
        "name": "Paneer Pizza",
        "price": 120,
        "image": "https://i.imgur.com/6eZ3OQK.png",
        "ingredients": ["Paneer", "Cheese", "Tomato", "Capsicum", "Oregano"]
    },
    "french fries": {
        "id": 3,
        "name": "Fries",
        "price": 50,
        "image": "https://i.imgur.com/C1vZqkJ.png",
        "ingredients": ["Potatoes", "Salt", "Oil"]
    }
}


def recognize_loop():
    global last_item
    r = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        r.adjust_for_ambient_noise(source)

    while True:
        with mic as source:
            print("🎤 Listening...")
            audio = r.listen(source)

        try:
            text = r.recognize_google(audio).lower()
            print("🗣️ Recognized:", text)

            for key in ITEMS:
                if key in text:
                    last_item = ITEMS[key]
                    break
        except Exception as e:
            print("❌", str(e))
        time.sleep(1)

@app.route("/")
def serve_index():
    return send_from_directory('', 'index.html')

@app.route("/latest_item")
def get_latest():
    return jsonify(last_item)

if __name__ == "__main__":
    threading.Thread(target=recognize_loop, daemon=True).start()
    app.run(debug=True)
