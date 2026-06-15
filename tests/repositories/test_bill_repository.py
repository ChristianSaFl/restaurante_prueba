import unittest

from main.python.domain.entities.product import Product
from main.python.domain.entities.order import Order
from main.python.domain.entities.bill import Bill
from main.python.domain.repositories.bill_repository import InMemoryBillRepository


class TestBillRepository(unittest.TestCase):

    def create_bill(self):
        product = Product("Pizza", 20)
        order = Order()
        order.add_product(product, 1)
        return Bill(order)

    def test_save_and_find_bill(self):
        repository = InMemoryBillRepository()
        bill = self.create_bill()

        repository.save(bill)
        result = repository.find_by_id(1)

        self.assertIsNotNone(result)
        self.assertEqual(result.subtotal(), 20)

    def test_find_nonexistent_bill(self):
        repository = InMemoryBillRepository()

        result = repository.find_by_id(99)

        self.assertIsNone(result)

    def test_list_all_bills(self):
        repository = InMemoryBillRepository()
        bill1 = self.create_bill()
        bill2 = self.create_bill()

        repository.save(bill1)
        repository.save(bill2)

        result = repository.list_all()

        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()