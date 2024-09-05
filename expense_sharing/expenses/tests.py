# Create your tests here.

from django.test import TestCase
from .models import User, Expense, Participant, Transaction

from rest_framework.test import APITestCase
from .serializers import UserSerializer
from django.urls import reverse

from django.core import mail
from django.utils import timezone
from celery import current_app

from expenses.tasks import send_weekly_summaries

import logging
logger = logging.getLogger(__name__)



class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            name="John Doe",
            email="john.doe@example.com",
            mobileNumber="1234567890"
        )
        logger.info("UserModelTests")
        print(self.user)
    def test_user_creation(self):
        self.assertEqual(self.user.name, "John Doe")
        self.assertEqual(self.user.email, "john.doe@example.com")

class ExpenseModelTests(TestCase):
    def setUp(self):
        self.payer = User.objects.create(
            name="John Doe",
            email="john.doe@example.com",
            mobileNumber="1234567890"
        )
        self.expense = Expense.objects.create(
            amount=100.00,
            type="EQUAL",
            description="Dinner",
        )
        self.participant = Participant.objects.create(
            expense=self.expense,
            user=self.payer,
            share=50.00
        )

    def test_expense_creation(self):
        self.assertEqual(self.expense.amount, 100.00)
        self.assertEqual(self.expense.type, "EQUAL")
        self.assertEqual(self.participant.share, 50.00)


class UserSerializerTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            name="John Doe",
            email="john.doe@example.com",
            mobileNumber="1234567890"
        )
        self.serializer = UserSerializer(instance=self.user)

    def test_user_serializer(self):
        data = self.serializer.data
        self.assertEqual(data['name'], "John Doe")
        self.assertEqual(data['email'], "john.doe@example.com")


class UserViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            name="John Doe",
            email="john.doe@example.com",
            mobileNumber="1234567890"
        )
        self.url = reverse('user-list')

    def test_get_users(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class ExpenseIntegrationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            name="John Doe",
            email="john.doe@example.com",
            mobileNumber="1234567890"
        )
        self.expense_data = {
            'amount': 100.00,
            'type': 'EQUAL',
            'description': 'Dinner',
            'payer':1,
            'shares':{'1':100.00}
        }

    def test_create_expense(self):
        response = self.client.post(reverse('expense-list'), self.expense_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['message'], 'Expense added or updated successfully')

# 4. Email Notifications Testing
class EmailTestCase(TestCase):
    def test_send_email(self):
        mail.send_mail(
            'Subject here',
            'Here is the message.',
            'from@example.com',
            ['dineshbansal.nitjsr@gmail.com]'],
            fail_silently=False,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Subject here')

# 5. Scheduled Jobs Testing
class ScheduledTaskTestCase(TestCase):
    def test_scheduled_task(self):
        # Trigger scheduled task manually
        result = current_app.tasks['expenses.tasks.send_weekly_summaries'].delay()
        self.assertEqual(type(result), 'celery.result.AsyncResult')
        print(type(result)) #<class 'celery.result.AsyncResult'>
        # self.assertEqual(result.status, 'SUCCESS')
