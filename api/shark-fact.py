from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def shark_fact():
    return jsonify({"ok": True, "msg": "Shark API is alive 🦈"})
