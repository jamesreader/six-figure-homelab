import psycopg2
import os
from urllib.parse import urlparse

database_url = os.getenv('DATABASE_URL', 'postgresql://dashuser:dashpass@localhost:5432/dashboard')
url = urlparse(database_url)

DB_CONFIG = {
    'host': url.hostname,
    'database': url.path[1:],
    'user': url.username,
    'password': url.password
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)
