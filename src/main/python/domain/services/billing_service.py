from main.python.domain.entities.bill import Bill


BILL_NOT_FOUND = "Bill not found"


class BillingService:
    def __init__(self, repository):
        self.repository = repository

    def generate_bill(self, order):
        bill = Bill(order)
        self.repository.save(bill)
        return bill

    def apply_discount(self, bill_id, percentage):
        bill = self.repository.find_by_id(bill_id)

        if bill is None:
            raise ValueError(BILL_NOT_FOUND)

        bill.apply_discount(percentage)
        self.repository.save(bill)
        return bill

    def add_tip(self, bill_id, amount):
        bill = self.repository.find_by_id(bill_id)

        if bill is None:
            raise ValueError(BILL_NOT_FOUND)

        bill.add_tip(amount)
        self.repository.save(bill)
        return bill

    def pay_bill(self, bill_id):
        bill = self.repository.find_by_id(bill_id)

        if bill is None:
            raise ValueError(BILL_NOT_FOUND)

        bill.mark_as_paid()
        self.repository.save(bill)
        return bill