import os

from couchdb import Server


class CouchLogger(object):
    def __init__(self, couchdb_url, db_name):
        self.couchdb_url = couchdb_url
        self.db_name = db_name
        self.server = None

    def _connect(self):
        self.server = Server(self.couchdb_url)
        # create db if it doesn't exist
        if self.db_name not in self.server:
            self.server.create(self.db_name)
        self.db = self.server[self.db_name]

    def log(self, entry):
        if self.server is None:
            self._connect()
        self.db.save(entry)

    @staticmethod
    def from_environment():
        couchdb_host = os.environ.get('PROVENANCE_DB_HOST', 'localhost')
        couchdb_user = os.environ.get('PROVENANCE_DB_USER', 'admin')
        couchdb_password = os.environ.get('PROVENANCE_DB_PASSWORD', 'password')
        couchdb_db = os.environ.get('PROVENANCE_DB_NAME', 'provenance')
        return CouchLogger(f'http://{couchdb_user}:{couchdb_password}@{couchdb_host}:5984', couchdb_db)
