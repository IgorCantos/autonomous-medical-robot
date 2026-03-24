import json
from ..config.database import database

def parse_record_fields(row):
    return {
        **dict(row),
        'symptoms': json.loads(row['symptoms'] if row['symptoms'] else '[]'),
        'prescriptions': json.loads(row['prescriptions'] if row['prescriptions'] else '[]'),
        'observations': json.loads(row['observations'] if row['observations'] else '[]')
    }

class MedicalRecord:
    @staticmethod
    def create(record_data):
        patient_id = record_data.get('patientId')
        date = record_data.get('date')
        record_type = record_data.get('type')
        symptoms = record_data.get('symptoms', [])
        prescriptions = record_data.get('prescriptions', [])
        observations = record_data.get('observations', [])

        sql = '''
            INSERT INTO medical_records (patientId, date, type, symptoms, prescriptions, observations)
            VALUES (?, ?, ?, ?, ?, ?)
        '''

        try:
            result = database.run(sql, (
                patient_id,
                date,
                record_type,
                json.dumps(symptoms),
                json.dumps(prescriptions),
                json.dumps(observations)
            ))
            return MedicalRecord.find_by_id(result['lastID'])
        except Exception as error:
            raise Exception(f'Erro ao criar prontuário: {error}')

    @staticmethod
    def find_by_id(record_id):
        try:
            row = database.get("SELECT * FROM medical_records WHERE id = ?", (record_id,))
            return parse_record_fields(row) if row else None
        except Exception as error:
            raise Exception(f'Erro ao buscar prontuário: {error}')

    @staticmethod
    def find_by_patient_id(patient_id, limit=20):
        try:
            rows = database.all(
                "SELECT * FROM medical_records WHERE patientId = ? ORDER BY id ASC LIMIT ?",
                (patient_id, limit)
            )
            return [parse_record_fields(row) for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao buscar prontuários do paciente: {error}')

    @staticmethod
    def find_by_type(patient_id, record_type):
        try:
            rows = database.all(
                "SELECT * FROM medical_records WHERE patientId = ? AND type = ? ORDER BY id ASC",
                (patient_id, record_type)
            )
            return [parse_record_fields(row) for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao buscar prontuários por tipo: {error}')

    @staticmethod
    def find_by_date_range(patient_id, start_date, end_date):
        try:
            rows = database.all(
                "SELECT * FROM medical_records WHERE patientId = ? AND date BETWEEN ? AND ? ORDER BY id ASC",
                (patient_id, start_date, end_date)
            )
            return [parse_record_fields(row) for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao buscar prontuários por período: {error}')

    @staticmethod
    def update(record_id, record_data):
        date = record_data.get('date')
        record_type = record_data.get('type')
        symptoms = record_data.get('symptoms', [])
        prescriptions = record_data.get('prescriptions', [])
        observations = record_data.get('observations', [])

        sql = '''
            UPDATE medical_records
            SET date = ?, type = ?, symptoms = ?, prescriptions = ?, observations = ?
            WHERE id = ?
        '''

        try:
            result = database.run(sql, (
                date,
                record_type,
                json.dumps(symptoms),
                json.dumps(prescriptions),
                json.dumps(observations),
                record_id
            ))
            return result['changes'] > 0
        except Exception as error:
            raise Exception(f'Erro ao atualizar prontuário: {error}')

    @staticmethod
    def delete(record_id):
        try:
            result = database.run("DELETE FROM medical_records WHERE id = ?", (record_id,))
            return result['changes'] > 0
        except Exception as error:
            raise Exception(f'Erro ao deletar prontuário: {error}')

    @staticmethod
    def find_all_with_patient_data():
        try:
            rows = database.all('''
                SELECT
                    mr.*,
                    p.fullName as patientName,
                    p.patientId as patientId
                FROM medical_records mr
                JOIN patients p ON mr.patientId = p.patientId
                ORDER BY mr.id ASC
            ''')
            return [parse_record_fields(row) for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao buscar prontuários com dados de paciente: {error}')

    @staticmethod
    def search(patient_id, query):
        try:
            search_pattern = f'%{query}%'
            rows = database.all(
                "SELECT * FROM medical_records WHERE patientId = ? AND (symptoms LIKE ? OR prescriptions LIKE ? OR observations LIKE ?) ORDER BY id ASC",
                (patient_id, search_pattern, search_pattern, search_pattern)
            )
            return [parse_record_fields(row) for row in rows]
        except Exception as error:
            raise Exception(f'Erro ao pesquisar prontuários: {error}')
