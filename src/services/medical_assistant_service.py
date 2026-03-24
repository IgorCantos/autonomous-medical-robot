import os
import re
import uuid
from datetime import datetime
from ..config.logger import logger
from ..config.database import database
from ..services.rag_service import medical_rag_service
from ..models.ai_log import AILog

class MedicalAssistantService:
    def __init__(self):
        self.max_response_time = int(os.getenv('MAX_RESPONSE_TIME', 30000))
        self.max_context_length = int(os.getenv('MAX_CONTEXT_LENGTH', 10000))

    def process_query(self, query, patient_id=None):
        start_time = datetime.now()
        session_id = str(uuid.uuid4())

        logger.info('Processando consulta médica com RAG', {
            'sessionId': session_id,
            'patientId': patient_id,
            'query': query[:100]
        })

        try:
            validation = self.validate_query(query)
            if not validation['isValid']:
                raise Exception(f"Consulta inválida: {', '.join(validation['errors'])}")

            response = self.process_with_rag(query, patient_id)

            response_time = int((datetime.now() - start_time).total_seconds() * 1000)

            self.log_interaction({
                'session_id': session_id,
                'patient_id': patient_id,
                'query': query,
                'response': response['response'],
                'sources': response.get('sources', []),
                'response_time_ms': response_time,
                'risk_flags': response.get('riskFlags', []),
                'validation_passed': response.get('validated', False)
            })

            logger.info('Consulta processada com sucesso', {
                'sessionId': session_id,
                'responseTime': response_time,
                'method': 'rag'
            })

            return {
                'session_id': str(session_id).strip(),
                'patientId': int(patient_id) if patient_id else None,
                'query': str(query),
                'response': response['response'],
                'sources': response.get('sources', []),
                'responseTime': response_time,
                'timestamp': datetime.now().isoformat(),
                'riskFlags': response.get('riskFlags', []),
                'validated': response.get('validated', False),
                'method': 'rag'
            }
        except Exception as error:
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.error('Erro ao processar consulta', {
                'sessionId': session_id,
                'patientId': patient_id,
                'error': str(error),
                'responseTime': response_time
            })

            self.log_interaction({
                'session_id': session_id,
                'patient_id': patient_id,
                'query': query,
                'response': f'Erro: {str(error)}',
                'sources': ['Sistema'],
                'response_time_ms': response_time,
                'isError': True
            })

            raise error

    def process_with_rag(self, query, patient_id):
        try:
            logger.info('Processing with RAG', {
                'patientId': patient_id,
                'query': query[:100]
            })

            rag_response = medical_rag_service.query_medical_records(query, patient_id)

            return {
                'response': rag_response,
                'validated': False
            }
        except Exception as error:
            logger.error(f'RAG processing failed: {error}')
            raise error

    def validate_query(self, query):
        errors = []

        if not query or not query.strip():
            errors.append('A consulta não pode estar vazia')

        if len(query) > 1000:
            errors.append('A consulta é muito longa (máximo 1000 caracteres)')

        forbidden_patterns = [
            re.compile(r'prescreva.*medicamento', re.IGNORECASE),
            re.compile(r'qual.*dosagem', re.IGNORECASE),
            re.compile(r'quanto.*tomar', re.IGNORECASE),
            re.compile(r'posso.*parar.*medicamento', re.IGNORECASE)
        ]

        for pattern in forbidden_patterns:
            if pattern.search(query):
                errors.append('A consulta contém solicitação inadequada')
                break

        return {
            'isValid': len(errors) == 0,
            'errors': errors
        }

    def log_interaction(self, log_data):
        try:
            logger.info('Salvando log de interação', {
                'session_id': log_data.get('session_id'),
                'patient_id': log_data.get('patient_id'),
                'hasQuery': bool(log_data.get('query')),
                'hasResponse': bool(log_data.get('response')),
                'riskFlags': log_data.get('risk_flags')
            })

            AILog.create(log_data)
            logger.info('Log salvo com sucesso', {'session_id': log_data.get('session_id')})
        except Exception as error:
            logger.error(f'Erro ao registrar interação: {error}')

    def get_session_history(self, session_id):
        try:
            logs = AILog.find_by_session(session_id)
            return [{
                'query': log['query'],
                'response': log['response'],
                'sources': json.loads(log['sources']) if log['sources'] else [],
                'timestamp': log['created_at'],
                'responseTime': log['response_time_ms']
            } for log in logs]
        except Exception as error:
            logger.error(f'Erro ao buscar histórico da sessão: {error}')
            raise error

    def get_patient_ai_history(self, patient_id, limit=20):
        try:
            logs = AILog.find_by_patient(patient_id, limit)
            return [{
                'sessionId': log['session_id'],
                'query': log['query'],
                'response': log['response'],
                'sources': json.loads(log['sources']) if log['sources'] else [],
                'timestamp': log['created_at'],
                'responseTime': log['response_time_ms']
            } for log in logs]
        except Exception as error:
            logger.error(f'Erro ao buscar histórico de IA do paciente: {error}')
            raise error

    def get_system_analytics(self, start_date, end_date):
        return AILog.get_analytics(start_date, end_date)

import json
medical_assistant_service = MedicalAssistantService()
