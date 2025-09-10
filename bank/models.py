from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    pass

class Account(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="+")
    type = models.CharField(max_length=10, blank=True, null=True)
    balance = models.FloatField(default = 0.0)
    digits = models. CharField(max_length=4, default = '0000', blank=True, null=True)
    overdrawn = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} {self.type}"

    def serialize(self):
        return {
            "id": self.id,
            "user": self.user,
            "type": self.type,
            "balance": self.balance,
            "digits": self.digits,
            "overdrawn": self.overdrawn
        }

class Transaction(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    sendaccount = models.ForeignKey("Account", on_delete = models.PROTECT, related_name="+")
    receiveaccount = models.ForeignKey("Account", on_delete = models.PROTECT, related_name="+")
    amount = models.FloatField(default = 0.0)
    selftransaction = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.sendaccount}".title() + " to " + f"{self.receiveaccount}".title()

    def serialize(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "sendaccount": self.sendaccount,
            "receiveaccount": self.receiveaccount,
            "amount": self.amount,
        }

class Categorization(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="+")
    transaction = models.ForeignKey("Transaction", on_delete = models.CASCADE, related_name="transaction_category")
    category = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.category}"

    def serialize(self):
        return {
            "id": self.id,
            "user": self.user,
            "transaction": self.transaction,
            "category": self.category,
        }

