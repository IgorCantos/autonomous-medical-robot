import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.config.database import database
from src.config.logger import logger
from src.routes import api_routes

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Enable CORS
CORS(app)

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# Register routes (routes already have /api prefix)
app.register_blueprint(api_routes)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'service': 'medical-assistant'}), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'Autonomous Medical Robot',
        'version': '1.0.0',
        'status': 'running'
    }), 200

def initialize_database():
    try:
        logger.info('Inicializando banco de dados...')
        database.connect()
        logger.info('Banco de dados inicializado com sucesso')
    except Exception as error:
        logger.error(f'Erro ao inicializar banco de dados: {error}')
        raise error

if __name__ == '__main__':
    # Initialize database
    initialize_database()
    
    # Get port from environment
    port = int(os.getenv('PORT', 3000))
    
    logger.info(f'Servidor iniciando na porta {port}...')
    
    try:
        app.run(host='0.0.0.0', port=port, debug=os.getenv('NODE_ENV') == 'development')
    except KeyboardInterrupt:
        logger.info('Servidor interrompido pelo usuário')
    finally:
        database.close()
        logger.info('Servidor finalizado')
