from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction_atomic
from django.db.models import Sum, F # For aggregation if needed
import django_filters.rest_framework
from decimal import Decimal

from .models import Transaction, TransactionProduct
from .serializers import (
    TransactionSerializer, CreateTransactionSerializer, UpdateTransactionSerializer,
    EstimateMissedRequestSerializer, EstimateMissedResponseSerializer
)
from .permissions import IsOwnerPermission
from .pagination import CustomPageNumberPagination # Assuming you have this
from products.models import Product # Needed for EstimateMissedTransaction
from products.services import ProductService # Import the service for business logic

class TransactionFilter(django_filters.rest_framework.FilterSet):
    transaction_type = django_filters.rest_framework.ChoiceFilter(
        choices=Transaction.TRANSACTION_TYPE_CHOICES,
        field_name='transaction_type'
    )
    date_from = django_filters.rest_framework.DateFilter(
        field_name='transaction_date', lookup_expr='gte'
    )
    date_to = django_filters.rest_framework.DateFilter(
        field_name='transaction_date', lookup_expr='lte'
    )

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'date_from', 'date_to']


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerPermission]
    pagination_class = CustomPageNumberPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = TransactionFilter
    # lookup_field = 'id' # default is 'pk', which is usually fine

    def get_queryset(self):
        """
        Ensure users can only see their own transactions.
        Prefetch related products to avoid N+1 queries.
        """
        return self.queryset.filter(user=self.request.user).prefetch_related('products__product')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTransactionSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UpdateTransactionSerializer
        return TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({
            'success': True,
            'message': 'Transaction created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'message': 'Transactions retrieved successfully',
                'data': {
                    'results': serializer.data,
                    'count': self.paginator.page.paginator.count,
                    'next': self.paginator.get_next_link(),
                    'previous': self.paginator.get_previous_link()
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'message': 'Transactions retrieved successfully',
            'data': {
                'results': serializer.data
            }
        })

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'message': 'Transaction retrieved successfully',
                'data': serializer.data
            })
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Transaction not found',
                'errors': {'detail': 'Transaction not found'}
            }, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Custom logic: Estimated transactions cannot be updated via this endpoint
        if instance.transaction_type == 'ESTIMATED':
            return Response({
                'success': False,
                'message': 'Estimated transactions cannot be updated directly.',
                'errors': {'detail': 'Estimated transactions can only be converted from shopping lists or generated.'}
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied, we must refresh the instance
            # to reflect changes.
            instance = self.get_object()
            serializer = self.get_serializer(instance)

        return Response({
            'success': True,
            'message': 'Transaction updated successfully',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Custom logic: Only ACTUAL transactions can be deleted
        if instance.transaction_type == 'ESTIMATED':
            return Response({
                'success': False,
                'message': 'Estimated transactions cannot be deleted.',
                'errors': {'detail': 'Only actual transactions can be deleted.'}
            }, status=status.HTTP_400_BAD_REQUEST)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='estimate-missed',
            serializer_class=EstimateMissedRequestSerializer)
    def estimate_missed(self, request):
        """
        POST /transactions/estimate-missed/
        Creates an estimated transaction for a missed shopping date.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        missed_date = serializer.validated_data['transaction_date']

        product_service = ProductService(request.user)

        with db_transaction_atomic.atomic():
            # 1. Estimate products for the missed date
            estimated_product_quantities = product_service.estimate_missed_products(missed_date)

            if not estimated_product_quantities:
                # If no products are estimated, still create an empty estimated transaction
                # or return a specific message/error if empty transactions are not allowed.
                # OpenAPI suggests a 201 response with data, so creating an empty one is acceptable.
                pass # Proceed to create transaction, it will just have no products

            # 2. Create the estimated transaction
            estimated_transaction = Transaction.objects.create(
                user=request.user,
                transaction_date=missed_date,
                transaction_type='ESTIMATED',
                total_amount=Decimal('0.00') # Initialize total_amount, will sum up from products
            )

            # 3. Add estimated products to the transaction
            for product_id, quantity in estimated_product_quantities.items():
                try:
                    product = Product.objects.get(id=product_id)
                    # For estimated transactions, unit_price might not be precise,
                    # or could be an average. For now, let's assume it's part of estimation or 0.
                    # If Product has a default price, could use that. Let's use 0 for simplicity if not defined.
                    unit_price = product.default_unit_price if hasattr(product, 'default_unit_price') else Decimal('0.00')
                    TransactionProduct.objects.create(
                        transaction=estimated_transaction,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price, # This might be zero or a placeholder
                        total_price=quantity * unit_price
                    )
                except Product.DoesNotExist:
                    # Log this or handle error: estimated product ID doesn't exist
                    continue

            # Recalculate total_amount after products are added
            # This is important if total_amount was initially set to 0.00
            actual_total_amount = estimated_transaction.products.aggregate(
                sum_total=Sum(F('quantity') * F('unit_price'))
            )['sum_total'] or Decimal('0.00')
            estimated_transaction.total_amount = actual_total_amount.quantize(Decimal('0.01'))
            estimated_transaction.save()

            response_serializer = EstimateMissedResponseSerializer(
                {'transaction': estimated_transaction}
            )

            return Response({
                'success': True,
                'message': 'Missed transaction estimated successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)