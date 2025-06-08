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
        "image": "https://cdn.pixabay.com/photo/2016/03/05/19/02/hamburger-1238246_960_720.jpg",
        "ingredients": ["Bun", "Patty", "Lettuce", "Tomato", "Sauce"]
    },
    "paneer pizza": {
        "id": 2,
        "name": "Paneer Pizza",
        "price": 120,
        "image": "https://foodoncall.co.in/wp-content/uploads/2017/10/chatpata-paneer-pizza.jpg",
        "ingredients": ["Cheese", "Paneer", "Sauce", "Capsicum"]
    },
    "french fries": {
        "id": 3,
        "name": "Fries",
        "price": 50,
        "image": "https://cdn.pixabay.com/photo/2014/04/22/02/56/fries-329523_960_720.jpg",
        "ingredients": ["Potatoes", "Salt", "Oil"]
    },
    "pepsi": {
        "id": 4,
        "name": "pepsi",
        "price": 50,
        "image": "https://media.istockphoto.com/id/487787092/photo/can-and-glass-of-pepsi-cola.jpg?s=612x612&w=0&k=20&c=4Lqp4y8xCIF4IrV2a6DGkNhreCUwEAVfv3mEgb9aUJY=",
        "ingredients": ["Potatoes", "Salt", "Oil"]
    },
    "pasta": {
        "id": 5,
        "name": "pasta",
        "price": 50,
        "image": "https://img.freepik.com/free-photo/penne-pasta-tomato-sauce-with-chicken-tomatoes-wooden-table_2829-19739.jpg?semt=ais_hybrid&w=740",
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
