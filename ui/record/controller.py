from __future__ import annotations

from typing import Optional

from services.record_service import fetch_records_page, Record


class RecordController:
    def __init__(self) -> None:
        self.current_page: int = 1
        self.total_records: int = 0
        self._last_query: object = object()

    def get_page(
        self,
        page: int,
        page_size: int,
        search_query: Optional[str] = None,
    ) -> list[Record]:
        query_changed = search_query != self._last_query
        data, total = fetch_records_page(
            page, page_size, search_query, count=query_changed
        )
        if query_changed:
            self.total_records = total
            self._last_query = search_query
        return data
