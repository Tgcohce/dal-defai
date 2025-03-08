from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Allow CORS only for specific domains (React frontend on localhost:3000)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

messages = [{"text": "Welcome to Curtis Portal", "sender": "system"}]

@app.route('/api/messages', methods=['GET'])
def get_messages():
    return jsonify(messages)

@app.route('/api/messages', methods=['POST'])
def post_message():
    new_message = request.json.get('text')
    if new_message:
        messages.append({"text": new_message, "sender": "user"})
        return jsonify({"text": new_message, "sender": "user"}), 201
    return jsonify({"error": "No message text provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)

