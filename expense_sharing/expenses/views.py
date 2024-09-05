from collections import defaultdict
from rest_framework.response import Response
from expenses.tasks import send_expense_email_task
from django.conf import settings
from rest_framework.decorators import action, api_view
from .services import calculate_balances
from rest_framework import viewsets, status
from .models import User, Expense, Participant, Transaction
from .serializers import UserSerializer, ExpenseSerializer, ParticipantSerializer, TransactionSerializer
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer


    def create(self, request, *args, **kwargs):
        print(request.data)
        data = request.data
        amount = data['amount']
        type = data['type']
        payer = int(data['payer'])
        shares = data['shares']

        print(payer)

        calculated_shares = {}
        # Validate and process based on expense type
        if type == 'PERCENT':
            total_percent = sum(shares.values())
            if round(total_percent, 2) != 100.00:
                return Response({'error': 'Total percentage must sum up to 100.'}, status=status.HTTP_400_BAD_REQUEST)
            calculated_shares = {int(user_id): round(amount * (percent / total_percent), 2) for user_id, percent in shares.items()}
        elif type == 'EXACT':
            total_shares = sum(shares.values())
            if round(total_shares, 2) != round(amount, 2):
                return Response({'error': 'Total shares must equal the total amount.'}, status=status.HTTP_400_BAD_REQUEST)
            calculated_shares = {int(user) : share for user, share in shares.items()}
        elif type == 'EQUAL':
            num_users = len(shares)
            equal_share = round(amount / num_users, 2)
            calculated_shares = {int(user_id): equal_share for user_id in shares.keys()}
            # Ensure that the total amount is correctly rounded
            total_shares = equal_share * num_users
            if round(total_shares, 2) != round(amount, 2):
                # Adjust the first user to balance the rounding error
                first_user = next(iter(shares.keys()))
                calculated_shares[int(first_user)] = round(equal_share + (amount - total_shares), 2)

        # as a payer substract the total amount paid :-
        if payer in calculated_shares.keys():
            calculated_shares[payer] -= amount
        elif len(calculated_shares) != 0:
            calculated_shares[payer] = -1 * amount

        print(calculated_shares)

        payer = User.objects.get(userId=payer)
        expense = Expense.objects.create(
            amount=amount,
            type=type,
            description=data.get('description'),
            payer=payer)

        # Update Participant records
        self.update_participant(expense, calculated_shares)

        #Update the Transaction records
        self.update_transaction(calculated_shares)

        serializer = ExpenseSerializer(expense)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update_participant(self, expense, shares):
        # Get existing Participant records
        existing_participant = Participant.objects.filter(expense=expense.expenseId)
        existing_user_ids = existing_participant.values_list('user_id', flat=True)

        # Remove old Participant records if necessary
        for participant in existing_participant:
            if participant.user_id not in shares:
                participant.delete()
                print("deleted")

        # Add or update Participant records
        for user_id, share in shares.items():
            if user_id in existing_user_ids:
                # Update existing Participant record
                participant = Participant.objects.filter(expense=expense.expenseId, user_id=user_id).update(share=share)
            else:
                # Create new UserExpense record
                user = User.objects.get(userId=user_id)
                participant = Participant.objects.create(user= user, expense=expense, share=share)
            print(participant)

        # Notify users about the update
        self.notify_users(expense, shares)

    def notify_users(self, expense, shares):
        for user_id, share in shares.items():
            print("sending mail")
            send_expense_email_task.delay(user_id, expense.expenseId, share, expense.payer.userId)
            print("mail sent")

    def update_transaction(self, shares):
        to_user = min(zip(shares.values(), shares.keys()))[1]
        try:
            to_user = User.objects.get(userId=to_user)
        except ObjectDoesNotExist:
            print("One or both of the users do not exist.")
        for from_user, amount in shares.items():
            try:
                from_user = User.objects.get(userId=from_user)
            except ObjectDoesNotExist:
                    print("One or both of the users do not exist.")
            if from_user != to_user :
                transaction = Transaction.objects.create(fromUser = from_user, toUser = to_user,amount = amount)
                print(transaction)


class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

@api_view(['GET'])
def user_expenses(request, user_id):
    try:
        user = User.objects.get(userId=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)

    # Get all expenses where the user is a participant
    expenses = Expense.objects.filter(participant__user=user)
    serializer = ExpenseSerializer(expenses, many=True)

    return Response(serializer.data)

@api_view(['GET'])
def user_balances(request, user_id):
    try:
        user = User.objects.get(userId=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)

    # Calculate all balances
    all_balances = calculate_balances()

    # Filter out non-zero balances related to the user
    user_balance = all_balances.get(user, Decimal(0))
    relevant_balances = {u.userId: balance for u, balance in all_balances.items() if balance != 0 and u != user}

    response_data = {
        'user_balance': user_balance,
        'others_balances': relevant_balances
    }

    return Response(response_data)

@api_view(['GET'])
def simplify_expenses(request):
    """Simplify the debts and return the result."""
    simplified_debts = defaultdict(lambda: defaultdict(int))
    
    all_balances = calculate_balances()
    lenders = []
    borrowers = []
    
    for user, balance in all_balances.items():
        if balance > 0:
            lenders.append((user, balance))
        elif balance < 0:
            borrowers.append((user, -balance))

    i, j = 0, 0
    while i < len(lenders) and j < len(borrowers):
        lender, lend_amount = lenders[i]
        borrower, borrow_amount = borrowers[j]

        transfer_amount = min(lend_amount, borrow_amount)

        simplified_debts[borrower][lender] = transfer_amount
        lenders[i] = (lender, lend_amount - transfer_amount)
        borrowers[j] = (borrower, borrow_amount - transfer_amount)

        if lenders[i][1] == 0:
            i += 1
        if borrowers[j][1] == 0:
            j += 1

    # result = {}
    result = []
    for borrower, lenders in simplified_debts.items():
        for lender, amount in lenders.items():
        # result[borrower.userId] = {lender.userId: amount for lender, amount in lenders.items()}
            result.append(f" {borrower.name} owes {lender.name} : {amount}")
    return Response(result, status=status.HTTP_200_OK)


