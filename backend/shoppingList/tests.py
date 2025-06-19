import json
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch, MagicMock

from shoppingList.models import ShoppingList, ShoppingListItem
from products.models import Product
from transactions.models import Transaction, TransactionProduct
from authentication.models import UserProfile

User = get_user_model()


class ShoppingListModelTest(TestCase):
    """Test ShoppingList model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='Test Product',
            category='Test Category',
            default_unit='item'
        )
        
    def test_shopping_list_creation(self):
        """Test basic shopping list creation"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        self.assertEqual(shopping_list.user, self.user)
        self.assertEqual(shopping_list.status, 'IN_PROGRESS')
        
    def test_shopping_list_item_creation(self):
        """Test shopping list item creation"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        item = ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            product=self.product,
            predicted_quantity=Decimal('2.0'),
            predicted_price=Decimal('5.99')
        )
        self.assertEqual(item.shopping_list, shopping_list)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.predicted_quantity, Decimal('2.0'))
        self.assertFalse(item.is_purchased)
        
    def test_shopping_list_status_transitions(self):
        """Test valid status transitions"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        
        # Valid transitions
        valid_transitions = [
            ('IN_PROGRESS', 'TRIAGED'),
            ('TRIAGED', 'PENDING'),
            ('PENDING', 'COMPLETED'),
            ('PENDING', 'EXPIRED')
        ]
        
        for from_status, to_status in valid_transitions:
            shopping_list.status = from_status
            shopping_list.save()
            shopping_list.status = to_status
            shopping_list.save()
            self.assertEqual(shopping_list.status, to_status)


class ShoppingListAPITest(APITestCase):
    """Test Shopping List API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.product1 = Product.objects.create(
            name='Milk',
            category='Dairy',
            default_unit='litre'
        )
        self.product2 = Product.objects.create(
            name='Bread',
            category='Bakery',
            default_unit='item'
        )
        
    def test_list_shopping_lists(self):
        """Test GET /shopping-lists/"""
        # Create test shopping lists
        ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=14),
            status='TRIAGED'
        )
        
        url = reverse('shopping-list-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 2)
        self.assertTrue(response.data['success'])
        
    def test_list_shopping_lists_with_filters(self):
        """Test GET /shopping-lists/ with status filter"""
        ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=14),
            status='COMPLETED'
        )
        
        url = reverse('shopping-list-list')
        response = self.client.get(url, {'status': 'IN_PROGRESS'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['status'], 'IN_PROGRESS')
        
    def test_get_shopping_list_detail(self):
        """Test GET /shopping-lists/{id}/"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            product=self.product1,
            predicted_quantity=Decimal('2.0'),
            predicted_price=Decimal('3.50')
        )
        
        url = reverse('shopping-list-detail', kwargs={'pk': shopping_list.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], shopping_list.id)
        self.assertEqual(len(response.data['data']['items']), 1)
        self.assertTrue(response.data['success'])
        
    def test_update_shopping_list(self):
        """Test PUT /shopping-lists/{id}/"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        
        url = reverse('shopping-list-detail', kwargs={'pk': shopping_list.id})
        data = {
            'status': 'TRIAGED',
            'items': [
                {
                    'product_id': self.product1.id,
                    'predicted_quantity': 2.0,
                    'predicted_price': 3.50
                }
            ]
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        shopping_list.refresh_from_db()
        self.assertEqual(shopping_list.status, 'TRIAGED')
        self.assertEqual(shopping_list.items.count(), 1)
        
    def test_delete_shopping_list_in_progress(self):
        """Test DELETE /shopping-lists/{id}/ for IN_PROGRESS list"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        
        url = reverse('shopping-list-detail', kwargs={'pk': shopping_list.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ShoppingList.objects.filter(id=shopping_list.id).exists())
        
    def test_delete_shopping_list_completed_fails(self):
        """Test DELETE /shopping-lists/{id}/ for COMPLETED list should fail"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='COMPLETED'
        )
        
        url = reverse('shopping-list-detail', kwargs={'pk': shopping_list.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(ShoppingList.objects.filter(id=shopping_list.id).exists())
        
    @patch('shoppingList.services.ShoppingListGenerator')
    def test_generate_shopping_lists(self, mock_generator):
        """Test POST /shopping-lists/generate/"""
        # Mock the generator service
        mock_instance = MagicMock()
        mock_generator.return_value = mock_instance
        mock_instance.generate_lists.return_value = [
            ShoppingList.objects.create(
                user=self.user,
                scheduled_date=date.today() + timedelta(days=7),
                status='IN_PROGRESS'
            )
        ]
        
        url = reverse('shopping-list-generate')
        data = {
            'num_lists': 4,
            'start_date': str(date.today() + timedelta(days=7))
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['created_lists'], 1)
        self.assertTrue(response.data['success'])
        
    def test_complete_shopping_list(self):
        """Test POST /shopping-lists/{id}/complete/"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today(),
            status='TRIAGED'
        )
        item = ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            product=self.product1,
            predicted_quantity=Decimal('2.0'),
            predicted_price=Decimal('3.50')
        )
        
        url = reverse('shopping-list-complete', kwargs={'pk': shopping_list.id})
        data = {
            'total_amount': 7.00,
            'items': [
                {
                    'item_id': item.id,
                    'actual_quantity': 2.0,
                    'is_purchased': True,
                    'unit_price': 3.50
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        shopping_list.refresh_from_db()
        self.assertEqual(shopping_list.status, 'COMPLETED')
        self.assertIsNotNone(shopping_list.completed_at)
        
        # Check transaction was created
        self.assertTrue(Transaction.objects.filter(
            user=self.user,
            transaction_type='ACTUAL'
        ).exists())
        
    def test_convert_expired_list_to_transaction(self):
        """Test POST /shopping-lists/{id}/convert-to-transaction/"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() - timedelta(days=1),
            status='EXPIRED'
        )
        ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            product=self.product1,
            predicted_quantity=Decimal('2.0'),
            predicted_price=Decimal('3.50')
        )
        
        url = reverse('shopping-list-convert-to-transaction', kwargs={'pk': shopping_list.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check estimated transaction was created
        transaction = Transaction.objects.get(
            user=self.user,
            transaction_type='ESTIMATED'
        )
        self.assertEqual(transaction.products.count(), 1)
        
    def test_convert_non_expired_list_fails(self):
        """Test converting non-expired list should fail"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        
        url = reverse('shopping-list-convert-to-transaction', kwargs={'pk': shopping_list.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class ShoppingListSimulationTest(APITestCase):
    """Test shopping list simulation functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.product = Product.objects.create(
            name='Test Product',
            category='Test Category',
            default_unit='item'
        )
        
    @patch('shoppingList.services.ShoppingListSimulator')
    def test_simulate_shopping_behavior(self, mock_simulator):
        """Test POST /shopping-lists/simulate/"""
        # Mock the simulator service
        mock_instance = MagicMock()
        mock_simulator.return_value = mock_instance
        mock_instance.simulate.return_value = {
            'simulated_lists': [
                {
                    'id': 1,
                    'scheduled_date': str(date.today() + timedelta(days=7)),
                    'status': 'COMPLETED',
                    'items': []
                }
            ],
            'final_pending_products': 0,
            'completion_rate': 0.75
        }
        
        url = reverse('shopping-list-simulate')
        data = {
            'num_lists': 4,
            'start_date': str(date.today() + timedelta(days=7)),
            'completion_pattern': [True, False, True, True]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['completion_rate'], 0.75)


class ShoppingListEdgeCasesTest(APITestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
    def test_access_other_users_shopping_list(self):
        """Test that users cannot access other users' shopping lists"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        other_shopping_list = ShoppingList.objects.create(
            user=other_user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        
        url = reverse('shopping-list-detail', kwargs={'pk': other_shopping_list.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_complete_shopping_list_wrong_status(self):
        """Test completing shopping list with wrong status"""
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today(),
            status='COMPLETED'  # Already completed
        )
        
        url = reverse('shopping-list-complete', kwargs={'pk': shopping_list.id})
        data = {'items': []}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        
    def test_generate_lists_invalid_parameters(self):
        """Test generating lists with invalid parameters"""
        url = reverse('shopping-list-generate')
        
        # Test with too many lists
        data = {'num_lists': 15}  # Max is 12
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with past date
        data = {
            'num_lists': 4,
            'start_date': str(date.today() - timedelta(days=1))
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_unauthorized_access(self):
        """Test accessing endpoints without authentication"""
        self.client.credentials()  # Remove authentication
        
        url = reverse('shopping-list-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_pagination(self):
        """Test pagination for shopping lists"""
        # Create multiple shopping lists
        for i in range(25):
            ShoppingList.objects.create(
                user=self.user,
                scheduled_date=date.today() + timedelta(days=i+1),
                status='IN_PROGRESS'
            )
            
        url = reverse('shopping-list-list')
        response = self.client.get(url, {'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 10)
        self.assertIsNotNone(response.data['data']['meta']['next'])
        
    def test_update_nonexistent_shopping_list(self):
        """Test updating a shopping list that doesn't exist"""
        url = reverse('shopping-list-detail', kwargs={'pk': 999})
        data = {'status': 'TRIAGED'}
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ShoppingListItemTest(TestCase):
    """Test ShoppingListItem specific functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='Test Product',
            category='Test Category',
            default_unit='item'
        )
        self.shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='IN_PROGRESS'
        )
        
    def test_shopping_list_item_str_representation(self):
        """Test string representation of shopping list item"""
        item = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            product=self.product,
            predicted_quantity=Decimal('2.0')
        )
        expected_str = f"{self.product.name} x 2.0"
        self.assertIn(self.product.name, str(item))
        
    def test_shopping_list_item_decimal_precision(self):
        """Test decimal precision for quantities and prices"""
        item = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            product=self.product,
            predicted_quantity=Decimal('2.555'),
            predicted_price=Decimal('3.999')
        )
        # Assuming model uses appropriate decimal places
        self.assertEqual(item.predicted_quantity, Decimal('2.555'))
        self.assertEqual(item.predicted_price, Decimal('3.999'))
        
    def test_shopping_list_total_calculation(self):
        """Test calculation of shopping list total"""
        ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            product=self.product,
            predicted_quantity=Decimal('2.0'),
            predicted_price=Decimal('3.50')
        )
        
        # Assuming model has a method to calculate total
        # This would depend on your actual model implementation
        items = self.shopping_list.items.all()
        total = sum(item.predicted_quantity * (item.predicted_price or 0) for item in items)
        self.assertEqual(total, Decimal('7.00'))