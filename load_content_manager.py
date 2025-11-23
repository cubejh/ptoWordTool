import os

class APIKeyManager:
    def __init__(self, filename="API_key.txt"):
        self.filename = filename

        if not os.path.exists(self.filename):
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write("")

    def read_key(self):
        """讀取 API key"""
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return ""

    def write_key(self, key: str):
        """寫入 API key"""
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(key.strip())

class ModelManager:
    def loadModel(self, filepath="setting/model.txt"):
        if not os.path.exists(filepath):
            return []

        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
