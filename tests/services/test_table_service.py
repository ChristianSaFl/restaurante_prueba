import unittest
from unittest.mock import MagicMock

from main.python.domain.entities.table import Table
from main.python.domain.services.table_service import TableService


class TestTableService(unittest.TestCase):

    def test_create_table_success(self):
        mock_repository = MagicMock()
        mock_repository.find_by_number.return_value = None

        service = TableService(mock_repository)
        table = Table(1, 4)

        result = service.create_table(table)

        self.assertEqual(result.number, 1)
        mock_repository.find_by_number.assert_called_once_with(1)
        mock_repository.save.assert_called_once_with(table)

    def test_create_existing_table(self):
        mock_repository = MagicMock()
        existing_table = Table(1, 4)
        mock_repository.find_by_number.return_value = existing_table

        service = TableService(mock_repository)

        with self.assertRaises(ValueError):
            service.create_table(Table(1, 4))

        mock_repository.save.assert_not_called()

    def test_occupy_table_success(self):
        mock_repository = MagicMock()
        table = Table(1, 4)
        mock_repository.find_by_number.return_value = table

        service = TableService(mock_repository)
        result = service.occupy_table(1)

        self.assertFalse(result.is_available())
        mock_repository.find_by_number.assert_called_once_with(1)
        mock_repository.save.assert_called_once_with(table)

    def test_occupy_nonexistent_table(self):
        mock_repository = MagicMock()
        mock_repository.find_by_number.return_value = None

        service = TableService(mock_repository)

        with self.assertRaises(ValueError):
            service.occupy_table(99)

        mock_repository.save.assert_not_called()

    def test_release_table_success(self):
        mock_repository = MagicMock()
        table = Table(1, 4)
        table.occupy()
        mock_repository.find_by_number.return_value = table

        service = TableService(mock_repository)
        result = service.release_table(1)

        self.assertTrue(result.is_available())
        mock_repository.find_by_number.assert_called_once_with(1)
        mock_repository.save.assert_called_once_with(table)

    def test_get_available_tables(self):
        mock_repository = MagicMock()
        table = Table(1, 4)
        mock_repository.list_available.return_value = [table]

        service = TableService(mock_repository)
        result = service.get_available_tables()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].number, 1)
        mock_repository.list_available.assert_called_once()


if __name__ == "__main__":
    unittest.main()