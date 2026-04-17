from django.contrib import admin
from .models import Expense, ExpenseCategory, RecurringExpense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
	list_display = ('name',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
	list_display = ('date', 'category', 'amount', 'payee')
	list_filter = ('category', 'date')
	search_fields = ('payee', 'note')


@admin.register(RecurringExpense)
class RecurringExpenseAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'amount', 'frequency', 'next_date', 'active')
	list_filter = ('category', 'frequency', 'active')
	search_fields = ('name', 'note')
	actions = ['create_now_action']

	def create_now_action(self, request, queryset):
		"""Admin action to create Expense rows now for selected recurring entries."""
		created = 0
		for r in queryset:
			try:
				r.create_expense(user=request.user)
				created += 1
			except Exception as e:
				self.message_user(request, f"Failed to create for {r}: {e}", level=40)
		self.message_user(request, f"Created {created} expense(s).")

	create_now_action.short_description = 'Create expense(s) now from selected RecurringExpense(s)'
