import json
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog, messagebox

DATA_DIR = Path("data")

class JSONStore:
    def __init__(self, filename):
        self.file_path = DATA_DIR / filename
        self.data = []
        self._load()

    def _load(self):
        if self.file_path.exists():
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = []

    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get_all(self):
        return self.data

    def get_by_id(self, item_id):
        return next((item for item in self.data if item.get("id") == item_id), None)

    def add(self, item):
        if self.get_by_id(item["id"]):
            raise ValueError(f"Item with ID {item['id']} already exists.")
        self.data.append(item)
        self.save()

    def update(self, item_id, updates):
        item = self.get_by_id(item_id)
        if not item:
            raise ValueError(f"Item with ID {item_id} not found.")
        item.update(updates)
        self.save()

    def delete(self, item_id):
        self.data = [item for item in self.data if item.get("id") != item_id]
        self.save()


