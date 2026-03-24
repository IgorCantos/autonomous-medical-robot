from datetime import datetime
import json
from ..config.database import database

class AILog:
    @staticmethod
    def create(log_data):
        session_id = log_data.get('session_id')
        patient_id = log_data.get('patient_id')
        query = log_data.get('query')
        response = log_data.get('response')
        sources = log_data.get('sources', [])
        response_time_ms = log_data.get('response_time_ms')
        risk_flags = log_data.get('risk_flags', [])
        validation_passed = log_data.get('validation_passed', False)
        created_at = datetime.now().isoformat()

        sql = '''
            INSERT INTO ai_logs (session_id, patient_id, query, response, sources, response_time_ms, risk_flags, validation_passed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        try:
            result = database.run(sql, (
                session_id,
                patient_id,
                query,
                response,
                json.dumps(sources),
                response_time_ms,
                json.dumps(risk_flags),
                validation_passed,
                created_at
            ))
            return AILog.find_by_id(result['lastID'])
        except Exception as error:
            raise Exception(f'Erro ao criar log: {error}')

    @staticmethod
    def find_by_id(log_id):
        try:
            row = database.get("SELECT * FROM ai_logs WHERE id = ?", (log_id,))
            return dict(row) if row else None
        except Exception as error:
            raise Exception(f'Erro ao buscar log: {error}')

    @staticmethod
    def find_by_session(session_id):
        try:
            rows = database.all(
                "SELECT * FROM ai_logs WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,)
            )
            return [dict(row) for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao buscar logs da sessão: {error}')

    @staticmethod
    def find_by_patient(patient_id, limit=20):
        try:
            rows = database.all(
                "SELECT * FROM ai_logs WHERE patient_id = ? ORDER BY created_at DESC LIMIT ?",
                (patient_id, limit)
            )
            return [dict(row) for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao buscar logs do paciente: {error}')

    @staticmethod
    def get_analytics(start_date, end_date):
        try:
            row = database.get('''
                SELECT
                    COUNT(*) as total_queries,
                    AVG(response_time_ms) as avg_response_time,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    COUNT(DISTINCT patient_id) as unique_patients
                FROM ai_logs
                WHERE created_at BETWEEN ? AND ?
            ''', (start_date, end_date))
            return dict(row) if row else {
                'total_queries': 0,
                'avg_response_time': 0,
                'unique_sessions': 0,
                'unique_patients': 0
            }
        except Exception as error:
            raise Exception(f'Erro ao buscar analytics: {error}')
