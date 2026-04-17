
from django import forms
from .models import Invoice
from invoices.models import Payment
from django.utils import timezone

# نموذج تعديل الفاتورة (حاليًا فقط المبلغ)
class EditInvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['amount', 'created_at']
        labels = {
            'amount': 'المبلغ',
            'created_at': 'تاريخ الإنشاء',
        }
        widgets = {
            'created_at': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class PaymentForm(forms.Form):
    payment_date = forms.DateField(label='Payment Date', initial=timezone.now, widget=forms.DateInput(attrs={'type': 'date'}))
    METHOD_CHOICES_EN = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('benefit', 'Benefit'),
        ('bank', 'Bank Transfer'),
        ('other', 'Other'),
    ]
    method = forms.ChoiceField(label='Payment Method', choices=METHOD_CHOICES_EN)
    reference = forms.CharField(label='Reference #', required=False, widget=forms.TextInput(attrs={'placeholder': "Auto-filled if method is 'benefit'"}))
    notes = forms.CharField(label='Notes', required=False, widget=forms.Textarea(attrs={'rows':2}), max_length=200)
    amount = forms.DecimalField(label='Amount', max_digits=12, decimal_places=3, required=False)


class ExpenseForm(forms.ModelForm):
    class Meta:
        from .models import Expense
        model = Expense
        fields = ['date', 'amount', 'category', 'payee', 'note', 'bill']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 3}),
            'amount': forms.NumberInput(attrs={'step': '0.001', 'inputmode': 'decimal'}),
        }


class RecurringExpenseForm(forms.ModelForm):
    class Meta:
        from .models import RecurringExpense
        model = RecurringExpense
        fields = ['name', 'amount', 'category', 'frequency', 'interval', 'start_date', 'next_date', 'end_date', 'active', 'note', 'reminder_only', 'is_flexible', 'auto_create', 'payee', 'payee_recipient', 'payee_month']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'next_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 3}),
            'payee': forms.TextInput(),
            'payee_recipient': forms.TextInput(),
            'payee_month': forms.TextInput(),
        }


class CompleteExpenseForm(forms.ModelForm):
    class Meta:
        from .models import Expense
        model = Expense
        fields = ['amount', 'payee', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
            'amount': forms.NumberInput(attrs={'step': '0.001', 'inputmode': 'decimal'}),
        }
