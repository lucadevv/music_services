"""Pagination service for standardized list responses."""
from typing import List, Dict, Any, Optional
from math import ceil
from datetime import datetime


class PaginationService:
    """Service for handling pagination logic."""

    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 50

    @staticmethod
    def paginate(
        items: List[Any],
        page: int = 1,
        page_size: int = None,
        max_page_size: int = None
    ) -> Dict[str, Any]:
        """
        Apply pagination to a list of items.

        Args:
            items: List of items to paginate
            page: Current page number (1-indexed)
            page_size: Number of items per page (default: 10)
            max_page_size: Maximum allowed page size (default: 50)

        Returns:
            Dict with items, pagination metadata, and status
        """
        page_size = page_size or PaginationService.DEFAULT_PAGE_SIZE
        max_page_size = max_page_size or PaginationService.MAX_PAGE_SIZE

        # Validate and normalize page size
        page_size = min(page_size, max_page_size)
        page_size = max(page_size, 1)

        # Validate page number
        page = max(page, 1)

        total_results = len(items)
        total_pages = ceil(total_results / page_size) if page_size > 0 else 0

        # Calculate slice indices
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        # Apply pagination
        paginated_items = items[start_index:end_index]

        # Determine navigation flags
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "items": paginated_items,
            "pagination": {
                "total_results": total_results,
                "total_pages": total_pages,
                "page": page,
                "page_size": page_size,
                "start_index": start_index,
                "end_index": end_index,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }

    @staticmethod
    def validate_pagination_params(
        limit: Optional[int] = None,
        start_index: Optional[int] = None,
        max_limit: Optional[int] = None
    ) -> tuple[int, int, int]:
        """
        Validate and normalize pagination parameters.

        Args:
            limit: Number of items per page (default: 10)
            start_index: Starting index (default: 0)
            max_limit: Maximum allowed limit (default: 50)

        Returns:
            Tuple of (page_size, page, start_index)
        """
        max_limit = max_limit or PaginationService.MAX_PAGE_SIZE

        # Default values
        if limit is None:
            limit = PaginationService.DEFAULT_PAGE_SIZE
        if start_index is None:
            start_index = 0

        # Validate and normalize limit
        limit = min(limit, max_limit)
        limit = max(limit, 1)

        # Validate start_index
        start_index = max(start_index, 0)

        # Calculate page from start_index and limit
        page = (start_index // limit) + 1

        return limit, page, start_index
