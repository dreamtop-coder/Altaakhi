from django import forms
from .models import Invoice
from invoices.models import Payment
from django.utils import timezone


# نموذج تعديل الفاتورة (حاليًا فقط المبلغ)
class EditInvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["amount", "created_at"]
        labels = {
            "amount": "المبلغ",
            "created_at": "تاريخ الإنشاء",
        }
        widgets = {
            "created_at": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }


class PaymentForm(forms.Form):
    payment_date = forms.DateField(
        label="تاريخ الدفع",
        initial=timezone.now,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    method = forms.ChoiceField(label="طريقة الدفع", choices=Payment.METHOD_CHOICES)
    reference = forms.CharField(
        label="رقم المرجع",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "يُملأ تلقائياً إذا بنفت"}),
    )
    notes = forms.CharField(
        label="ملاحظات",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        max_length=200,
    )
