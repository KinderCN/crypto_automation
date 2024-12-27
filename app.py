from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

# Définir un token secret
SECRET_TOKEN = os.getenv('SECRET_TOKEN', 'votre_token_secret')

@app.route('/run-script', methods=['POST'])
def run_script():
    token = request.headers.get('Authorization')
    if token != f"Bearer {SECRET_TOKEN}":
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        # Exécuter le script Python
        result = subprocess.run(['python', 'script_crypto_automation.py'], capture_output=True, text=True, check=True)
        return jsonify({
            'status': 'success',
            'output': result.stdout
        }), 200
    except subprocess.CalledProcessError as e:
        return jsonify({
            'status': 'error',
            'output': e.stderr
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)