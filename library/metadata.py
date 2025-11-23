# library/metadata.py
import json
import os


class MetadataDB:
    def __init__(self, path):
        self.path = path
        if os.path.exists(path):
            self.db = json.load(open(path))
        else:
            self.db = []
            self._save()

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.db, f, indent=2)

    def add_document(self, meta):
        self.db.append(meta)
        self._save()

    def get_all(self):
        return self.db
