# shoppingList/models.py
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date

User = get_user_model()


class ShoppingList(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('TRIAGED', 'Triaged'),
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('EXPIRED', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_lists')
    scheduled_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Shopping List for {self.user.username} - {self.scheduled_date}"
    
    def can_be_deleted(self):
        """Check if shopping list can be deleted"""
        return self.status in ['IN_PROGRESS', 'TRIAGED', 'PENDING']
    
    def is_expired(self):
        """Check if shopping list is expired"""
        return self.scheduled_date < date.today() and self.status != 'COMPLETED'


class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    predicted_quantity = models.DecimalField(max_digits=10, decimal_places=3)
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_quantity = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_purchased = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['shopping_list', 'product']
        
    def __str__(self):
        return f"{self.product.name} x {self.predicted_quantity}"
    
    @property
    def predicted_total(self):
        """Calculate predicted total for this item"""
        if self.predicted_price:
            return self.predicted_quantity * self.predicted_price
        return Decimal('0.00')
    
    @property
    def actual_total(self):
        """Calculate actual total for this item"""
        if self.unit_price and self.actual_quantity:
            return self.actual_quantity * self.unit_price
        return Decimal('0.00')