from django.contrib import admin
from .models import User, Expense, Participant, Transaction

admin.site.register(User)
admin.site.register(Expense)
admin.site.register(Participant)
admin.site.register(Transaction)


# Register your models here.
