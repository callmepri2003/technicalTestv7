# shoppingList/admin.py
from django.contrib import admin
from .models import ShoppingList, ShoppingListItem


class ShoppingListItemInline(admin.TabularInline):
    model = ShoppingListItem
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = [
        'product', 'predicted_quantity', 'predicted_price',
        'actual_quantity', 'unit_price', 'is_purchased'
    ]


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'scheduled_date', 'status', 
        'item_count', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'scheduled_date', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    inlines = [ShoppingListItemInline]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'scheduled_date', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')


@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'shopping_list', 'product', 'predicted_quantity',
        'predicted_price', 'is_purchased', 'created_at'
    ]
    list_filter = ['is_purchased', 'shopping_list__status', 'product__category', 'created_at']
    search_fields = ['product__name', 'shopping_list__user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('shopping_list', 'product')
        }),
        ('Predicted Values', {
            'fields': ('predicted_quantity', 'predicted_price')
        }),
        ('Actual Values', {
            'fields': ('actual_quantity', 'unit_price', 'is_purchased')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'shopping_list', 'shopping_list__user', 'product'
        )