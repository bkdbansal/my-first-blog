from django.db import models
from django.conf import settings
# Create your models here.

class User(models.Model):
    userId = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobileNumber = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Expense(models.Model):
    SPLIT_TYPE_CHOICES = [
        ('EQUAL', 'Equal'),
        ('EXACT', 'Exact'),
        ('PERCENT', 'Percent')
    ]

    payer = models.ForeignKey(User, related_name='payer_expenses', on_delete=models.CASCADE, default = 1)
    expenseId = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=SPLIT_TYPE_CHOICES)
    # participants = models.ManyToManyField(User, through='Participant')
    description = models.TextField(blank=True, null=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Expense {self.expenseId}"


class Participant(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    share = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('expense', 'user')

    def __str__(self):
        return f"{self.user.name} - {self.share}"

class Transaction(models.Model):
    fromUser = models.ForeignKey(User, related_name='transactions_sent', on_delete=models.CASCADE)
    toUser = models.ForeignKey(User, related_name='transactions_received', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fromUser.name} -> {self.toUser.name}: {self.amount}"
