# shoppingList/services.py
import random
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from .models import ShoppingList, ShoppingListItem
from products.models import Product
from transactions.models import Transaction, TransactionProduct


class ShoppingListGenerator:
    def __init__(self, user):
        self.user = user
    
    def generate_lists(self, num_lists, start_date=None):
        """Generate shopping lists for the user"""
        if start_date is None:
            start_date = date.today() + timedelta(days=7)
        
        created_lists = []
        products = list(Product.objects.all()[:10])  # Get some sample products
        
        for i in range(num_lists):
            scheduled_date = start_date + timedelta(weeks=i)
            
            # Check if list already exists for this date
            existing_list = ShoppingList.objects.filter(
                user=self.user,
                scheduled_date=scheduled_date
            ).first()
            
            if existing_list:
                continue
            
            shopping_list = ShoppingList.objects.create(
                user=self.user,
                scheduled_date=scheduled_date,
                status='IN_PROGRESS'
            )
            
            # Add random items to the list
            num_items = random.randint(3, 8)
            selected_products = random.sample(products, min(num_items, len(products)))
            
            for product in selected_products:
                quantity = Decimal(str(random.uniform(1, 5))).quantize(Decimal('0.01'))
                price = Decimal(str(random.uniform(1, 20))).quantize(Decimal('0.01'))
                
                ShoppingListItem.objects.create(
                    shopping_list=shopping_list,
                    product=product,
                    predicted_quantity=quantity,
                    predicted_price=price
                )
            
            created_lists.append(shopping_list)
        
        return created_lists


class ShoppingListSimulator:
    def __init__(self, user):
        self.user = user
    
    def simulate(self, num_lists, start_date, completion_pattern=None):
        """Simulate shopping behavior"""
        if completion_pattern is None:
            completion_pattern = [random.choice([True, False]) for _ in range(num_lists)]
        
        # Generate lists using the generator
        generator = ShoppingListGenerator(self.user)
        lists = generator.generate_lists(num_lists, start_date)
        
        simulated_data = []
        completed_count = 0
        
        for i, shopping_list in enumerate(lists):
            will_complete = completion_pattern[i] if i < len(completion_pattern) else random.choice([True, False])
            
            if will_complete:
                # Simulate completion
                shopping_list.status = 'COMPLETED'
                shopping_list.completed_at = timezone.now()
                shopping_list.save()
                
                # Mark some items as purchased
                for item in shopping_list.items.all():
                    item.is_purchased = random.choice([True, False])
                    if item.is_purchased:
                        item.actual_quantity = item.predicted_quantity
                        item.unit_price = item.predicted_price
                    item.save()
                
                completed_count += 1
            else:
                # Mark as expired or keep pending
                shopping_list.status = random.choice(['EXPIRED', 'PENDING'])
                shopping_list.save()
            
            simulated_data.append({
                'id': shopping_list.id,
                'scheduled_date': str(shopping_list.scheduled_date),
                'status': shopping_list.status,
                'items': []  # Simplified for simulation
            })
        
        # Calculate final pending products
        pending_products = 0
        for shopping_list in lists:
            if shopping_list.status in ['PENDING', 'EXPIRED']:
                pending_products += shopping_list.items.filter(is_purchased=False).count()
        
        completion_rate = completed_count / len(lists) if lists else 0
        
        return {
            'simulated_lists': simulated_data,
            'final_pending_products': pending_products,
            'completion_rate': completion_rate
        }


class ShoppingListService:
    @staticmethod
    def complete_shopping_list(shopping_list, completion_data):
        """Complete a shopping list and create transaction"""
        if shopping_list.status not in ['TRIAGED', 'PENDING']:
            raise ValueError("Shopping list cannot be completed in current status")
        
        # Update shopping list
        shopping_list.status = 'COMPLETED'
        shopping_list.completed_at = timezone.now()
        shopping_list.save()
        
        # Update items
        item_updates = {item['item_id']: item for item in completion_data['items']}
        
        for item in shopping_list.items.all():
            if item.id in item_updates:
                update_data = item_updates[item.id]
                item.is_purchased = update_data['is_purchased']
                if 'actual_quantity' in update_data:
                    item.actual_quantity = update_data['actual_quantity']
                if 'unit_price' in update_data:
                    item.unit_price = update_data['unit_price']
                item.save()
        
        # Create transaction
        transaction = Transaction.objects.create(
            user=shopping_list.user,
            transaction_type='ACTUAL',
            transaction_date=date.today(),
            total_amount=completion_data.get('total_amount', Decimal('0.00')),
            shopping_list=shopping_list
        )

        
        # Add transaction products
        for item in shopping_list.items.filter(is_purchased=True):
            if item.actual_quantity and item.unit_price:
                TransactionProduct.objects.create(
                    transaction=transaction,
                    product=item.product,
                    quantity=item.actual_quantity,
                    unit_price=item.unit_price,
                    total_price=item.actual_total
                )
        
        return transaction
    
    @staticmethod
    def convert_expired_to_transaction(shopping_list):
        """Convert expired shopping list to estimated transaction"""
        if shopping_list.status != 'EXPIRED':
            raise ValueError("Only expired shopping lists can be converted")

        # Calculate total amount
        total_amount = sum(item.predicted_total for item in shopping_list.items.all() if item.predicted_price)

        # Create estimated transaction
        transaction = Transaction.objects.create(
            user=shopping_list.user,
            transaction_type='ESTIMATED',
            transaction_date=shopping_list.scheduled_date,
            total_amount=total_amount,
            shopping_list=shopping_list
        )

        # Add transaction products
        for item in shopping_list.items.all():
            if item.predicted_price:
                TransactionProduct.objects.create(
                    transaction=transaction,
                    product=item.product,
                    quantity=item.predicted_quantity,
                    unit_price=item.predicted_price
                )

        return transaction
