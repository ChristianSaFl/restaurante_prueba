class OrderRepository:
    def save(self, order):
        raise NotImplementedError

    def find_by_id(self, id):
        raise NotImplementedError


class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self.orders = {}
        self.current_id = 1

    def save(self, order):
        order.id = self.current_id
        self.orders[self.current_id] = order
        self.current_id += 1

    def find_by_id(self, id):
        return self.orders.get(id, None)