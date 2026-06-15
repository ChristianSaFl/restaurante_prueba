class Bill:
    TAX_RATE = 0.18
    MAX_DISCOUNT = 50

    def __init__(self, order):
        if order is None:
            raise ValueError("Order is required")

        if order.is_empty():
            raise ValueError("Cannot create bill for empty order")

        self.order = order
        self.discount_percentage = 0
        self.tip = 0
        self.paid = False

    def subtotal(self):
        return self.order.total()

    def apply_discount(self, percentage):
        if percentage is None or percentage < 0 or percentage > self.MAX_DISCOUNT:
            raise ValueError("Invalid discount percentage")

        self.discount_percentage = percentage

    def add_tip(self, amount):
        if amount is None or amount < 0:
            raise ValueError("Tip cannot be negative")

        self.tip = amount

    def tax(self):
        amount_after_discount = self.subtotal() - self.discount_amount()
        return amount_after_discount * self.TAX_RATE

    def discount_amount(self):
        return self.subtotal() * self.discount_percentage / 100

    def total(self):
        amount_after_discount = self.subtotal() - self.discount_amount()
        return amount_after_discount + self.tax() + self.tip

    def mark_as_paid(self):
        if self.paid:
            raise ValueError("Bill is already paid")

        self.paid = True