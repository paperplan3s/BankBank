from django.contrib import admin
from .models import User, Account, Transaction, Categorization

# Register your models here.

admin.site.register(User)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(Categorization)
