from django.core.management.base import BaseCommand
from expenses.models import Expense, ExpenseParticipant
from django.contrib.auth.models import User
from decimal import Decimal

from django.db.models import Sum, F, FloatField

class Command(BaseCommand):
    help = 'Manage expenses via console'

    def add_arguments(self, parser):
        parser.add_argument('--action', type=str, choices=['add', 'list', 'balance'], help='Action to perform')
        parser.add_argument('--user', type=str, help='Username')
        parser.add_argument('--amount', type=float, help='Total amount of the expense')
        parser.add_argument('--type', type=str, choices=['EQUAL', 'EXACT', 'PERCENT'], help='Type of expense')
        parser.add_argument('--participants', type=str, nargs='+', help='List of participants')
        parser.add_argument('--shares', type=float, nargs='+', help='Shares for each participant')

    def handle(self, *args, **options):
        if options['action'] == 'add':
            self.add_expense(options)
        elif options['action'] == 'list':
            self.list_expenses()
        elif options['action'] == 'balance':
            self.show_balances(options['user'])
        else:
            self.stdout.write(self.style.ERROR('Invalid action. Use --action add, list, or balance.'))

    def add_expense(self, options):
        try:
            user = User.objects.get(username=options['user'])
            expense = Expense.objects.create(
                user=user,
                amount=options['amount'],
                expense_type=options['type']
            )
            for participant, share in zip(options['participants'], options['shares']):
                user = User.objects.get(username=participant)
                ExpenseParticipant.objects.create(
                    expense=expense,
                    user=user,
                    share=Decimal(share)
                )
            self.stdout.write(self.style.SUCCESS('Expense added successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error adding expense: {e}'))

    def list_expenses(self):
        expenses = Expense.objects.all()
        for expense in expenses:
            self.stdout.write(f'{expense.name} - {expense.amount} - {expense.expense_type}')

    def show_balances(self, username):
        # Implementation for showing balances for a user
        pass



    def calculate_balances(user):
        expenses = ExpenseParticipant.objects.filter(user=user)
        total_paid = expenses.filter(expense__payer=user).aggregate(total_paid=Sum('share'))['total_paid'] or 0

        total_owed = expenses.exclude(expense__payer=user).aggregate(total_owed=Sum('share'))['total_owed'] or 0

        balance = total_paid - total_owed

        return balance


    def simplify_expenses(user):
        # Retrieve all balances involving the user
        transactions = ExpenseParticipant.objects.filter(
            expense__participants=user
        ).values('user').annotate(total=Sum('share'))
        
        # Process simplification logic
        simplified_transactions = []
        # Simplification logic goes here
        return simplified_transactions