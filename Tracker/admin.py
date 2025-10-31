from django.contrib import admin
from .models import Transaction,TransactionSubType, TransactionType, BankAccount, UserProvidedSymbol
# Register your models here.
admin.site.register([Transaction, TransactionType, TransactionSubType, BankAccount, UserProvidedSymbol])
