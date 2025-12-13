from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from functools import wraps
from db import get_db_connection

auth_bp = Blueprint('auth', __name__)

# Load config from .env
JWT_SECRET = os.getenv('JWT_SECRET_KEY')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))

def token_required(f):
    """Decorator to protect routes - validates JWT from cookie"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Pass user_id to the route function
        return f(current_user_id, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    """Create new user account"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if username exists
    cur.execute('SELECT id FROM users WHERE username = %s', (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'error': 'Username already exists'}), 409
    
    # Create user
    password_hash = generate_password_hash(password)
    cur.execute(
        'INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id',
        (username, password_hash)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT in httpOnly cookie"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, password_hash FROM users WHERE username = %s', (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user or not check_password_hash(user[1], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate JWT
    token = jwt.encode(
        {
            'user_id': user[0],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    
    # Set httpOnly cookie
    response = make_response(jsonify({'message': 'Login successful'}))
    response.set_cookie(
        'token',
        token,
        httponly=True,
        secure=False,  # Set to True when using HTTPS
        samesite='Lax',
        max_age=JWT_EXPIRATION_HOURS * 3600
    )
    
    return response

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clear authentication cookie"""
    response = make_response(jsonify({'message': 'Logged out successfully'}))
    response.set_cookie('token', '', expires=0)
    return response

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user_id):
    """Get current user info - demonstrates protected route"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, username, created_at FROM users WHERE id = %s', (current_user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user[0],
        'username': user[1],
        'created_at': user[2].isoformat()
    })
