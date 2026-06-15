import unittest
from unittest.mock import MagicMock

from main.python.domain.entities.product import Product
from main.python.domain.entities.order import Order
from main.python.domain.services.order_service import OrderService

class TestOrderService(unittest.TestCase):

    def test_create_order_success(self):
        mock_repo = MagicMock()

        service = OrderService(mock_repo)

        p = Product("Pizza", 10)
        order = Order()
        order.add_product(p, 2)

        total = service.create_order(order)

        self.assertEqual(total, 20)
        mock_repo.save.assert_called_once()

    def test_create_empty_order(self):
        mock_repo = MagicMock()
        service = OrderService(mock_repo)

        order = Order()

        with self.assertRaises(ValueError):
            service.create_order(order)

if __name__ == "__main__":
    unittest.main()