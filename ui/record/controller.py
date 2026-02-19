from services.record_service import fetch_records_page


class RecordController:
    def __init__(self):
        self.current_page = 1
        self.total_records = 0

    def get_page(self, page, page_size, search_query=None):
        data, total = fetch_records_page(page, page_size, search_query)
        self.total_records = total
        return data
