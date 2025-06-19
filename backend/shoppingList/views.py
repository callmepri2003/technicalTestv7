# shoppingList/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import date

from .models import ShoppingList, ShoppingListItem
from .serializers import (
    ShoppingListSerializer,
    ShoppingListCreateUpdateSerializer,
    ShoppingListGenerateSerializer,
    ShoppingListCompleteSerializer,
    ShoppingListSimulateSerializer
)
from .services import ShoppingListGenerator, ShoppingListSimulator, ShoppingListService


class ShoppingListListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ShoppingListCreateUpdateSerializer
        return ShoppingListSerializer
    
    def get_queryset(self):
        queryset = ShoppingList.objects.filter(user=self.request.user)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        
        return queryset.prefetch_related('items__product')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        shopping_list = serializer.save(user=request.user)
        
        response_serializer = ShoppingListSerializer(shopping_list)
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Shopping list created successfully'
        }, status=status.HTTP_201_CREATED)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Handle pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return Response({
                'success': True,
                'data': {
                    'results': serializer.data,
                    'meta': {
                        'count': paginated_response.data['count'],
                        'next': paginated_response.data['next'],
                        'previous': paginated_response.data['previous']
                    }
                }
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': {
                'results': serializer.data,
                'meta': {
                    'count': len(serializer.data),
                    'next': None,
                    'previous': None
                }
            }
        })


class ShoppingListDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ShoppingListCreateUpdateSerializer
        return ShoppingListSerializer
    
    def get_queryset(self):
        return ShoppingList.objects.filter(user=self.request.user).prefetch_related('items__product')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        shopping_list = serializer.save()
        
        response_serializer = ShoppingListSerializer(shopping_list)
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Shopping list updated successfully'
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not instance.can_be_deleted():
            return Response({
                'success': False,
                'message': 'Cannot delete completed or expired shopping list'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_shopping_lists(request):
    """Generate shopping lists for the user"""
    serializer = ShoppingListGenerateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    generator = ShoppingListGenerator(request.user)
    created_lists = generator.generate_lists(
        num_lists=serializer.validated_data['num_lists'],
        start_date=serializer.validated_data.get('start_date')
    )
    
    return Response({
        'success': True,
        'data': {
            'created_lists': len(created_lists),
            'message': f'Generated {len(created_lists)} shopping lists'
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_shopping_list(request, pk):
    """Complete a shopping list"""
    shopping_list = get_object_or_404(
        ShoppingList.objects.filter(user=request.user),
        pk=pk
    )
    
    if shopping_list.status not in ['TRIAGED', 'PENDING']:
        return Response({
            'success': False,
            'message': 'Shopping list cannot be completed in current status'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = ShoppingListCompleteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        transaction = ShoppingListService.complete_shopping_list(
            shopping_list, 
            serializer.validated_data
        )
        
        response_serializer = ShoppingListSerializer(shopping_list)
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Shopping list completed successfully',
            'transaction_id': transaction.id
        })
    
    except ValueError as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convert_to_transaction(request, pk):
    """Convert expired shopping list to estimated transaction"""
    shopping_list = get_object_or_404(
        ShoppingList.objects.filter(user=request.user),
        pk=pk
    )
    
    if shopping_list.status != 'EXPIRED':
        return Response({
            'success': False,
            'message': 'Only expired shopping lists can be converted to transactions'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        transaction = ShoppingListService.convert_expired_to_transaction(shopping_list)
        
        return Response({
            'success': True,
            'data': {
                'transaction_id': transaction.id,
                'message': 'Shopping list converted to estimated transaction'
            }
        }, status=status.HTTP_201_CREATED)
    
    except ValueError as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulate_shopping_behavior(request):
    """Simulate shopping behavior"""
    serializer = ShoppingListSimulateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    simulator = ShoppingListSimulator(request.user)
    simulation_result = simulator.simulate(
        num_lists=serializer.validated_data['num_lists'],
        start_date=serializer.validated_data['start_date'],
        completion_pattern=serializer.validated_data.get('completion_pattern')
    )
    
    return Response({
        'success': True,
        'data': simulation_result
    })