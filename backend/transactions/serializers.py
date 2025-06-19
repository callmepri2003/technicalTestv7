# transactions/serializers.py
from rest_framework import serializers
from .models import Transaction, TransactionProduct
from products.models import Product
from decimal import Decimal
from datetime import date

# Helper for Product detail in Transaction response
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'default_unit']
        read_only_fields = ['id', 'name', 'category', 'default_unit'] # Ensure these are read-only when nested


class TransactionProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True) # Nested serializer for GET responses
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )

    class Meta:
        model = TransactionProduct
        fields = ['id', 'product', 'product_id', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id', 'total_price'] # total_price is calculated

    def create(self, validated_data):
        # 'product' is handled by source='product' in product_id field
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # 'product' is handled by source='product' in product_id field
        return super().update(instance, validated_data)

    def validate(self, data):
        # Ensure unit_price is provided if total_price is not (or vice-versa, or both can be derived)
        quantity = data.get('quantity')
        unit_price = data.get('unit_price')
        # total_price = data.get('total_price') # For manual override if needed

        if quantity is not None and unit_price is not None:
            # Ensure quantity and unit_price are positive
            if quantity <= 0:
                raise serializers.ValidationError({"quantity": "Quantity must be a positive value."})
            if unit_price < 0: # Unit price can be zero in some cases
                raise serializers.ValidationError({"unit_price": "Unit price cannot be negative."})
            # total_price will be calculated in model's save method, or here explicitly if needed
            data['total_price'] = quantity * unit_price
        elif quantity is not None and (unit_price is None):
             # If only quantity is provided, and no unit_price, it's problematic for calculating total_price.
             # This depends on whether products *must* have a unit_price for 'ACTUAL' transactions.
             # For now, make unit_price optional as per OpenAPI, but advise frontend to send it if possible.
             # Or, enforce: raise serializers.ValidationError("unit_price is required for each product to calculate total_price.")
             pass # Let model handle missing total_price calculation or leave it null

        return data

class CreateTransactionProductSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )

    class Meta:
        model = TransactionProduct
        fields = ['product_id', 'quantity', 'unit_price']

    def validate(self, data):
        quantity = data.get('quantity')
        unit_price = data.get('unit_price')

        if quantity is None:
            raise serializers.ValidationError({"quantity": "Quantity is required for each product."})
        if quantity <= 0:
            raise serializers.ValidationError({"quantity": "Quantity must be a positive value."})
        if unit_price is not None and unit_price < 0:
            raise serializers.ValidationError({"unit_price": "Unit price cannot be negative."})

        return data


class TransactionSerializer(serializers.ModelSerializer):
    products = TransactionProductSerializer(many=True, read_only=True) # Nested for GET
    # total_amount will be calculated if not provided for ACTUAL types
    # receipt_image might need a special field for upload

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_date', 'transaction_type', 'total_amount',
            'receipt_image', 'shopping_list', 'products', 'created_at'
        ]
        read_only_fields = ['transaction_type', 'shopping_list', 'created_at'] # These are set by backend logic or linked

    def to_representation(self, instance):
        """Override to ensure total_amount is calculated on retrieve if needed."""
        representation = super().to_representation(instance)
        # Recalculate total_amount dynamically if it's null, or ensure it's correct
        if instance.transaction_type == 'ACTUAL' and (instance.total_amount is None or instance.total_amount == 0):
            calculated_total = sum(
                (item.quantity * item.unit_price if item.unit_price is not None else Decimal('0.00'))
                for item in instance.products.all()
            )
            representation['total_amount'] = str(calculated_total.quantize(Decimal('0.01'))) # Format to 2 decimal places
        return representation


class CreateTransactionSerializer(serializers.ModelSerializer):
    products = CreateTransactionProductSerializer(many=True) # Writable nested serializer
    receipt_image = serializers.FileField(required=False, allow_null=True) # For file upload

    class Meta:
        model = Transaction
        fields = ['id', 'transaction_date', 'total_amount', 'receipt_image', 'products']

    def validate(self, data):
        # Ensure products list is not empty
        if not data.get('products'):
            raise serializers.ValidationError({"products": "At least one product is required for a transaction."})

        # For ACTUAL transactions, if total_amount is not provided, calculate it from product unit_price * quantity
        if data.get('total_amount') is None:
            calculated_total = Decimal('0.00')
            for item_data in data['products']:
                quantity = item_data.get('quantity')
                unit_price = item_data.get('unit_price')
                if quantity is not None and unit_price is not None:
                    calculated_total += quantity * unit_price
                else:
                    # If unit_price is null for any product, total_amount cannot be fully calculated automatically
                    raise serializers.ValidationError(
                        {"total_amount": "Total amount cannot be automatically calculated if any product's unit price is missing."}
                    )
            data['total_amount'] = calculated_total.quantize(Decimal('0.01')) # Quantize for precision

        return data

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        validated_data['user'] = self.context['request'].user
        validated_data['transaction_type'] = 'ACTUAL' # Manual creation is always ACTUAL

        transaction = Transaction.objects.create(**validated_data)
        for item_data in products_data:
            TransactionProduct.objects.create(transaction=transaction, **item_data)
        return transaction


class UpdateTransactionProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False) # For existing items
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    # Allows marking for deletion by sending id and _delete: true
    _delete = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = TransactionProduct
        fields = ['id', 'product_id', 'quantity', 'unit_price', '_delete']
        extra_kwargs = {
            'quantity': {'required': True},
            'unit_price': {'required': False, 'allow_null': True}
        }

    def validate(self, data):
        if data.get('quantity') is not None and data.get('quantity') <= 0:
            raise serializers.ValidationError({"quantity": "Quantity must be a positive value."})
        if data.get('unit_price') is not None and data.get('unit_price') < 0:
            raise serializers.ValidationError({"unit_price": "Unit price cannot be negative."})
        return data


class UpdateTransactionSerializer(serializers.ModelSerializer):
    products = UpdateTransactionProductSerializer(many=True, required=False) # Optional for partial updates

    class Meta:
        model = Transaction
        fields = ['transaction_date', 'total_amount', 'receipt_image', 'products']
        read_only_fields = ['transaction_type', 'shopping_list'] # Cannot change type or shopping list link via this endpoint


    def validate(self, data):
        # Disallow updating 'ESTIMATED' transactions via this endpoint
        if self.instance and self.instance.transaction_type == 'ESTIMATED':
            raise serializers.ValidationError(
                {"detail": "Estimated transactions cannot be updated via this endpoint."}
            )

        # Handle total_amount recalculation if products are provided in update
        products_data = data.get('products')
        if products_data is not None:
            # If total_amount is explicitly provided, use it. Otherwise, calculate.
            if data.get('total_amount') is None:
                calculated_total = Decimal('0.00')
                for item_data in products_data:
                    # If an item is marked for deletion, skip it in calculation
                    if item_data.get('_delete'):
                        continue

                    quantity = item_data.get('quantity')
                    unit_price = item_data.get('unit_price')

                    if quantity is not None and unit_price is not None:
                        calculated_total += quantity * unit_price
                    else:
                        # This scenario means an existing product might be updated without unit_price
                        # or a new one added without unit_price.
                        # For updates, we need to consider existing unit_price if not provided.
                        item_id = item_data.get('id')
                        if item_id:
                            try:
                                existing_item = self.instance.products.get(id=item_id)
                                effective_quantity = quantity if quantity is not None else existing_item.quantity
                                effective_unit_price = unit_price if unit_price is not None else existing_item.unit_price
                                if effective_quantity is not None and effective_unit_price is not None:
                                    calculated_total += effective_quantity * effective_unit_price
                                else:
                                    # Still missing info to calculate for an existing item
                                    raise serializers.ValidationError(
                                        {"total_amount": "Total amount cannot be automatically calculated if product unit price is missing after update."}
                                    )
                            except TransactionProduct.DoesNotExist:
                                # New item being added, if unit_price is null, this would have been caught earlier in CreateTransactionProductSerializer's validate
                                pass
                        else:
                            # This is a new product being added in the update, must have unit_price
                            raise serializers.ValidationError(
                                {"total_amount": "Total amount cannot be automatically calculated if new product's unit price is missing."}
                            )

                data['total_amount'] = calculated_total.quantize(Decimal('0.01'))

        return data

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', None)

        # Update main Transaction fields
        instance.transaction_date = validated_data.get('transaction_date', instance.transaction_date)
        instance.total_amount = validated_data.get('total_amount', instance.total_amount)
        instance.receipt_image = validated_data.get('receipt_image', instance.receipt_image)
        instance.save()

        if products_data is not None:
            # Handle nested TransactionProducts
            for item_data in products_data:
                item_id = item_data.get('id')
                _delete = item_data.pop('_delete', False)

                if item_id:
                    # Existing item
                    try:
                        transaction_product = TransactionProduct.objects.get(
                            id=item_id, transaction=instance
                        )
                        if _delete:
                            transaction_product.delete()
                        else:
                            # Update existing fields, but preserve product reference
                            product_instance = item_data.pop('product', None) # Pop source='product' field
                            for key, value in item_data.items():
                                setattr(transaction_product, key, value)
                            transaction_product.save() # This will trigger total_price recalculation if unit_price/quantity changed
                    except TransactionProduct.DoesNotExist:
                        raise serializers.ValidationError(f"Transaction product with ID {item_id} not found in this transaction.")
                elif not _delete:
                    # New item (must have product_id)
                    product_instance = item_data.pop('product', None)  # This comes from source='product'
                    if product_instance is None:
                        raise serializers.ValidationError("product_id is required for new transaction products.")
                    TransactionProduct.objects.create(transaction=instance, product=product_instance, **item_data)

        # After product updates, re-save transaction to trigger total_amount recalculation if it's set to None
        # This is important if total_amount was not explicitly provided in the update payload.
        if instance.total_amount is None:
            instance.save() # Triggers the save method which can recalculate total_amount if it were None

        return instance


class EstimateMissedRequestSerializer(serializers.Serializer):
    missed_date = serializers.DateField()

    def validate_missed_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("Missed date cannot be in the future.")
        return value


class EstimateMissedTransactionProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True) # Nested serializer for GET responses
    # quantity and total_price are the main estimated fields

    class Meta:
        model = TransactionProduct
        fields = ['product', 'quantity', 'total_price']
        read_only_fields = ['product', 'quantity', 'total_price'] # All read-only in this context


class EstimateMissedResponseTransactionSerializer(serializers.ModelSerializer):
    products = EstimateMissedTransactionProductSerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'transaction_date', 'transaction_type', 'total_amount', 'products', 'created_at']
        read_only_fields = ['id', 'transaction_date', 'transaction_type', 'total_amount', 'products', 'created_at']


class EstimateMissedResponseSerializer(serializers.Serializer):
    transaction = EstimateMissedResponseTransactionSerializer()