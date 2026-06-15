class Product:
    def __init__(self, name, price):
        if name is None or name.strip() == "":
            raise ValueError("Product name cannot be empty")
        
        if price is None or price <= 0:
            raise ValueError("Product price must be positive")
        
        self.name = name
        self.price = price