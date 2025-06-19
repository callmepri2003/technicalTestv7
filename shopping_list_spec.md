# Shopping List Prediction System - Complete Technical Specification

## Overview
A Django REST Framework system that predicts future shopping lists based on historical purchase patterns, handles missed shopping scenarios, and manages shopping list lifecycle states. The system uses token-based authentication and provides RESTful endpoints for mobile/web clients.

## Data Models

### User Profile Extension
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_shopping_day = models.IntegerField(choices=WEEKDAY_CHOICES, default=1)  # 0=Monday, 6=Sunday
    preferred_shopping_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='WEEKLY')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

FREQUENCY_CHOICES = [
    ('WEEKLY', 'Weekly - 7 days'),
    ('FORTNIGHTLY', 'Fortnightly - 14 days'), 
    ('MONTHLY', 'Monthly - 30 days'),
    ('CUSTOM', 'Custom interval')
]

WEEKDAY_CHOICES = [(i, day) for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])]
```

### Product
```python
class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=100, blank=True)
    default_unit = models.CharField(max_length=20, default='item')  # item, kg, litre, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
```

### Transaction
```python
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('ACTUAL', 'Actual Purchase'),
        ('ESTIMATED', 'Estimated/Missed Purchase')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='ACTUAL')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['user', 'transaction_date']),
            models.Index(fields=['user', 'transaction_type'])
        ]
```

### TransactionProduct
```python
class TransactionProduct(models.Model):
    transaction = models.ForeignKey(Transaction, related_name='products', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['transaction', 'product']
```

### ShoppingList
```python
class ShoppingList(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress - Being Built'),
        ('TRIAGED', 'Triaged - Ready for Shopping'),
        ('PENDING', 'Pending - Scheduled Date Active'),
        ('COMPLETED', 'Completed - Shopping Done'),
        ('EXPIRED', 'Expired - Missed Shopping Date')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scheduled_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'scheduled_date']
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'scheduled_date'])
        ]
```

### ShoppingListItem
```python
class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    predicted_quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    actual_quantity = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_purchased = models.BooleanField(default=False)
    predicted_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['shopping_list', 'product']
```

### ProductFrequency (Computed Model)
```python
class ProductFrequency(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    average_interval_days = models.IntegerField()  # Days between purchases
    frequency_category = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    last_purchase_date = models.DateField()
    total_purchases = models.IntegerField()
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2)  # 0.00-1.00
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'product']
```

## Business Rules & Algorithms

### Frequency Calculation Algorithm
```python
def calculate_product_frequency(user, product):
    """
    Calculate purchase frequency for a specific product for a user
    Only considers ACTUAL transactions, not ESTIMATED ones
    """
    transactions = Transaction.objects.filter(
        user=user,
        transaction_type='ACTUAL',
        products__product=product
    ).order_by('transaction_date')
    
    if transactions.count() < 2:
        return None  # Insufficient data
    
    # Get unique purchase dates (handle multiple purchases same day)
    purchase_dates = list(transactions.values_list('transaction_date', flat=True).distinct())
    
    if len(purchase_dates) < 2:
        return None
    
    # Calculate intervals between purchases
    intervals = []
    for i in range(1, len(purchase_dates)):
        interval = (purchase_dates[i] - purchase_dates[i-1]).days
        intervals.append(interval)
    
    # Calculate average interval
    average_interval = sum(intervals) / len(intervals)
    
    # Determine frequency category
    if average_interval <= 10:
        category = 'WEEKLY'
    elif average_interval <= 21:
        category = 'FORTNIGHTLY'
    elif average_interval <= 45:
        category = 'MONTHLY'
    else:
        category = 'CUSTOM'
    
    # Calculate confidence score based on consistency
    if len(intervals) >= 3:
        variance = sum((x - average_interval) ** 2 for x in intervals) / len(intervals)
        confidence = max(0.1, 1.0 - (variance / (average_interval ** 2)))
    else:
        confidence = 0.5  # Medium confidence for limited data
    
    return {
        'average_interval_days': int(average_interval),
        'frequency_category': category,
        'last_purchase_date': purchase_dates[-1],
        'total_purchases': len(purchase_dates),
        'confidence_score': round(confidence, 2)
    }
```

### Shopping List Status Management
```python
class ShoppingListStatusManager:
    """
    Manages shopping list status transitions and business rules
    """
    
    @staticmethod
    def get_or_create_triaged_list(user):
        """
        Ensures only one TRIAGED list exists at a time
        Returns the current triaged list or creates one
        """
        # Check for existing triaged list
        triaged_list = ShoppingList.objects.filter(
            user=user, 
            status='TRIAGED'
        ).first()
        
        if triaged_list:
            return triaged_list
        
        # Get the earliest IN_PROGRESS list to promote
        next_list = ShoppingList.objects.filter(
            user=user,
            status='IN_PROGRESS',
            scheduled_date__gte=timezone.now().date()
        ).order_by('scheduled_date').first()
        
        if next_list:
            next_list.status = 'TRIAGED'
            next_list.save()
            return next_list
        
        return None
    
    @staticmethod
    def expire_overdue_lists(user):
        """
        Mark lists as EXPIRED if their scheduled date has passed
        """
        overdue_lists = ShoppingList.objects.filter(
            user=user,
            scheduled_date__lt=timezone.now().date(),
            status__in=['TRIAGED', 'PENDING']
        )
        
        expired_lists = []
        for shopping_list in overdue_lists:
            shopping_list.status = 'EXPIRED'
            shopping_list.save()
            expired_lists.append(shopping_list)
        
        return expired_lists
    
    @staticmethod
    def complete_shopping_list(shopping_list):
        """
        Mark a shopping list as completed
        """
        shopping_list.status = 'COMPLETED'
        shopping_list.completed_at = timezone.now()
        shopping_list.save()
        
        # Promote next list to TRIAGED
        ShoppingListStatusManager.get_or_create_triaged_list(shopping_list.user)
```

## API Endpoints & Core Functions

### 1. Generate Predicted Shopping Lists
**Endpoint**: `POST /api/shopping-lists/generate/`

```python
class GeneratePredictedShoppingListsView(APIView):
    """
    Generate multiple future shopping lists based on transaction history
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = GenerateListsSerializer(data=request.data)
        if serializer.is_valid():
            # Get parameters
            num_lists = serializer.validated_data.get('num_lists', 4)
            start_date = serializer.validated_data.get('start_date', None)
            
            # Generate lists
            result = self.generate_predicted_lists(
                user=request.user,
                num_lists=num_lists,
                start_date=start_date
            )
            
            return Response(result, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def generate_predicted_lists(self, user, num_lists, start_date=None):
        """
        Core business logic for generating shopping lists
        """
        # Get user preferences
        profile = UserProfile.objects.get(user=user)
        
        # Calculate start date if not provided
        if not start_date:
            start_date = self.get_next_shopping_date(user)
        
        # Get or refresh product frequencies
        self.refresh_product_frequencies(user)
        
        # Get products that should be predicted
        frequencies = ProductFrequency.objects.filter(
            user=user,
            confidence_score__gte=0.3  # Only predict products with reasonable confidence
        )
        
        created_lists = []
        current_date = start_date
        
        for i in range(num_lists):
            # Create shopping list
            shopping_list, created = ShoppingList.objects.get_or_create(
                user=user,
                scheduled_date=current_date,
                defaults={'status': 'IN_PROGRESS'}
            )
            
            if created:
                # Add predicted products
                for freq in frequencies:
                    if self.should_include_product(freq, current_date):
                        ShoppingListItem.objects.create(
                            shopping_list=shopping_list,
                            product=freq.product,
                            predicted_quantity=self.calculate_predicted_quantity(freq),
                            predicted_price=self.calculate_predicted_price(user, freq.product)
                        )
                
                created_lists.append(shopping_list)
            
            # Calculate next shopping date
            current_date = self.get_next_shopping_date_from_date(current_date, profile)
        
        # Ensure one list is triaged
        if created_lists:
            ShoppingListStatusManager.get_or_create_triaged_list(user)
        
        return {
            'created_lists': len(created_lists),
            'lists': ShoppingListSerializer(created_lists, many=True).data
        }
```

### 2. Handle Missed Shopping (Generate Estimated Transactions)
**Endpoint**: `POST /api/transactions/estimate-missed/`

```python
class EstimateMissedTransactionsView(APIView):
    """
    Identify missed shopping dates and redistribute products to future lists
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = EstimateMissedSerializer(data=request.data)
        if serializer.is_valid():
            missed_date = serializer.validated_data['missed_date']
            
            result = self.handle_missed_shopping(request.user, missed_date)
            return Response(result, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def handle_missed_shopping(self, user, missed_date):
        """
        Handle a missed shopping date by creating estimated transaction
        and redistributing products to future lists
        """
        # 1. Create estimated transaction for missed date
        estimated_transaction = self.create_estimated_transaction(user, missed_date)
        
        # 2. Get products that should have been purchased
        missed_products = self.get_products_for_date(user, missed_date)
        
        # 3. Add missed products to estimated transaction
        for product_data in missed_products:
            TransactionProduct.objects.create(
                transaction=estimated_transaction,
                product=product_data['product'],
                quantity=product_data['quantity'],
                unit_price=product_data['estimated_price'],
                total_price=product_data['estimated_price'] * product_data['quantity']
            )
        
        # 4. Redistribute products to future shopping lists
        redistributed_items = self.redistribute_missed_products(user, missed_products)
        
        return {
            'estimated_transaction': TransactionSerializer(estimated_transaction).data,
            'redistributed_items': redistributed_items,
            'total_missed_products': len(missed_products)
        }
    
    def redistribute_missed_products(self, user, missed_products):
        """
        Add missed products to future shopping lists
        """
        # Get future lists that can accept products (not expired/completed)
        future_lists = ShoppingList.objects.filter(
            user=user,
            scheduled_date__gte=timezone.now().date(),
            status__in=['IN_PROGRESS', 'TRIAGED']
        ).order_by('scheduled_date')
        
        redistributed = []
        
        for product_data in missed_products:
            # Find the earliest appropriate list for this product
            target_list = self.find_target_list_for_product(
                future_lists, 
                product_data['product'],
                product_data['frequency_days']
            )
            
            if target_list:
                # Add or update item in target list
                item, created = ShoppingListItem.objects.get_or_create(
                    shopping_list=target_list,
                    product=product_data['product'],
                    defaults={
                        'predicted_quantity': product_data['quantity'],
                        'predicted_price': product_data['estimated_price']
                    }
                )
                
                if not created:
                    # Item already exists, increase quantity
                    item.predicted_quantity += product_data['quantity']
                    item.save()
                
                redistributed.append({
                    'product': product_data['product'].name,
                    'quantity': product_data['quantity'],
                    'target_date': target_list.scheduled_date,
                    'action': 'created' if created else 'updated'
                })
        
        return redistributed
```

### 3. Shopping List Simulation
**Endpoint**: `POST /api/shopping-lists/simulate/`

```python
class SimulateShoppingBehaviorView(APIView):
    """
    Simulate shopping behavior patterns for testing and analysis
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SimulationSerializer(data=request.data)
        if serializer.is_valid():
            # Parameters
            num_lists = serializer.validated_data.get('num_lists', 4)
            start_date = serializer.validated_data.get('start_date')
            completion_pattern = serializer.validated_data['completion_pattern']  # [True, False, True, False]
            
            result = self.simulate_shopping_behavior(
                user=request.user,
                num_lists=num_lists,
                start_date=start_date,
                completion_pattern=completion_pattern
            )
            
            return Response(result, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def simulate_shopping_behavior(self, user, num_lists, start_date, completion_pattern):
        """
        Simulate shopping behavior without persisting changes
        Returns projected shopping lists based on completion pattern
        """
        # Generate initial lists (temporary, not saved)
        initial_lists = self.generate_temporary_lists(user, num_lists, start_date)
        
        # Apply completion pattern
        simulated_lists = []
        pending_products = []  # Products from missed trips
        
        for i, (shopping_list, is_missed) in enumerate(zip(initial_lists, completion_pattern)):
            if is_missed:
                # Trip was missed - add products to pending
                for item in shopping_list['items']:
                    pending_products.append({
                        'product': item['product'],
                        'quantity': item['quantity'],
                        'original_date': shopping_list['scheduled_date']
                    })
                
                # Mark list as expired
                shopping_list['status'] = 'EXPIRED'
                shopping_list['items'] = []  # Items moved to future lists
                
            else:
                # Trip was completed
                shopping_list['status'] = 'COMPLETED'
                
                # Add any pending products to this list
                current_items = shopping_list['items'][:]
                for pending in pending_products:
                    # Check if product already in list
                    existing_item = next(
                        (item for item in current_items if item['product']['id'] == pending['product']['id']), 
                        None
                    )
                    
                    if existing_item:
                        existing_item['quantity'] += pending['quantity']
                    else:
                        current_items.append({
                            'product': pending['product'],
                            'quantity': pending['quantity'],
                            'source': 'redistributed'
                        })
                
                shopping_list['items'] = current_items
                pending_products = []  # Clear pending after redistribution
            
            simulated_lists.append(shopping_list)
        
        return {
            'simulated_lists': simulated_lists,
            'final_pending_products': len(pending_products),
            'completion_rate': completion_pattern.count(False) / len(completion_pattern)
        }
```

### 4. Convert Expired List to Estimated Transaction
**Endpoint**: `POST /api/shopping-lists/{id}/convert-to-transaction/`

```python
class ConvertExpiredListView(APIView):
    """
    Convert an expired shopping list to an estimated transaction
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            shopping_list = ShoppingList.objects.get(
                pk=pk,
                user=request.user,
                status='EXPIRED'
            )
        except ShoppingList.DoesNotExist:
            return Response(
                {'error': 'Expired shopping list not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        estimated_transaction = self.convert_expired_list_to_transaction(shopping_list)
        
        return Response(
            TransactionSerializer(estimated_transaction).data,
            status=status.HTTP_201_CREATED
        )
    
    def convert_expired_list_to_transaction(self, shopping_list):
        """
        Convert expired shopping list to estimated transaction
        """
        # Create estimated transaction
        estimated_transaction = Transaction.objects.create(
            user=shopping_list.user,
            transaction_date=shopping_list.scheduled_date,
            transaction_type='ESTIMATED'
        )
        
        total_amount = Decimal('0.00')
        
        # Convert shopping list items to transaction products
        for item in shopping_list.items.all():
            estimated_price = item.predicted_price or self.calculate_predicted_price(
                shopping_list.user, 
                item.product
            )
            
            line_total = estimated_price * item.predicted_quantity
            total_amount += line_total
            
            TransactionProduct.objects.create(
                transaction=estimated_transaction,
                product=item.product,
                quantity=item.predicted_quantity,
                unit_price=estimated_price,
                total_price=line_total
            )
        
        # Update transaction total
        estimated_transaction.total_amount = total_amount
        estimated_transaction.save()
        
        return estimated_transaction
```

## Error Handling & Validation

### Custom Exceptions
```python
class ShoppingListException(Exception):
    pass

class InsufficientDataException(ShoppingListException):
    pass

class InvalidDateException(ShoppingListException):
    pass

class BusinessRuleViolationException(ShoppingListException):
    pass
```

### Validation Rules
```python
class GenerateListsSerializer(serializers.Serializer):
    num_lists = serializers.IntegerField(min_value=1, max_value=12, default=4)
    start_date = serializers.DateField(required=False)
    
    def validate_start_date(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Start date cannot be in the past")
        return value

class EstimateMissedSerializer(serializers.Serializer):
    missed_date = serializers.DateField()
    
    def validate_missed_date(self, value):
        if value >= timezone.now().date():
            raise serializers.ValidationError("Missed date must be in the past")
        
        # Check if date is too far in the past (more than 90 days)
        if (timezone.now().date() - value).days > 90:
            raise serializers.ValidationError("Cannot estimate transactions older than 90 days")
        
        return value

class SimulationSerializer(serializers.Serializer):
    num_lists = serializers.IntegerField(min_value=1, max_value=12)
    start_date = serializers.DateField()
    completion_pattern = serializers.ListField(
        child=serializers.BooleanField(),
        min_length=1,
        max_length=12
    )
    
    def validate(self, attrs):
        if len(attrs['completion_pattern']) != attrs['num_lists']:
            raise serializers.ValidationError(
                "Completion pattern length must match num_lists"
            )
        return attrs
```

## Testing Strategy

### Unit Tests
```python
class ShoppingListGenerationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.profile = UserProfile.objects.create(
            user=self.user,
            preferred_shopping_day=1,  # Tuesday
            preferred_shopping_frequency='WEEKLY'
        )
    
    def test_generate_lists_with_no_history(self):
        """Test generation when user has no transaction history"""
        # Should create empty lists or return appropriate message
        pass
    
    def test_frequency_calculation_single_purchase(self):
        """Test frequency calculation with insufficient data"""
        # Should return None or default frequency
        pass
    
    def test_redistribute_missed_products(self):
        """Test that missed products are correctly redistributed"""
        # Create scenario and verify redistribution logic
        pass
```

### Integration Tests
```python
class ShoppingListAPITests(APITestCase):
    def test_generate_lists_endpoint(self):
        """Test the complete list generation workflow"""
        pass
    
    def test_estimate_missed_transactions(self):
        """Test missed transaction estimation"""
        pass
    
    def test_simulation_endpoint(self):
        """Test shopping behavior simulation"""
        pass
```

### Authentication
All endpoints require authentication via DRF Token Authentication:
```
Authorization: Token <user_token>
```

### Response Format
```json
{
    "success": true,
    "data": { ... },
    "message": "Operation completed successfully",
    "errors": null
}
```

### Error Response Format
```json
{
    "success": false,
    "data": null,
    "message": "Validation failed",
    "errors": {
        "field_name": ["Error message"]
    }
}
```