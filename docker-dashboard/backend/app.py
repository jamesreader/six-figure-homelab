from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

#Environment variables for DB connection
from urllib.parse import urlparse

database_url = os.getenv('DATABASE_URL', 'postgresql://dashuser:dashpass@localhost:5432/dashboard')
url = urlparse(database_url)

DB_CONFIG = {
    'host': url.hostname,
    'database': url.path[1:],
    'user': url.username,
    'password': url.password
}

def get_db():
	return psycopg2.connect(**DB_CONFIG)


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

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
