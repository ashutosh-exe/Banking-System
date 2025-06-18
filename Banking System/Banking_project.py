import json
import uuid
from abc import ABC, abstractmethod

# --- Account Base Class ---
class Account(ABC):
    def __init__(self, account_number: str, account_holder_id: str, initial_balance: float = 0.0):
        self._account_number = account_number
        self._account_holder_id = account_holder_id
        self._balance = initial_balance

    @property
    def account_number(self):
        return self._account_number

    @property
    def balance(self):
        return self._balance

    @property
    def account_holder_id(self):
        return self._account_holder_id

    @abstractmethod
    def deposit(self, amount: float) -> bool:
        pass

    @abstractmethod
    def withdraw(self, amount: float) -> bool:
        pass

    def display_details(self) -> str:
        return f"Acc No: {self._account_number}, Balance: ${self._balance:.2f}"

    @abstractmethod
    def to_dict(self) -> dict:
        pass


class SavingsAccount(Account):
    def __init__(self, account_number, account_holder_id, initial_balance=0.0, interest_rate=0.01):
        super().__init__(account_number, account_holder_id, initial_balance)
        self._interest_rate = interest_rate

    @property
    def interest_rate(self):
        return self._interest_rate

    @interest_rate.setter
    def interest_rate(self, value):
        if value >= 0:
            self._interest_rate = value

    def deposit(self, amount):
        if amount > 0:
            self._balance += amount
            return True
        return False

    def withdraw(self, amount):
        if 0 < amount <= self._balance:
            self._balance -= amount
            return True
        return False

    def apply_interest(self):
        self._balance += self._balance * self._interest_rate

    def display_details(self):
        return f"{super().display_details()}, Interest Rate: {self._interest_rate * 100:.2f}%"

    def to_dict(self):
        return {
            "type": "savings",
            "account_number": self._account_number,
            "account_holder_id": self._account_holder_id,
            "balance": self._balance,
            "interest_rate": self._interest_rate
        }

class CheckingAccount(Account):
    def __init__(self, account_number, account_holder_id, initial_balance=0.0, overdraft_limit=0.0):
        super().__init__(account_number, account_holder_id, initial_balance)
        self._overdraft_limit = overdraft_limit

    @property
    def overdraft_limit(self):
        return self._overdraft_limit

    @overdraft_limit.setter
    def overdraft_limit(self, value):
        if value >= 0:
            self._overdraft_limit = value

    def deposit(self, amount):
        if amount > 0:
            self._balance += amount
            return True
        return False

    def withdraw(self, amount):
        if self._balance - amount >= -self._overdraft_limit:
            self._balance -= amount
            return True
        return False

    def display_details(self):
        return f"{super().display_details()}, Overdraft Limit: ${self._overdraft_limit:.2f}"

    def to_dict(self):
        return {
            "type": "checking",
            "account_number": self._account_number,
            "account_holder_id": self._account_holder_id,
            "balance": self._balance,
            "overdraft_limit": self._overdraft_limit
        }


class Customer:
    def __init__(self, customer_id: str, name: str, address: str):
        self._customer_id = customer_id
        self._name = name
        self._address = address
        self._account_numbers = []

    @property
    def customer_id(self):
        return self._customer_id

    @property
    def name(self):
        return self._name

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, new_address):
        self._address = new_address

    @property
    def account_numbers(self):
        return self._account_numbers.copy()

    def add_account_number(self, account_number: str):
        if account_number not in self._account_numbers:
            self._account_numbers.append(account_number)

    def remove_account_number(self, account_number: str):
        if account_number in self._account_numbers:
            self._account_numbers.remove(account_number)

    def display_details(self):
        return (f"Customer ID: {self._customer_id}, Name: {self._name}, "
                f"Address: {self._address}, Accounts: {len(self._account_numbers)}")

    def to_dict(self):
        return {
            "customer_id": self._customer_id,
            "name": self._name,
            "address": self._address,
            "account_numbers": self._account_numbers
        }



class Bank:
    def __init__(self, customer_file='customers.json', account_file='accounts.json'):
        self._customers = {}
        self._accounts = {}
        self._customer_file = customer_file
        self._account_file = account_file
        self._load_data()

    def _load_data(self):
        try:
            with open(self._customer_file, 'r') as f:
                customer_data = json.load(f)
                for cust in customer_data:
                    c = Customer(cust['customer_id'], cust['name'], cust['address'])
                    for acc_num in cust.get('account_numbers', []):
                        c.add_account_number(acc_num)
                    self._customers[c.customer_id] = c
        except FileNotFoundError:
            pass

        try:
            with open(self._account_file, 'r') as f:
                account_data = json.load(f)
                for acc in account_data:
                    acc_type = acc.pop('type')
                    balance = acc.pop('balance', 0.0)

                    if acc_type == 'savings':
                        account = SavingsAccount(
                            account_number=acc['account_number'],
                            account_holder_id=acc['account_holder_id'],
                            initial_balance=balance,
                            interest_rate=acc.get('interest_rate', 0.01)
                        )
                    elif acc_type == 'checking':
                        account = CheckingAccount(
                            account_number=acc['account_number'],
                            account_holder_id=acc['account_holder_id'],
                            initial_balance=balance,
                            overdraft_limit=acc.get('overdraft_limit', 0.0)
                        )
                    else:
                        continue

                    self._accounts[account.account_number] = account


        except FileNotFoundError:
            pass

    def _save_data(self):
        with open(self._customer_file, 'w') as f:
            json.dump([c.to_dict() for c in self._customers.values()], f, indent=2)
        with open(self._account_file, 'w') as f:
            json.dump([a.to_dict() for a in self._accounts.values()], f, indent=2)

    def add_customer(self, customer: Customer) -> bool:
        if customer.customer_id in self._customers:
            return False
        self._customers[customer.customer_id] = customer
        self._save_data()
        return True

    def remove_customer(self, customer_id: str) -> bool:
        customer = self._customers.get(customer_id)
        if customer and not customer.account_numbers:
            del self._customers[customer_id]
            self._save_data()
            return True
        return False

    def create_account(self, customer_id: str, account_type: str,
                       initial_balance: float = 0.0, **kwargs):
        if customer_id not in self._customers:
            return None
        account_number = str(uuid.uuid4())
        if account_type == 'savings':
            account = SavingsAccount(account_number, customer_id,
                                     initial_balance, kwargs.get('interest_rate', 0.01))
        elif account_type == 'checking':
            account = CheckingAccount(account_number, customer_id,
                                      initial_balance, kwargs.get('overdraft_limit', 0.0))
        else:
            return None
        self._accounts[account.account_number] = account
        self._customers[customer_id].add_account_number(account.account_number)
        self._save_data()
        return account

    def deposit(self, account_number: str, amount: float) -> bool:
        account = self._accounts.get(account_number)
        if account and account.deposit(amount):
            self._save_data()
            return True
        return False

    def withdraw(self, account_number: str, amount: float) -> bool:
        account = self._accounts.get(account_number)
        if account and account.withdraw(amount):
            self._save_data()
            return True
        return False

    def transfer_funds(self, from_acc_num: str, to_acc_num: str, amount: float) -> bool:
        from_acc = self._accounts.get(from_acc_num)
        to_acc = self._accounts.get(to_acc_num)
        if from_acc and to_acc and from_acc.withdraw(amount):
            if to_acc.deposit(amount):
                self._save_data()
                return True
            else:
                from_acc.deposit(amount)  # rollback
        return False

    def get_customer_accounts(self, customer_id: str):
        customer = self._customers.get(customer_id)
        if not customer:
            return []
        return [self._accounts[acc_num] for acc_num in customer.account_numbers if acc_num in self._accounts]

    def display_all_customers(self):
        for customer in self._customers.values():
            print(customer.display_details())

    def display_all_accounts(self):
        for account in self._accounts.values():
            print(account.display_details())

    def apply_all_interest(self):
        for account in self._accounts.values():
            if isinstance(account, SavingsAccount):
                account.apply_interest()
        self._save_data()


def main():
    bank = Bank()

    menu = """
    === Banking System Menu ===
    1. Add Customer
    2. Remove Customer
    3. Create Account
    4. Deposit
    5. Withdraw
    6. Transfer Funds
    7. View Customer Accounts
    8. View All Customers
    9. View All Accounts
    10. Apply Interest to All Savings Accounts
    11. Exit
    """

    while True:
        print(menu)
        choice = input("Enter your choice (1-11): ").strip()

        if choice == '1':
            cid = input("Customer ID: ").strip()
            name = input("Full Name: ").strip()
            address = input("Address: ").strip()
            customer = Customer(cid, name, address)
            if bank.add_customer(customer):
                print("Customer added successfully.")
            else:
                print("Customer ID already exists.")

        elif choice == '2':
            cid = input("Customer ID to remove: ").strip()
            if bank.remove_customer(cid):
                print("Customer removed successfully.")
            else:
                print("Cannot remove customer. Either not found or has active accounts.")

        elif choice == '3':
            cid = input("Customer ID: ").strip()
            acct_type = input("Account Type (savings/checking): ").strip().lower()
            init_bal = float(input("Initial Balance: "))
            extra = {}
            if acct_type == 'savings':
                extra['interest_rate'] = float(input("Interest Rate (e.g. 0.01 for 1%): "))
            elif acct_type == 'checking':
                extra['overdraft_limit'] = float(input("Overdraft Limit: "))

            acct = bank.create_account(cid, acct_type, init_bal, **extra)
            if acct:
                print(f"{acct_type.capitalize()} account created. Account No: {acct.account_number}")
            else:
                print("Account creation failed.")

        elif choice == '4':
            acc = input("Account Number: ").strip()
            amt = float(input("Amount to deposit: "))
            if bank.deposit(acc, amt):
                print("Deposit successful.")
            else:
                print("Deposit failed.")

        elif choice == '5':
            acc = input("Account Number: ").strip()
            amt = float(input("Amount to withdraw: "))
            if bank.withdraw(acc, amt):
                print("Withdrawal successful.")
            else:
                print("Withdrawal failed.")

        elif choice == '6':
            from_acc = input("From Account Number: ").strip()
            to_acc = input("To Account Number: ").strip()
            amt = float(input("Amount to transfer: "))
            if bank.transfer_funds(from_acc, to_acc, amt):
                print("Transfer successful.")
            else:
                print("Transfer failed.")

        elif choice == '7':
            cid = input("Customer ID: ").strip()
            accounts = bank.get_customer_accounts(cid)
            if accounts:
                for acct in accounts:
                    print(acct.display_details())
            else:
                print("No accounts found or invalid customer.")

        elif choice == '8':
            print("All Customers:")
            bank.display_all_customers()

        elif choice == '9':
            print("All Accounts:")
            bank.display_all_accounts()

        elif choice == '10':
            bank.apply_all_interest()
            print("Interest applied to all savings accounts.")

        elif choice == '11':
            print("Exiting... Goodbye!")
            break

        else:
            print("Invalid option. Please try again.")


if __name__ == '__main__':
    main()



