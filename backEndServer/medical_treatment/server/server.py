
from server.routes.chatBotRoute import chatBot_bp
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


server = Flask(__name__)
CORS(server, origins=["http://localhost:3000", "http://localhost:4200",
     "http://127.0.0.1:3000", "http://localhost:5173"])
server.register_blueprint(chatBot_bp)

if __name__ == "__main__":
    server.run(debug=True)
