from datetime import timedelta, timezone
from celery import shared_task
from django.core.mail import send_mail
from celery.schedules import crontab
from django.conf import settings
from .models import Transaction, User

import logging
logger = logging.getLogger(__name__)

@shared_task
def test():
    try:
        logger.info('Test task started.')
        print("Test task is working")
        logger.info('Test task completed.')
    except Exception as e:
        logger.error(f'Test task failed: {e}')
        raise

@shared_task
def send_expense_email_task(user_id, expense_id, share, sender_id):
    # user_email = get_user_email(user_id)
    user = User.objects.get(userId=user_id)
    expense_details = f"Expense ID: {expense_id}, Share: {share}, Paid By: {sender_id}"
    
    try:
        send_mail(
            subject='New Expense Added',
            message=expense_details,
            from_email='your_email@example.com',
            recipient_list=[user.email],
        )
        logger.info(f"Email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")



@shared_task
def send_weekly_summaries():
        # Get the date one week ago
    one_week_ago = timezone.now() - timedelta(weeks=1)
    
    # Get all transactions from the past week
    transactions = Transaction.objects.filter(createdAt__gte=one_week_ago)
    
    # Create a dictionary to store the balance for each user
    user_balances = {}

    logger.info("Calculate the total balance for each user")
    for transaction in transactions:
        from_user = transaction.fromUser
        to_user = transaction.toUser
        amount = transaction.amount

        if from_user not in user_balances:
            user_balances[from_user] = {}
        if to_user not in user_balances:
            user_balances[to_user] = {}

        logger.info("Deduct the amount from the sender's balance")
        if to_user in user_balances[from_user]:
            user_balances[from_user][to_user] -= amount
        else:
            user_balances[from_user][to_user] = -amount

        logger.info("Add the amount to the receiver's balance")
        if from_user in user_balances[to_user]:
            user_balances[to_user][from_user] += amount
        else:
            user_balances[to_user][from_user] = amount

    logger.info("Send summary emails to users")
    for user, balances in user_balances.items():
        summary = []
        for other_user, balance in balances.items():
            if balance != 0:
                summary.append(f'{other_user.name}: {balance:.2f}')

        logger.info("Create the email body")
        email_body = "Weekly Summary of Your Transactions:\n\n"
        if summary:
            email_body += "\n".join(summary)
        else:
            email_body = "No transactions this week."

        logger.info("Send email")
        send_mail(
            'Weekly Transaction Summary',
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )