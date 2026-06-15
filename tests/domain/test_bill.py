import unittest

from main.python.domain.entities.product import Product
from main.python.domain.entities.order import Order
from main.python.domain.entities.bill import Bill


class TestBill(unittest.TestCase):

    def create_order(self):
        product = Product("Pizza", 20)
        order = Order()
        order.add_product(product, 2)
        return order

    def test_create_bill_success(self):
        order = self.create_order()

        bill = Bill(order)

        self.assertEqual(bill.subtotal(), 40)
        self.assertFalse(bill.paid)

    def test_create_bill_without_order(self):
        with self.assertRaises(ValueError):
            Bill(None)

    def test_create_bill_with_empty_order(self):
        order = Order()

        with self.assertRaises(ValueError):
            Bill(order)

    def test_apply_valid_discount(self):
        order = self.create_order()
        bill = Bill(order)

        bill.apply_discount(10)

        self.assertEqual(bill.discount_percentage, 10)
        self.assertEqual(bill.discount_amount(), 4)

    def test_apply_invalid_discount(self):
        order = self.create_order()
        bill = Bill(order)

        with self.assertRaises(ValueError):
            bill.apply_discount(60)

    def test_add_valid_tip(self):
        order = self.create_order()
        bill = Bill(order)

        bill.add_tip(5)

        self.assertEqual(bill.tip, 5)

    def test_add_negative_tip(self):
        order = self.create_order()
        bill = Bill(order)

        with self.assertRaises(ValueError):
            bill.add_tip(-1)

    def test_total_with_tax_discount_and_tip(self):
        order = self.create_order()
        bill = Bill(order)

        bill.apply_discount(10)
        bill.add_tip(5)

        # subtotal = 40
        # discount = 4
        # after discount = 36
        # tax = 36 * 0.18 = 6.48
        # total = 36 + 6.48 + 5 = 47.48
        self.assertAlmostEqual(bill.total(), 47.48)

    def test_mark_as_paid(self):
        order = self.create_order()
        bill = Bill(order)

        bill.mark_as_paid()

        self.assertTrue(bill.paid)

    def test_mark_bill_already_paid(self):
        order = self.create_order()
        bill = Bill(order)
        bill.mark_as_paid()

        with self.assertRaises(ValueError):
            bill.mark_as_paid()


if __name__ == "__main__":
    unittest.main()