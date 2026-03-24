import json
from ..config.database import database

def parse_patient_fields(row):
    return {
        'id': row['id'],
        'patientId': row['patientId'],
        'fullName': row['fullName'],
        'dateOfBirth': row['dateOfBirth'],
        'gender': row['gender'],
        'allergies': json.loads(row['allergies'] if row['allergies'] else '[]'),
        'currentMedications': json.loads(row['currentMedications'] if row['currentMedications'] else '[]'),
        'habits': json.loads(row['habits'] if row['habits'] else '[]'),
        'created_at': row['created_at'],
        'updated_at': row['updated_at']
    }

class Patient:
    @staticmethod
    def find_all():
        try:
            rows = database.all("SELECT * FROM patients ORDER BY id ASC")
            return [parse_patient_fields(row) for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao buscar pacientes: {error}')

    @staticmethod
    def find_by_id(patient_id):
        try:
            row = database.get("SELECT * FROM patients WHERE patientId = ?", (patient_id,))
            return parse_patient_fields(row) if row else None
        except Exception as error:
            raise Exception(f'Erro ao buscar paciente: {error}')

    @staticmethod
    def search(query):
        try:
            search_query = f'%{query}%'
            rows = database.all(
                "SELECT * FROM patients WHERE fullName LIKE ? OR allergies LIKE ? OR currentMedications LIKE ? ORDER BY id ASC",
                (search_query, search_query, search_query)
            )
            return [parse_patient_fields(row) for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao buscar pacientes: {error}')

    @staticmethod
    def get_medical_history(patient_id):
        try:
            rows = database.all(
                "SELECT * FROM medical_records WHERE patientId = ? ORDER BY id ASC",
                (patient_id,)
            )
            return [{
                **dict(row),
                'symptoms': json.loads(row['symptoms'] if row['symptoms'] else '[]'),
                'prescriptions': json.loads(row['prescriptions'] if row['prescriptions'] else '[]'),
                'observations': json.loads(row['observations'] if row['observations'] else '[]')
            } for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao buscar histórico médico: {error}')

    @staticmethod
    def get_consultations(patient_id):
        try:
            rows = database.all(
                "SELECT * FROM medical_records WHERE patientId = ? AND type IN ('Consulta', 'Follow-up') ORDER BY id ASC",
                (patient_id,)
            )
            return [{
                **dict(row),
                'symptoms': json.loads(row['symptoms'] if row['symptoms'] else '[]'),
                'prescriptions': json.loads(row['prescriptions'] if row['prescriptions'] else '[]'),
                'observations': json.loads(row['observations'] if row['observations'] else '[]')
            } for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao buscar consultas: {error}')
