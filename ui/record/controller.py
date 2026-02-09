from services.record_service import fetch_records

class RecordController:
    def __init__(self):
        self.records = []
        self.filtered_records = []
        self.current_page = 1

    def refresh(self):
        self.records = fetch_records()
        self.filtered_records = self.records.copy()
        self.current_page = 1
