from flask import Blueprint, request, jsonify, Response
import requests

ollama_bp = Blueprint('ollama', __name__)
OLLAMA_URL = "http://ollama.ollama.svc.cluster.local:11434"

@ollama_bp.route('/models', methods=['GET'])
def list_models():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ollama_bp.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": data.get("model"),
                "prompt": data.get("prompt"),
                "stream": False
            }
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

