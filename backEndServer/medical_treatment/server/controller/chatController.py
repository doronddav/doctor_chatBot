from flask import request, jsonify
from medical_treatment import run_doctor_chat_session, get_session_info, reset_session


def get_chatBot_chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "")
        user_name = data.get("name", "משתמש")
        action = data.get("action", "chat")

        if action == "info":
            session_info = get_session_info(user_name)
            return jsonify(session_info)

        elif action == "reset":
            reset_session(user_name)
            return jsonify({"message": "Session reset successfully"})

        elif action == "chat":
            if not user_input:
                return jsonify({"error": "Missing message"}), 400

            reply = run_doctor_chat_session(user_name, user_input)
            session_info = get_session_info(user_name)

            return jsonify({
                "reply": reply,
                "stage": session_info.get('stage', 'unknown'),
                "finished": session_info.get('stage') == 'finished'
            })

        else:
            return jsonify({"error": "Invalid action"}), 400

    except Exception as e:
        print(f"Error in chat controller: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    finally:
        print("Request processed")
