class Table:
    def __init__(self, number, capacity):
        if number is None or number <= 0:
            raise ValueError("Table number must be positive")

        if capacity is None or capacity <= 0:
            raise ValueError("Table capacity must be positive")

        self.number = number
        self.capacity = capacity
        self.occupied = False

    def occupy(self):
        if self.occupied:
            raise ValueError("Table is already occupied")

        self.occupied = True

    def release(self):
        if not self.occupied:
            raise ValueError("Table is already free")

        self.occupied = False

    def is_available(self):
        return not self.occupied