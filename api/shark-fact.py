from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def shark_fact():
    return jsonify({"msg": "Shark API is alive 🦈"})
