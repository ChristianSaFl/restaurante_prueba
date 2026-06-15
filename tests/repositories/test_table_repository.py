import unittest
from main.python.domain.entities.table import Table
from main.python.domain.repositories.table_repository import InMemoryTableRepository


class TestTableRepository(unittest.TestCase):

    def test_save_and_find_table(self):
        repository = InMemoryTableRepository()
        table = Table(1, 4)

        repository.save(table)
        result = repository.find_by_number(1)

        self.assertIsNotNone(result)
        self.assertEqual(result.number, 1)
        self.assertEqual(result.capacity, 4)

    def test_find_nonexistent_table(self):
        repository = InMemoryTableRepository()

        result = repository.find_by_number(99)

        self.assertIsNone(result)

    def test_list_available_tables(self):
        repository = InMemoryTableRepository()

        table1 = Table(1, 4)
        table2 = Table(2, 2)
        table2.occupy()

        repository.save(table1)
        repository.save(table2)

        available_tables = repository.list_available()

        self.assertEqual(len(available_tables), 1)
        self.assertEqual(available_tables[0].number, 1)


if __name__ == "__main__":
    unittest.main()