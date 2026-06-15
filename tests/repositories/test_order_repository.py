import unittest
from main.python.domain.entities.product import Product
from main.python.domain.entities.order import Order
from main.python.domain.repositories.order_repository import InMemoryOrderRepository

class TestOrderRepository(unittest.TestCase):

    def test_save_and_find(self):
        repo = InMemoryOrderRepository()

        p = Product("Pizza", 10)
        order = Order()
        order.add_product(p, 1)

        repo.save(order)

        result = repo.find_by_id(1)

        self.assertIsNotNone(result)
        self.assertEqual(result.total(), 10)

    def test_find_nonexistent(self):
        repo = InMemoryOrderRepository()
        self.assertIsNone(repo.find_by_id(99))

if __name__ == "__main__":
    unittest.main()