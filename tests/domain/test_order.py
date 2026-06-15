import unittest
from main.python.domain.entities.product import Product
from main.python.domain.entities.order import Order

class TestOrder(unittest.TestCase):

    def test_add_product_and_total(self):
        p = Product("Pizza", 10)
        order = Order()
        order.add_product(p, 2)

        self.assertEqual(order.total(), 20)

    def test_empty_order(self):
        order = Order()
        self.assertTrue(order.is_empty())

if __name__ == "__main__":
    unittest.main()