import unittest
from main.python.domain.entities.table import Table


class TestTable(unittest.TestCase):

    def test_create_valid_table(self):
        table = Table(1, 4)

        self.assertEqual(table.number, 1)
        self.assertEqual(table.capacity, 4)
        self.assertTrue(table.is_available())

    def test_invalid_table_number(self):
        with self.assertRaises(ValueError):
            Table(0, 4)

    def test_invalid_table_capacity(self):
        with self.assertRaises(ValueError):
            Table(1, 0)

    def test_occupy_table(self):
        table = Table(1, 4)

        table.occupy()

        self.assertFalse(table.is_available())

    def test_occupy_already_occupied_table(self):
        table = Table(1, 4)
        table.occupy()

        with self.assertRaises(ValueError):
            table.occupy()

    def test_release_table(self):
        table = Table(1, 4)
        table.occupy()

        table.release()

        self.assertTrue(table.is_available())

    def test_release_free_table(self):
        table = Table(1, 4)

        with self.assertRaises(ValueError):
            table.release()


if __name__ == "__main__":
    unittest.main()