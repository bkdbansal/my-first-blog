# **Expense Sharing Application**

## **Overview**
        The Expense Sharing Application is built using the Django framework and provides functionality for users to share 
        expenses, split payments, track balances, and simplify debts. This application supports different types of expense 
        splits, asynchronous email notifications, and scheduled tasks for sending weekly balance summaries.

## **Architecture Components:**
      •	Django Backend: Handles HTTP requests, expense logic, and database interaction.
      •	Celery & Redis: Manages asynchronous tasks for sending emails and running scheduled jobs.
      •	Database (PostgreSQL/MySQL): Stores user, expense, split, and balance data.
      •	Email Service: Sends notifications to users about expenses and balance summaries.
________________________________________
## **System Design**

### **Class Structure**
#### 1.	User
        o	Represents a user in the system.
        o	Attributes: userId, name, email, mobileNumber.
##### class User(models.Model):
          userId = models.AutoField(primary_key=True)
          name = models.CharField(max_length=255)
          email = models.EmailField(unique=True)
          mobileNumber = models.CharField(max_length=20, unique=True)
  	
#### 3.	Expense
      o	Represents an expense created by a user (payer).
      o	Attributes: expenseId, payer, amount, type (Equal, Exact, Percent), description, createdAt.
 #####  class Expense(models.Model):
            payer = models.ForeignKey(User, on_delete=models.CASCADE)
            expenseId = models.AutoField(primary_key=True)
            amount = models.DecimalField(max_digits=12, decimal_places=2)
            type = models.CharField(max_length=10, choices=SPLIT_TYPE_CHOICES)
            description = models.TextField(blank=True, null=True)
            createdAt = models.DateTimeField(auto_now_add=True)
  	
#### 4.	Participant
    o	Tracks each participant's share in an expense.
##### class Participant(models.Model):
        expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        share = models.DecimalField(max_digits=12, decimal_places=2)
  
  	
#### 7.	Transaction
          o	Represents a transaction between two users, indicating who owes whom and how much.
          o	Attributes: fromUser, toUser, amount, createdAt.
##### class Transaction(models.Model):
          fromUser = models.ForeignKey(User, on_delete=models.CASCADE)
          toUser = models.ForeignKey(User, on_delete=models.CASCADE)
          amount = models.DecimalField(max_digits=12, decimal_places=2)
          createdAt = models.DateTimeField(auto_now_add=True)
    
________________________________________
## **Database Schema**
              The following is the SQL schema corresponding to the models:
##### CREATE TABLE users (
        userId SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        mobileNumber VARCHAR(20) UNIQUE NOT NULL
    );

##### CREATE TABLE expenses (
            expenseId SERIAL PRIMARY KEY,
            payer_id INT NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            type VARCHAR(10) NOT NULL CHECK (type IN ('EQUAL', 'EXACT', 'PERCENT')),
            description TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (payer_id) REFERENCES users(userId)
        );

###### CREATE TABLE participants (
            id SERIAL PRIMARY KEY,
            expense_id INT NOT NULL,
            user_id INT NOT NULL,
            share DECIMAL(12,2) NOT NULL,
            UNIQUE (expense_id, user_id),
            FOREIGN KEY (expense_id) REFERENCES expenses(expenseId),
            FOREIGN KEY (user_id) REFERENCES users(userId)
        );

##### CREATE TABLE transactions (
            id SERIAL PRIMARY KEY,
            fromUser_id INT NOT NULL,
            toUser_id INT NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fromUser_id) REFERENCES users(userId),
            FOREIGN KEY (toUser_id) REFERENCES users(userId)
        );
________________________________________
## API Contracts
### 1. User Management
#### •	POST /api/users/
              Create a new user.
#####    Request:
          {
              "name": "John Doe",
              "email": "john@example.com",
              "mobileNumber": "1234567890"
          }
#####    Response:
          {
              "userId": 1,
              "name": "John Doe",
              "email": "john@example.com",
              "mobileNumber": "1234567890"
          }
          
#### •	GET /api/users/{userId}/
            Retrieve a user's details by their ID.
##### Response:{
              "userId": 1,
              "name": "John Doe",
              "email": "john@example.com",
              "mobileNumber": "1234567890"
          }
          
## 2. Expense Management
### •	POST /api/expenses/
        Create a new expense and split it among participants.
#### Request:{
              "payer": 1,
              "amount": 1000,
              "type": "EQUAL",
              "shares": [
                  {"userId":  "share"},
                  {"userId":  "share"},
                  {"userId":  "share"}
              ],
              "description": "Dinner with friends"
          }
##### Response:
            {
                "expenseId": 1,
                "payer": 1,
                "amount": 1000,
                "type": "EQUAL",
                "description": "Dinner with friends",
                "createdAt": "2023-09-05T14:48:00Z"
            }
### •	GET /api/expenses/{userId}/
          Retrieve all expenses for a user.
####    Response:[
              {
                  "expenseId": 1,
                  "payer": 1,
                  "amount": 1000,
                  "type": "EQUAL",
                  "description": "Dinner with friends",
                  "createdAt": "2023-09-05T14:48:00Z"
              }
          ]
          
## 3. Transaction Management
 ### •	GET /api/transactions/{userId}/
                Retrieve non-zero transactions for a user.
####     Response:[
                    {
                        "fromUser": 1,
                        "toUser": 2,
                        "amount": 250
                    },
                    {
                        "fromUser": 1,
                        "toUser": 3,
                        "amount": 150
                    }
                ]

### •	GET users/<int:user_id>/expenses/
              o	Shows the expense for user.
### •	GET users/<int:user_id>/balances/
        o	Shows the Balance for users
### •	GET /api/ balances /simplify/
          Simplify transactions among users.
####    Request:{
              "userId": 1
          }
#### Response:
        [
          	  " User2 owes User1 : 1060.00",
            " User3 owes User1 : 2770.00",
           		 " User4 owes User1 : 1090.03"
        ]
________________________________________
### Simplification Logic
    •	The "simplify transactions" functionality reduces the number of transactions by resolving intermediate debts between users. For example, if User1 owes User2 $250 and User2 owes User3 $200, the system will simplify the transactions to:
    o	User1 owes User2 $50
    o	User1 owes User3 $200
________________________________________
### Scheduled Jobs and Email Notifications
#### Weekly Balance Reminder Emails
          •	The application sends weekly reminder emails to users, summarizing their outstanding balances. This is achieved 
        using Celery Beat, which schedules the job to run weekly.
#### Expense Notification Emails
          •	Asynchronously sends an email notification to each participant whenever a new expense is created. Celery               tasks are used to ensure that the notification process does not block the API response.
________________________________________
## Running Tests
To run the test suite for the application:
python manage.py test
Ensure that the test coverage includes:
•	Expense creation and validation (equal, exact, percentage)
•	Transaction calculation and simplification
•	Email notification logic
•	Scheduled tasks
