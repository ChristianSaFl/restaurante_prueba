import unittest
from main.python.domain.entities.product import Product

class TestProduct(unittest.TestCase):

    def test_valid_product(self):
        p = Product("Pizza", 20)
        self.assertEqual(p.name, "Pizza")
        self.assertEqual(p.price, 20)

    def test_empty_name(self):
        with self.assertRaises(ValueError):
            Product("", 10)

    def test_negative_price(self):
        with self.assertRaises(ValueError):
            Product("Pizza", -5)

if __name__ == "__main__":
    unittest.main()