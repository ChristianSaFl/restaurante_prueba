class TableService:
    def __init__(self, repository):
        self.repository = repository

    def create_table(self, table):
        existing_table = self.repository.find_by_number(table.number)

        if existing_table is not None:
            raise ValueError("Table already exists")

        self.repository.save(table)
        return table

    def occupy_table(self, number):
        table = self.repository.find_by_number(number)

        if table is None:
            raise ValueError("Table not found")

        table.occupy()
        self.repository.save(table)
        return table

    def release_table(self, number):
        table = self.repository.find_by_number(number)

        if table is None:
            raise ValueError("Table not found")

        table.release()
        self.repository.save(table)
        return table

    def get_available_tables(self):
        return self.repository.list_available()