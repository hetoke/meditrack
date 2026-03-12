from services.record_service import fetch_records_page


class RecordController:
    def __init__(self):
        self.current_page = 1
        self.total_records = 0
        self._last_query = object()  # sentinel, never equals any string

    def get_page(self, page, page_size, search_query=None):
        query_changed = search_query != self._last_query
        data, total = fetch_records_page(page, page_size, search_query,
                                         count=query_changed)
        if query_changed:
            self.total_records = total
            self._last_query = search_query
        return data
