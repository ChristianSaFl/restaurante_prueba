class TableRepository:
    def save(self, table):
        raise NotImplementedError

    def find_by_number(self, number):
        raise NotImplementedError

    def list_all(self):
        raise NotImplementedError

    def list_available(self):
        raise NotImplementedError


class InMemoryTableRepository(TableRepository):
    def __init__(self):
        self.tables = {}

    def save(self, table):
        self.tables[table.number] = table

    def find_by_number(self, number):
        return self.tables.get(number, None)

    def list_all(self):
        return list(self.tables.values())

    def list_available(self):
        return [table for table in self.tables.values() if table.is_available()]