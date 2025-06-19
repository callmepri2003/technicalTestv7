# transactions/models.py
from django.db import models
from django.conf import settings
from decimal import Decimal
from django.db.models import Sum # Import Sum for aggregation

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('ACTUAL', 'Actual Purchase'),
        ('ESTIMATED', 'Estimated Missed Purchase'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, default='ACTUAL')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    # Link to ShoppingList if this transaction originated from one
    shopping_list = models.OneToOneField(
        'shoppingList.ShoppingList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_transaction'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.transaction_type} Transaction by {self.user.username} on {self.transaction_date}"

    # NEW HELPER METHOD
    def _calculate_total_from_products(self):
        """Calculates the sum of total_price from all related TransactionProducts."""
        # Use annotate and Sum to efficiently get the sum from related items
        sum_result = self.products.aggregate(total_sum=Sum('total_price'))
        # Return 0.00 if there are no products or no total_price (e.g., all are None)
        return sum_result['total_sum'] if sum_result['total_sum'] is not None else Decimal('0.00')

    def save(self, *args, **kwargs):
        # Keep the save method as it was for normal operation,
        # relying on the serializer/view logic to call _calculate_total_from_products
        # and update total_amount when products are added/modified through the API.
        super().save(*args, **kwargs)

class TransactionProduct(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT) # PROTECT to prevent deleting product if it's in a transaction
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Transaction {self.transaction.id}"

    def save(self, *args, **kwargs):
        # Ensure total_price is calculated before saving TransactionProduct
        if self.unit_price is not None and self.quantity is not None:
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)