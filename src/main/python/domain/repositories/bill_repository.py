class BillRepository:
    def save(self, bill):
        raise NotImplementedError

    def find_by_id(self, bill_id):
        raise NotImplementedError

    def list_all(self):
        raise NotImplementedError


class InMemoryBillRepository(BillRepository):
    def __init__(self):
        self.bills = {}
        self.current_id = 1

    def save(self, bill):
        if not hasattr(bill, "id"):
            bill.id = self.current_id
            self.current_id += 1

        self.bills[bill.id] = bill
        return bill

    def find_by_id(self, bill_id):
        return self.bills.get(bill_id, None)

    def list_all(self):
        return list(self.bills.values())