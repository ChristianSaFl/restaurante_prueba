class Order:
    def __init__(self):
        self.items = []

    def add_product(self, product, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        
        self.items.append((product, quantity))

    def total(self):
        return sum(p.price * q for p, q in self.items)

    def is_empty(self):
        return len(self.items) == 0