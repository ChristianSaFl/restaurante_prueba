class OrderService:
    def __init__(self, repository):
        self.repository = repository

    def create_order(self, order):
        if order.is_empty():
            raise ValueError("Order cannot be empty")
        
        self.repository.save(order)
        return order.total()