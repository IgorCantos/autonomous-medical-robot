from flask import Blueprint, request, jsonify
import re
from ..services.medical_assistant_service import medical_assistant_service
from ..models.patient import Patient
from ..models.medical_record import MedicalRecord
from ..config.logger import logger

medical_assistant_controller = Blueprint('medical_assistant', __name__)

@medical_assistant_controller.route('/query', methods=['POST'])
def process_query():
    try:
        data = request.get_json()
        query = data.get('query')
        patient_id = data.get('patientId')

        if not query:
            return jsonify({'error': 'Query é obrigatória'}), 400

        if not patient_id:
            return jsonify({'error': 'patientId é obrigatório'}), 400

        if len(query) > 1000:
            return jsonify({'error': 'Query muito longa'}), 400

        forbidden_patterns = [
            r'prescreva.*medicamento',
            r'qual.*dosagem',
            r'quanto.*tomar'
        ]

        for pattern in forbidden_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return jsonify({'error': 'Consulta contém solicitação inadequada'}), 400

        result = medical_assistant_service.process_query(query, patient_id)
        return jsonify(result), 200
    except Exception as error:
        logger.error(f'Erro ao processar consulta: {error}')
        return jsonify({'error': str(error)}), 500

@medical_assistant_controller.route('/patients', methods=['GET'])
def get_patients():
    try:
        patients = Patient.find_all()
        return jsonify(patients), 200
    except Exception as error:
        logger.error(f'Erro ao buscar pacientes: {error}')
        return jsonify({'error': 'Erro ao buscar pacientes'}), 500

@medical_assistant_controller.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient_by_id(patient_id):
    try:
        patient = Patient.find_by_id(patient_id)
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        return jsonify(patient), 200
    except Exception as error:
        logger.error(f'Erro ao buscar paciente: {error}')
        return jsonify({'error': 'Erro ao buscar paciente'}), 500

@medical_assistant_controller.route('/patients/search', methods=['GET'])
def search_patients():
    try:
        query = request.args.get('q', '')
        patients = Patient.search(query)
        return jsonify(patients), 200
    except Exception as error:
        logger.error(f'Erro ao buscar pacientes: {error}')
        return jsonify({'error': 'Erro ao buscar pacientes'}), 500

@medical_assistant_controller.route('/patients/<int:patient_id>/medical-history', methods=['GET'])
def get_patient_medical_history(patient_id):
    try:
        patient = Patient.find_by_id(patient_id)
        if not patient:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        medical_history = Patient.get_medical_history(patient_id)
        return jsonify({
            'patient': patient,
            'medicalHistory': medical_history
        }), 200
    except Exception as error:
        logger.error(f'Erro ao buscar histórico médico: {error}')
        return jsonify({'error': 'Erro ao buscar histórico médico'}), 500

@medical_assistant_controller.route('/patient/<int:patient_id>/ai-history', methods=['GET'])
def get_patient_ai_history(patient_id):
    try:
        history = medical_assistant_service.get_patient_ai_history(patient_id)
        return jsonify({
            'patientId': patient_id,
            'history': history
        }), 200
    except Exception as error:
        logger.error(f'Erro ao buscar histórico de IA: {error}')
        return jsonify({'error': 'Erro ao buscar histórico de IA'}), 500

@medical_assistant_controller.route('/analytics', methods=['GET'])
def get_system_analytics():
    try:
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')

        if not start_date or not end_date:
            return jsonify({'error': 'startDate e endDate são obrigatórios'}), 400

        analytics = medical_assistant_service.get_system_analytics(start_date, end_date)
        return jsonify(analytics), 200
    except Exception as error:
        logger.error(f'Erro ao buscar analytics: {error}')
        return jsonify({'error': 'Erro ao buscar analytics'}), 500

@medical_assistant_controller.route('/session/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    try:
        history = medical_assistant_service.get_session_history(session_id)
        return jsonify({
            'session_id': session_id,
            'history': history
        }), 200
    except Exception as error:
        logger.error(f'Erro ao buscar histórico da sessão: {error}')
        return jsonify({'error': 'Erro ao buscar histórico da sessão'}), 500
