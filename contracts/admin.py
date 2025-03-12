from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Contract, Unit, Notification
from django.utils.timezone import now
from datetime import timedelta


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'unit',  'role',)
    list_filter = ('unit',)
    search_fields = ('username', 'email')
    

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    
@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'unit', 'start_date', 'end_date', 'created_at')
    list_filter = ('unit', 'end_date')
    search_fields = ('title', 'unit__name')
    
    def contract_status(self, obj):
        today = now().date()
        if obj.end_date < today:
            return "Expired"
        elif obj.end_date <= today + timedelta(days=30):
            return "Expiring soon"
        else:
            return "Active"
    contract_status.short_description = "Status"
    contract_status.admin_order_field = 'end_date'

    actions = ['renew_contract']

    def renew_contract(self, request, queryset):
        for contract in queryset:
            contract.end_date += timedelta(days=365)
            contract.renewal_count += 1
            contract.save()
            self.message_user(request, "Selected contracts have been renewed.")
            
    renew_contract.short_description = "Renew selected contracts by 1 year"
            


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract', 'sent_at', 'recipient_email')
    search_fields = ('contract__title',)
    
    