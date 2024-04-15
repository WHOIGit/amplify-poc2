import os

from pymongo import MongoClient

class MongoLogger:
    def __init__(self, conn_url, db_name='provenance', collection_name='logs'):
        self.conn_url = conn_url
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None

    def _connect(self):
        self.client = MongoClient(self.conn_url)
        # will create db/collection if it doesn't exist
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def log(self, entry):
        if self.client is None:
            self._connect()
        return self.collection.insert_one(entry).inserted_id

    @staticmethod
    def connection_url(host, user=None, password=None, port=27017):
        auth = f"{user}:{password}@" if user and password else ""
        port= f":{port}" if port else ""
        return f"mongodb://{auth}{host}{port}"

    @staticmethod
    def from_environment():
        db_host = os.environ.get('PROVENANCE_DB_HOST', 'localhost')
        db_user = os.environ.get('PROVENANCE_DB_USER')
        db_pass = os.environ.get('PROVENANCE_DB_PASSWORD')
        db_name = os.environ.get('PROVENANCE_DB_NAME', 'provenance')
        db_coll = os.environ.get('PROVENANCE_DB_COLLECTION', 'logs')
        db_port = os.environ.get('PROVENANCE_DB_PORT', 27017)
        return MongoLogger(MongoLogger.connection_url(db_host,db_user,db_pass,db_port), db_name, db_coll)

    @staticmethod
    def from_args(host, user=None, password=None, port=27017, db_name='provenance', db_coll='logs'):
        return MongoLogger(MongoLogger.connection_url(host, user, password, port), db_name, db_coll)
