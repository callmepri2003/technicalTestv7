# shoppingList/serializers.py
from rest_framework import serializers
from decimal import Decimal
from datetime import date, datetime
from .models import ShoppingList, ShoppingListItem
from products.models import Product


class ShoppingListItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_category = serializers.CharField(source='product.category', read_only=True)
    predicted_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    actual_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ShoppingListItem
        fields = [
            'id', 'product', 'product_name', 'product_category',
            'predicted_quantity', 'predicted_price', 'predicted_total',
            'actual_quantity', 'unit_price', 'actual_total', 'is_purchased'
        ]


class ShoppingListItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    predicted_quantity = serializers.DecimalField(max_digits=10, decimal_places=3)
    predicted_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    
    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product does not exist")
        return value


class ShoppingListSerializer(serializers.ModelSerializer):
    items = ShoppingListItemSerializer(many=True, read_only=True)
    total_predicted_amount = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ShoppingList
        fields = [
            'id', 'scheduled_date', 'status', 'created_at', 
            'updated_at', 'completed_at', 'items', 
            'total_predicted_amount', 'item_count'
        ]
        read_only_fields = ['created_at', 'updated_at', 'completed_at']
    
    def get_total_predicted_amount(self, obj):
        return sum(item.predicted_total for item in obj.items.all())
    
    def get_item_count(self, obj):
        return obj.items.count()


class ShoppingListCreateUpdateSerializer(serializers.ModelSerializer):
    items = ShoppingListItemCreateSerializer(many=True, required=False)
    
    class Meta:
        model = ShoppingList
        fields = ['scheduled_date', 'status', 'items']
    
    def validate_status(self, value):
        valid_transitions = {
            'IN_PROGRESS': ['TRIAGED'],
            'TRIAGED': ['PENDING'],
            'PENDING': ['COMPLETED', 'EXPIRED'],
            'COMPLETED': [],
            'EXPIRED': []
        }
        
        if self.instance:
            current_status = self.instance.status
            if value not in valid_transitions.get(current_status, []) and value != current_status:
                raise serializers.ValidationError(
                    f"Invalid status transition from {current_status} to {value}"
                )
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        shopping_list = ShoppingList.objects.create(**validated_data)
        
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            ShoppingListItem.objects.create(
                shopping_list=shopping_list,
                product=product,
                predicted_quantity=item_data['predicted_quantity'],
                predicted_price=item_data.get('predicted_price')
            )
        
        return shopping_list
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update shopping list fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update items if provided
        if items_data is not None:
            # Clear existing items
            instance.items.all().delete()
            
            # Create new items
            for item_data in items_data:
                product = Product.objects.get(id=item_data['product_id'])
                ShoppingListItem.objects.create(
                    shopping_list=instance,
                    product=product,
                    predicted_quantity=item_data['predicted_quantity'],
                    predicted_price=item_data.get('predicted_price')
                )
        
        return instance


class ShoppingListGenerateSerializer(serializers.Serializer):
    num_lists = serializers.IntegerField(min_value=1, max_value=12)
    start_date = serializers.DateField()
    
    def validate_start_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Start date cannot be in the past")
        return value


class ShoppingListCompleteItemSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    actual_quantity = serializers.DecimalField(max_digits=10, decimal_places=3, required=False)
    is_purchased = serializers.BooleanField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class ShoppingListCompleteSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    items = ShoppingListCompleteItemSerializer(many=True)
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item must be provided")
        return value


class ShoppingListSimulateSerializer(serializers.Serializer):
    num_lists = serializers.IntegerField(min_value=1, max_value=12)
    start_date = serializers.DateField()
    completion_pattern = serializers.ListField(
        child=serializers.BooleanField(),
        required=False
    )
    
    def validate_start_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Start date cannot be in the past")
        return value
    
    def validate(self, data):
        completion_pattern = data.get('completion_pattern', [])
        num_lists = data.get('num_lists', 0)
        
        if completion_pattern and len(completion_pattern) != num_lists:
            raise serializers.ValidationError(
                "Completion pattern length must match num_lists"
            )
        
        return data