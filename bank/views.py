from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import JsonResponse

import json
import datetime
import random


from .models import User, Account, Transaction, Categorization
from .forms import Transaction_form, Transfer_form, Search_form, Period_form, Month_form

# Create your views here.

#Initialize user's account, transaction, category data and the internal fund transfer form
def index(request):
    if request.user.is_authenticated:
        current = request.user
        savings = Account.objects.get(user=current.id, type = "Savings")
        checking = Account.objects.get(user=current.id, type = "Checking")

        #get latest 5 transactions, categorizations
        s_transactions, s_categories = get_transactions(savings,5)
        c_transactions, c_categories = get_transactions(checking,5)

        #get list of balances
        def get_balances(account, transactions):
            balance = account.serialize()["balance"]
            balances = [balance]
            for i in range(len(transactions)-1):
                amount = transactions[i].serialize()["amount"]
                if transactions[i].sendaccount == checking:
                    balance = balances[i] + amount
                    balances.append(balance)
                else:
                    balance = balances[i] - amount
                    balances.append(balance)
            return balances

        #get lists of balances to display in the table
        c_balance = get_balances(checking, c_transactions)
        s_balance = get_balances(savings, s_transactions)

        #Initialize internal transfer form
        form = Transfer_form
        return render(request,"bank/index.html", {"s_transactions": s_transactions, "c_transactions": c_transactions, "savings": savings, "checking": checking, "s_categories": s_categories, "c_categories": c_categories,"c_balances": c_balance, "s_balances": s_balance,"form": form, "message": "" })
    else:
        return render(request,"bank/index.html")

# Initialize a single account view with all the user's transactions and balances
@login_required
def account(request, name):

    #initialize account data
    current = request.user
    account = Account.objects.get(user=current.id, type = name)
    balance = account.balance
    transactions, categories = get_transactions(account,0)

    #get balances to display on table
    balances = [balance]
    for i in range(len(transactions)-1):
        amount = transactions[i].serialize()["amount"]
        if transactions[i].sendaccount == account:
            balance = balances[i] + amount
            balances.append(balance)
        else:
            balance = balances[i] - amount
            balances.append(balance)
    return render(request,"bank/account.html", {"transactions": transactions,   "categories": categories, "account": account, "balances": balances, "message": "" })

# Get transaction and category information for an account, with the option to limit results
@login_required
def get_transactions(account, limit):
    id = account.id
    if limit > 0:
        transactions = Transaction.objects.filter(Q(sendaccount =id) | Q(receiveaccount =id)).order_by("-timestamp")[:limit]
    else:
        transactions = Transaction.objects.filter(Q(sendaccount =id) | Q(receiveaccount =id)).order_by("-timestamp")
    transaction_ids = transactions.values("id")
    categs = {}

    for i in range(len(transactions)):
        t = transaction_ids[i]
        cat = Categorization.objects.filter(user = id, transaction= t["id"])
        if len(cat) == 1:
            category = cat.values("category")
            categs[i] = category[0]["category"]
        else:
            categs[i] = None
    return transactions, categs



# Get category totals for all transactions in the desired time period and return them in the necessary JSON format
@csrf_exempt
def chart_data(request, period):
    if request.method == "GET":
        current = request.user
        account = Account.objects.get(user=current.id, type = "Checking")
        transactions = Transaction.objects.filter(sendaccount =account)
        now = datetime.datetime.now()

        #Filter transactions
        if period == 'Week':
            current_week = now.strftime("%V")
            transactions =transactions.filter(timestamp__week=current_week)
        elif period == 'Month':
            current_month = now.month
            transactions = transactions.filter(timestamp__month=current_month)
        elif period == 'Year':
            current_year = now.year
            transactions =transactions.filter(timestamp__year=current_year)

        # Calculate totals for each category, add unclassified amounts to their respective categories
        category_totals = {}
        transaction_ids = transactions.values("id")
        balance = 0
        categories_list =["Category"]
        for i in range(len(transactions)):
            t = transaction_ids[i]
            balance += transactions[i].amount
            cat = Categorization.objects.filter(user=current.id, transaction=t["id"])
            if len(cat) == 1:
                cat = cat[0].category
                if cat not in categories_list:
                    categories_list.append(cat)
                    category_totals[cat] = transactions[i].amount
                else:
                    category_totals[cat] += transactions[i].amount
            elif len(cat) == 0:
                if "Unclassified" not in categories_list:
                    cat = "Unclassified"
                    categories_list.append(cat)
                    category_totals["Unclassified"] = transactions[i].amount
                else:
                    category_totals["Unclassified"] += transactions[i].amount

        datalist =[]
        for item in category_totals.items():
            item = list(item)
            datalist.append(item)
        return JsonResponse(datalist, safe=False)

#Initialize page with Spending Breakdown chart and supply the period form
def spending(request):
    form = Period_form
    return render(request,"bank/spending.html", {"form": form})


# Get category totals for all transactions in the desired time period as a percentage of that months paycheck and return them in the necessary JSON format
@csrf_exempt
def paycheck_data(request, month):
   if request.method == "GET":

        #Initialize account data, get relevant transactions and find users paycheck for the selected period
        current = request.user
        account = Account.objects.get(user=current.id, type = "Checking")
        transactions = Transaction.objects.filter(sendaccount =account)
        now = datetime.datetime.now()
        if month == "current":
            month = now.month
        else:
            month = now.month - 1
        transactions = transactions.filter(timestamp__month=month)
        month = transactions[0].timestamp
        income = Categorization.objects.filter(user = current, category="Income")
        if len(income) < 1:
            datalist =[]
            return JsonResponse(datalist, safe=False)

        elif len(income) >= 1:
            for i in range(len(income)):
                income_id = income[0].transaction.id
                paycheck = Transaction.objects.get(id = income_id)
                if paycheck.timestamp.month == month:
                    paycheck = paycheck.amount
                else:
                    pass

        # Calculate totals for each category, add unclassified amounts and the unspent remainder to their respective categories
        category_totals = {}
        transaction_ids = transactions.values("id")
        balance = 0
        categories_list =["Category"]

        for i in range(len(transactions)):
            t = transaction_ids[i]
            balance += transactions[i].amount
            cat = Categorization.objects.filter(user=current.id, transaction=t["id"])

            if len(cat) == 1:
                cat = cat[0].category
                if cat == 'Income':
                    pass
                if cat not in categories_list:
                    categories_list.append(cat)
                    category_totals[cat] = transactions[i].amount
                else:
                    category_totals[cat] += transactions[i].amount
            elif len(cat) == 0:
                if "Unclassified" not in categories_list:
                    cat = "Unclassified"
                    categories_list.append(cat)
                    category_totals["Unclassified"] = transactions[i].amount
                else:
                    category_totals["Unclassified"] += transactions[i].amount

        #Format the data into the correct JSON format to submit to the Google Charts API
        datalist = ["Category"]
        values = []
        for key, value in category_totals.items():
            datalist.append(key)
            values.append(value)
        datalist.append("Remaining Balance")
        datalist.append({"role": 'annotation'})
        total = paycheck.amount
        month_name = month.strftime('%B') + ", " + str(now.year)
        valuelist = [month_name]

        for i in range(len(values)):
            val = values[i]
            total -= val
            val = {'v': val, 'f': "${:.2f}".format(val)}
            valuelist.append(val)

        if total > 0:
            total = {'v': total, 'f': "${:.2f}".format(total)}
            valuelist.append(total)
        else:
            total = 0
            total = {'v': total, 'f': "${:.2f}".format(total)}
            valuelist.append(total)
        valuelist.append('')
        datalist = [datalist]
        datalist.append(valuelist)
        return JsonResponse(datalist, safe=False)


#Initialize Paycheck Breakdown page and form
@login_required
def paycheck(request):
    form = Month_form
    return render(request, "bank/paycheck.html",{"form": form})



# Filter transactions by with parameters supplied by the Search function
def filter(transactions, data, user, account):

    #filter by date
    now = datetime.datetime.now()
    if data["period"] == "month":
        current_month = now.month
        transactions = transactions.filter(timestamp__month=current_month)
        print(transactions)
    elif data["period"] == "quarter":
        current_q = now.month//3+1
        transactions = transactions.filter(timestamp__quarter=current_q)
    elif data["period"] == "week":
        current_week = now.strftime("%V")
        transactions =transactions.filter(timestamp__week=current_week)
    elif data["period"] == "year":
        current_year = now.year
        transactions =transactions.filter(timestamp__year=current_year)

    #if an account name has been specified, search for transactions that match, if none then return and empty list
    if data["searchaccount"] != '':
        account_user = User.objects.filter(Q(username__iexact= data["searchaccount"]) | Q(username__icontains= data["searchaccount"]))
        if len(account_user) > 0:
            account_user = Account.objects.get(user=account_user[0], type = "Checking")
            transactions = Transaction.objects.filter(Q(sendaccount=account_user, receiveaccount= account) | Q(sendaccount=account, receiveaccount= account_user))
        else:
            return []

    #if a category has been specified, search for transactions that match the users categorizations of that kind, if none then return and empty list
    if data["searchcat"] != '':
        categories = Categorization.objects.filter(user=user, category= data["searchcat"] )
        if len(categories) == 1:
            id = categories[0].transaction.id
            transactions = Transaction.objects.filter(id=id)
        elif len(categories) > 1:
            ids = categories.values_list("transaction", flat=True)
            transactions = transactions.filter(id__in=ids)
        elif len(categories) <1:
            return []
    return transactions


# allow the user to search their own transactions and then display the results
@login_required
def search(request):
    if request.method == "POST":
        form = Search_form(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            current = request.user

            #get the desired account and its transactions and then filter them with the desired parameters, then gather their categories to display as search results
            if data["account"] == "checking":
                account = Account.objects.get(user=current.id, type = "Checking")
            else:
                account = Account.objects.get(user=current.id, type = "Savings")
            transactions = Transaction.objects.filter(Q(sendaccount =account) | Q(receiveaccount =account)).order_by("-timestamp")
            transactions = filter(transactions, data, current, account)
            if len(transactions) > 0:
                transaction_ids = transactions.values("id")
                categs = {}
                for i in range(len(transactions)):
                    t = transaction_ids[i]
                    cat = Categorization.objects.filter(user=current.id, transaction=t["id"])
                    if len(cat) == 1:
                        category = cat.values("category")
                        categs[i] = category[0]["category"]
                    else:
                        categs[i] = None
                return render(request,"bank/search.html", {"transactions": transactions,  "categories": categs, "form": form})

            else:
                return render(request,"bank/search.html", {"form": form, "message": "No transactions met your search criteria."})
    else:

        #Initialize the form to perform a Search
        form = Search_form
        return render(request,"bank/search.html", {"form": form})

#Perform a transfer between users
@login_required
def ex_transfer(request):
    if request.method == "POST":
        form = Transaction_form(request.POST)
        if form.is_valid():

            #Initialize the details of the transfer
            current = request.user
            users_account = Account.objects.get(user=current.id, type = "Checking")
            balance = users_account.serialize()["balance"]
            transfer_amount = form.cleaned_data["amount"]

            #Check the user has enough balance to transfer out, if not, return an error message
            if transfer_amount > balance and transfer_amount <= 0:
                return render(request, "bank/transfer.html", {"form": form, "message" :"Insufficient funds/Invalid amount."})
            receiver = form.cleaned_data["receiver"]

            #Check the Receiver exists in the database, if not, return an error message
            rcvr_user = User.objects.filter(username__iexact = receiver)
            if len(rcvr_user) == 1:
                rcvr_user = rcvr_user[0]
            else:
                return render(request,"bank/error.html", {"message": "User not found, please try again."})

            #Ensure the user has a current checking account to receive the funds, if not, return an error
            try:
                rcvrs_account = Account.objects.get(user=rcvr_user, type = "Checking")
            except:
                return render(request, "bank/transfer.html", {"form": form, "message" :"Account not found."})

            #Perform the transaction, initialize the objects values and adjust each user's balance
            transfer = Transaction(
                    sendaccount = users_account,
                    receiveaccount = rcvrs_account,
                    amount = transfer_amount
                )
            transfer.save()
            users_account.balance -= transfer_amount
            users_account.save(update_fields=["balance"])
            rcvrs_account.balance += transfer_amount
            rcvrs_account.save(update_fields=["balance"])
            return HttpResponseRedirect(reverse("index"))

    else:

        #Initialize the form
        form = Transaction_form
        return render(request, "bank/transfer.html", {"form": form, "message": ""})

#Let the user transfer funds between their Savings and Checking accounts
@login_required
def internal_transfer(request):
    if request.method == "POST":
        current = request.user
        form = Transfer_form(request.POST)
        if form.is_valid():

            #Check the user has selected two differing accounts
            if form.cleaned_data["toaccount"] == form.cleaned_data["fromaccount"]:
                return render(request, "bank/index.html", {"form": form,
                "message": "Please select two different accounts."
            })

            #Initliaze transfer details
            if form.cleaned_data["toaccount"]== "checking" :
                outgoing = "Savings"
                incoming = "Checking"
            elif form.cleaned_data["toaccount"] == "savings":
                outgoing = "Checking"
                incoming = "Savings"
            from_acc = Account.objects.get(user=current.id, type=outgoing)
            to_acc = Account.objects.get(user=current.id, type=incoming)
            amount = float(form.cleaned_data["amount"])

            #Check there are sufficient funds to perform the transfer, then create the Transaction object and adjust the balances
            if from_acc.serialize()["balance"] >= amount and from_acc.serialize()["balance"] > 0:
                from_acc.balance -= amount
                from_acc.save(update_fields=["balance"])
                to_acc.balance += amount
                to_acc.save(update_fields=["balance"])
                transfer = Transaction(
                            sendaccount = from_acc,
                            receiveaccount = to_acc,
                            amount = amount,
                            selftransaction = True
                        )
                transfer.save()
                return HttpResponseRedirect(reverse("index"))
            else:

                #If there are insufficient funds, return an error message
                return render(request,"bank/error.html", {"message": "Insufficient funds, please try again."})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "bank/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "bank/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "bank/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user and default accounts
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
            digit1 = random.randint(1000,9999)
            new_checking = Account(
                user= user,
                type = "Checking",
                digits = digit1,
            )
            new_checking.save()
            digit2 = random.randint(1000,9999)
            new_savings = Account(
                user= user,
                type = "Savings",
                digits = digit2
            )
            new_savings.save()
        except IntegrityError:
            return render(request, "bank/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "bank/register.html")

#Allow the user to create a category for their Checking account transactions and access previous categorizations
@csrf_exempt
@login_required
def categorize(request):
    if request.method == "PUT":

        #Initialize the Category data, check the transaction in question exists
        data = json.loads(request.body)
        id = data["transaction"]
        category = data["category"]
        try:
            transaction = Transaction.objects.get(pk = id)
        except:
            return "No such transaction"

        #Check for previous categorizations and return them as dictionaries
        categ = Categorization.objects.filter(user=request.user, transaction = transaction)
        if len(categ) ==1 :
            categ = categ[0]
            categ.category = category
            categ.save(update_fields=["category"])
            return JsonResponse(model_to_dict(categ))

        # Else create a new Category object and return its details as dictionary
        else:
            new_categ = Categorization(
                user= request.user,
                transaction = transaction,
                category = category
            )
            new_categ.save()
        return JsonResponse(model_to_dict(new_categ))

    # Call must be via GET or PUT and not POST
    else:
        return JsonResponse({
            "error": "GET or PUT request required."
        }, status=400)

#Initialize Savings tracker page and form
@login_required
def savings(request):
    form = Period_form
    return render(request, "bank/savings.html", {"form": form})


#Get data on deposits and withdrawals made to users Saving account by desired period
@login_required
def savings_data(request, period):

    #Initialize user and account details
    current = request.user
    savings = Account.objects.get(user=current.id, type = "Savings")
    transactions = Transaction.objects.filter(Q(sendaccount =savings) | Q(receiveaccount = savings))
    now = datetime.datetime.now()

    #filter by search period
    if period == 'Week':
        current_week = now.strftime("%V")
        transactions =transactions.filter(timestamp__week=current_week)
    elif period == 'Month':
        current_month = now.month
        transactions = transactions.filter(timestamp__month=current_month)
    elif period == 'Year':
        current_year = now.year
        transactions =transactions.filter(timestamp__year=current_year)
    if len(transactions) < 1:
        today = now.strftime("%x")
        balances = [['Date', 'Balance'],[today, 0]]
        return JsonResponse(balances, safe=False)


    #Initialize JSON data and loop through results, if multiple transactions on one day, aggregate these
    balance = 0
    balances = [['Date', 'Balance']]
    if len(transactions) == 1:
        balances = [['Date', 'Balance'], [str(transactions[0].serialize()["timestamp"].strftime("%x")), savings.balance]]
        return JsonResponse(balances, safe=False)
    for i in range(len(transactions)):
        print(transactions[i].amount)
        amount = transactions[i].serialize()["amount"]
        date = str(transactions[i].serialize()["timestamp"].strftime("%x"))
        if transactions[i].sendaccount != savings:
            balance += amount
        else:
            balance = (0 - amount)
        sublist = [date, balance]
        repeat = any(date in sublist for sublist in balances)
        if repeat:
            for i in range(len(balances)):
                if date == balances[i][0]:
                    balances[i][1] = balances[i][1] + amount
        else:
            balances.append(sublist)
    return JsonResponse(balances, safe=False)
