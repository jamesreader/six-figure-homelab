from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import psycopg2
import os
from datetime import datetime

#Load environment variables from .env
load_dotenv()

#import Auth blueprint
from auth import auth_bp
from ollama import ollama_bp

app = Flask(__name__)

#CORS configuration - allow credentials for httpOnly cookies
CORS(app, supports_credentials=True, origins=['http://dashboard.homelab', 'http://localhost:3000'])

#Register auth blueprint with api/auth prefix
app.register_blueprint(auth_bp, url_prefix='/api/auth')
#Register ollama blueprint with api/ollama prefix
app.register_blueprint(ollama_bp, url_prefix='/api/ollama')

#Environment variables for DB connection
from db import get_db_connection as get_db

@app.route('/api/visits', methods=['GET', 'POST'])
def visits():
        conn = get_db()
        cur = conn.cursor()

        #create table if not exists
        cur.execute('''
                CREATE TABLE IF NOT EXISTS visits (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP,
                        ip_address VARCHAR(50)
                )
        ''')
        conn.commit()

        if request.method == 'POST':
                cur.execute(
                        'INSERT INTO visits (timestamp, ip_address) VALUES (%s, %s)',
                        (datetime.now(), request.remote_addr)
                )
                conn.commit()
                return jsonify({'status': 'recorded'})

        cur.execute('SELECT COUNT(*) FROM visits')
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return jsonify({'total_visits': count})

@app.route('/api/tracker/progress', methods=['GET'])
def get_progress():
        try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute('SELECT task_key, completed FROM roadmap_progress')
                rows = cur.fetchall()
                cur.close()
                conn.close()

                progress = {row[0]: row[1] for row in rows}
                return jsonify(progress), 200
        except Exception as e:
                return jsonify({'error': str(e)}), 500

@app.route('/api/tracker/progress', methods=['POST'])
def update_progress():
        try:
                data = request.get_json()
                task_key = data.get('task_key')
                completed =data.get('completed')

                if not task_key or completed is None:
                        return jsonify({'error': 'task_key and completed are required'}), 400

                conn = get_db()
                cur = conn.cursor()

                cur.execute('''
                        INSERT INTO roadmap_progress (task_key, completed, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (task_key)
                        DO UPDATE SET completed = %s, updated_at = CURRENT_TIMESTAMP
                ''', (task_key, completed, completed))

                conn.commit()
                cur.close()
                conn.close()

                return jsonify({'success': True, 'task_key': task_key, 'completed': completed}), 200
        except Exception as e:
                return jsonify({'error': str(e)}), 500

@app.route('/api/tracker/progress/bulk', methods=['POST'])
def bulk_import_progress():
        try:
                data = request.get_json()

                conn = get_db()
                cur = conn.cursor()

                for task_key, completed in data.items():
                        cur.execute('''
                                INSERT INTO roadmap_progress (task_key, completed, updated_at)
                                VALUES(%s, %S, CURRENT_TIMESTAMP)
                                ON CONFLICT (task_key)
                                DO UPDATE SET completed = %s, updated_at = CURRENT_TIMESTAMP
                        ''', (task_key, completed, completed))

                conn.commit()
                cur.close()
                conn.close()

                return jsonify({'succes': True, 'imported': len(data)}), 200
        except Exception as e:
                return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
# Test Sun Dec  7 03:52:13 UTC 2025
# Ollama integration Sat Dec 13 05:49:08 UTC 2025
