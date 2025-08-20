from flask import Blueprint
from server.controller import chatController

chatBot_bp = Blueprint('chatBot', __name__, url_prefix='/api/chatBot')


@chatBot_bp.route('/chat', methods=['POST'])
def get_chatBot_route():
    return chatController.get_chatBot_chat()
