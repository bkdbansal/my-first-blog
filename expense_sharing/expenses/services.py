from collections import defaultdict
from decimal import Decimal
from .models import Transaction

def calculate_balances():
    # Fetch all transactions
    transactions = Transaction.objects.all()
    balances = defaultdict(int)

    # Calculate balances based on transactions
    for transaction in transactions:
        balances[transaction.fromUser] -= transaction.amount
        balances[transaction.toUser] += transaction.amount

    return balances