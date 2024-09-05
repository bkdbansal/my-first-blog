from rest_framework import serializers
from .models import User, Expense, Participant, Transaction

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['userId', 'name', 'email', 'mobileNumber']

class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['expense', 'user', 'share']

class ExpenseSerializer(serializers.ModelSerializer):
    # participants = ParticipantSerializer(many=True)

    class Meta:
        model = Expense
        fields = ['payer', 'expenseId', 'amount', 'type', 'description', 'createdAt']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['fromUser', 'toUser', 'amount', 'createdAt']



