import sqlite3
import json
import os
from pathlib import Path
from .logger import logger

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'medical_records.db'

class Database:
    def __init__(self):
        self.db = None

    def get_db(self):
        return self.db

    def all(self, sql, params=()):
        if not self.db:
            raise Exception('Database not connected')
        cursor = self.db.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def get(self, sql, params=()):
        if not self.db:
            raise Exception('Database not connected')
        cursor = self.db.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()

    def run(self, sql, params=()):
        if not self.db:
            raise Exception('Database not connected')
        cursor = self.db.cursor()
        cursor.execute(sql, params)
        self.db.commit()
        return {'lastID': cursor.lastrowid, 'changes': cursor.rowcount}

    def connect(self):
        try:
            logger.info('Iniciando conexão com banco de dados...')
            
            # Ensure data directory exists
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            self.db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self.db.row_factory = sqlite3.Row
            
            logger.info(f'Conectado ao banco de dados SQLite: {DB_PATH}')
            logger.info(f'Database atribuído, status: {self.db is not None}')
            logger.info('Database conectado, iniciando inicialização...')
            
            self.init_database()
        except Exception as error:
            raise error

    def init_database(self):
        try:
            logger.info(f'initDatabase chamado, self.db status: {self.db is not None}')
            self.create_tables()
            self.seed_database()
            logger.info('Banco de dados inicializado com sucesso')
        except Exception as error:
            logger.error(f'Erro ao inicializar banco de dados: {error}')
            raise error

    def create_tables(self):
        try:
            drop_queries = [
                "DROP TABLE IF EXISTS ai_logs",
                "DROP TABLE IF EXISTS medical_records",
                "DROP TABLE IF EXISTS patients"
            ]

            create_queries = [
                '''CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patientId INTEGER UNIQUE,
                    fullName TEXT NOT NULL,
                    dateOfBirth TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    allergies TEXT,
                    currentMedications TEXT,
                    habits TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )''',

                '''CREATE TABLE IF NOT EXISTS medical_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recordId INTEGER UNIQUE,
                    patientId INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    type TEXT NOT NULL,
                    symptoms TEXT,
                    prescriptions TEXT,
                    observations TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patientId) REFERENCES patients(patientId)
                )''',

                '''CREATE TABLE IF NOT EXISTS ai_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    patient_id INTEGER,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    sources TEXT,
                    response_time_ms INTEGER,
                    risk_flags TEXT,
                    validation_passed BOOLEAN,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(patientId)
                )'''
            ]

            for i, query in enumerate(drop_queries):
                logger.info(f'Executando query {i+1}/{len(drop_queries)}: {query[:50]}...')
                self.db.execute(query)
                logger.info(f'Query {i+1} executada com sucesso')

            for i, query in enumerate(create_queries):
                logger.info(f'Executando query {i+1}/{len(create_queries)}: {query[:50]}...')
                self.db.execute(query)
                logger.info(f'Query {i+1} executada com sucesso')

            logger.info('Tabelas recriadas com sucesso')
        except Exception as error:
            raise error

    def seed_database(self):
        try:
            row = self.get("SELECT COUNT(*) as count FROM patients")
            
            if row and row['count'] > 0:
                logger.info('Banco de dados já contém dados, pulando seed')
                return

            mock_data_path = Path(__file__).parent.parent.parent / 'data' / 'patients-mock.json'

            if not mock_data_path.exists():
                logger.warn('Arquivo patients-mock.json não encontrado')
                return

            with open(mock_data_path, 'r', encoding='utf-8') as f:
                mock_data = json.load(f)

            patients = mock_data.get('patients', [])

            if not patients:
                logger.warn('Nenhum paciente encontrado no arquivo mock')
                return

            patients_inserted = 0
            for patient in patients:
                try:
                    self.run('''
                        INSERT INTO patients (patientId, fullName, dateOfBirth, gender, allergies, currentMedications, habits)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        patient.get('patientId'),
                        patient.get('fullName'),
                        patient.get('dateOfBirth'),
                        patient.get('gender'),
                        json.dumps(patient.get('allergies', [])),
                        json.dumps(patient.get('currentMedications', [])),
                        json.dumps(patient.get('habits', []))
                    ))
                    patients_inserted += 1
                except Exception as err:
                    logger.error(f'Erro ao inserir paciente: {err}')

            logger.info(f'{patients_inserted} pacientes inseridos com sucesso')
            
            if patients_inserted > 0:
                self.seed_medical_records(mock_data.get('records', []))
        except Exception as error:
            raise error

    def seed_medical_records(self, records):
        try:
            if not records:
                logger.warn('Nenhum registro médico encontrado no arquivo mock')
                return

            row = self.get("SELECT name FROM sqlite_master WHERE type='table' AND name='medical_records'")

            if not row:
                logger.error('Tabela medical_records não existe!')
                raise Exception('Tabela medical_records não existe')

            logger.info(f'Inserindo {len(records)} registros médicos...')
            records_inserted = 0

            for record in records:
                try:
                    self.run('''
                        INSERT INTO medical_records (recordId, patientId, date, type, symptoms, prescriptions, observations)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record.get('recordId'),
                        record.get('patientId'),
                        record.get('date'),
                        record.get('type'),
                        json.dumps(record.get('symptoms', [])),
                        json.dumps(record.get('prescriptions', [])),
                        json.dumps(record.get('observations', []))
                    ))
                    records_inserted += 1
                except Exception as err:
                    logger.error(f'Erro ao inserir registro médico: {err}')

            logger.info(f'{records_inserted} registros médicos inseridos com sucesso')
        except Exception as error:
            raise error

    def close(self):
        try:
            if self.db:
                self.db.close()
                logger.info('Conexão com banco de dados fechada')
        except Exception as error:
            logger.error(f'Erro ao fechar conexão com banco de dados: {error}')
            raise error

database = Database()
