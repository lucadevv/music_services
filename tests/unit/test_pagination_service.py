"""Tests for PaginationService."""
import pytest
from app.services.pagination_service import PaginationService


class TestPaginationService:
    """Test pagination logic."""

    def test_basic_pagination(self):
        """Test basic pagination with default page size."""
        items = list(range(25))  # 0-24

        result = PaginationService.paginate(items, page=1, page_size=10)

        assert len(result["items"]) == 10
        assert result["items"] == list(range(0, 10))
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["page_size"] == 10
        assert result["pagination"]["total_results"] == 25
        assert result["pagination"]["total_pages"] == 3
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is False

    def test_second_page(self):
        """Test pagination on page 2."""
        items = list(range(25))

        result = PaginationService.paginate(items, page=2, page_size=10)

        assert len(result["items"]) == 10
        assert result["items"] == list(range(10, 20))
        assert result["pagination"]["page"] == 2
        assert result["pagination"]["total_results"] == 25

    def test_third_page_partial(self):
        """Test pagination on last page (partial)."""
        items = list(range(25))

        result = PaginationService.paginate(items, page=3, page_size=10)

        assert len(result["items"]) == 5
        assert result["items"] == list(range(20, 25))
        assert result["pagination"]["page"] == 3
        assert result["pagination"]["has_next"] is False
        assert result["pagination"]["has_prev"] is True

    def test_custom_page_size(self):
        """Test pagination with custom page size."""
        items = list(range(25))

        result = PaginationService.paginate(items, page=1, page_size=5)

        assert len(result["items"]) == 5
        assert result["items"] == list(range(0, 5))
        assert result["pagination"]["page_size"] == 5

    def test_max_page_size(self):
        """Test that page size is capped at max_page_size."""
        items = list(range(100))

        result = PaginationService.paginate(items, page=1, page_size=1000, max_page_size=50)

        assert result["pagination"]["page_size"] == 50
        assert len(result["items"]) == 50

    def test_empty_items(self):
        """Test pagination with empty list."""
        items = []

        result = PaginationService.paginate(items, page=1, page_size=10)

        assert len(result["items"]) == 0
        assert result["pagination"]["total_results"] == 0
        assert result["pagination"]["total_pages"] == 0

    def test_validate_pagination_params_defaults(self):
        """Test parameter validation with defaults."""
        limit, page, start_index = PaginationService.validate_pagination_params()

        assert limit == 10  # Default page size
        assert page == 1
        assert start_index == 0

    def test_validate_pagination_params_custom(self):
        """Test parameter validation with custom values."""
        limit, page, start_index = PaginationService.validate_pagination_params(
            limit=20,
            start_index=30
        )

        assert limit == 20
        assert page == 2  # (30 // 20) + 1 = 2
        assert start_index == 30

    def test_validate_pagination_params_exceed_max(self):
        """Test parameter validation with limit exceeding max."""
        limit, page, start_index = PaginationService.validate_pagination_params(
            limit=100,
            start_index=0,
            max_limit=50
        )

        assert limit == 50  # Capped at max_limit

    def test_first_page_flags(self):
        """Test has_prev is False on first page."""
        items = list(range(25))

        result = PaginationService.paginate(items, page=1, page_size=10)

        assert result["pagination"]["has_prev"] is False
        assert result["pagination"]["has_next"] is True

    def test_last_page_flags(self):
        """Test has_next is False on last page."""
        items = list(range(25))

        result = PaginationService.paginate(items, page=3, page_size=10)

        assert result["pagination"]["has_prev"] is True
        assert result["pagination"]["has_next"] is False
