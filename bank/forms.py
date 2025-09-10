from django import forms

class Transaction_form(forms.Form):
    receiver = forms.CharField()
    amount = forms.FloatField(min_value = 0.0)

class Transfer_form(forms.Form):
    CHOICES = (('',''),('checking', 'Checking'),('savings', 'Savings'),)
    fromaccount = forms.ChoiceField(label="Move from", choices=CHOICES)
    TCHOICES = (('',''),('savings', 'Savings'),('checking', 'Checking'),)
    toaccount = forms.ChoiceField(label="To", choices=TCHOICES)
    amount = forms.FloatField(min_value = 0.0)

class Search_form(forms.Form):
    ACC_CHOICES = (('checking', 'Checking'),('savings', 'Savings'),)
    account = forms.ChoiceField(label="From my account",choices=ACC_CHOICES)
    P_CHOICES = (('week', 'Week'),('month', 'Month'),('quarter', 'Quarter'),('year', 'Year'))
    period = forms.ChoiceField(label="In the Past",choices=P_CHOICES)
    searchaccount = forms.CharField(label="Person or Business Name", required=False)
    C_CHOICES = (('',''),('Housing', 'Housing'),('Transport', 'Transport'),('Grocery', 'Grocery'), ('Utilities', 'Utilities'), ('Insurance', 'Insurance'), ('Medical', 'Medical'), ('Recreation', 'Recreation'), ('Miscellaneous', 'Miscellaneous')
, ('Income', 'Income'))
    searchcat = forms.ChoiceField(label="Category",choices=C_CHOICES, required=False)

class Period_form(forms.Form):
    P_CHOICES = (('Week', 'Week'), ('Month','Month'), ('Year', 'Year'))
    period = forms.ChoiceField(label="Period",choices=P_CHOICES)

class Month_form(forms.Form):
    M_CHOICES = (('current', 'This month'), ('last','Last Month'))
    period = forms.ChoiceField(label="Period",choices=M_CHOICES)
