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

from transactions.models import Transaction, TransactionProduct
from products.models import Product
from authentication.models import UserProfile # Assuming UserProfile is in authentication app
from shoppingList.models import ShoppingList # Used for linking to transactions

User = get_user_model()


class TransactionModelTest(TestCase):
    """Test Transaction and TransactionProduct model functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.product1 = Product.objects.create(
            name='Milk',
            category='Dairy',
            default_unit='liter'
        )
        self.product2 = Product.objects.create(
            name='Bread',
            category='Bakery',
            default_unit='loaf'
        )

    def test_transaction_creation(self):
        """Test basic transaction creation."""
        transaction = Transaction.objects.create(
            user=self.user,
            transaction_date=date.today(),
            transaction_type='ACTUAL',
            total_amount=Decimal('10.50')
        )
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.transaction_date, date.today())
        self.assertEqual(transaction.transaction_type, 'ACTUAL')
        self.assertEqual(transaction.total_amount, Decimal('10.50'))
        self.assertIsNotNone(transaction.created_at)

    def test_transaction_product_creation(self):
        """Test basic transaction product creation and association."""
        transaction = Transaction.objects.create(
            user=self.user,
            transaction_date=date.today(),
            transaction_type='ACTUAL',
            total_amount=Decimal('10.50')
        )
        transaction_product = TransactionProduct.objects.create(
            transaction=transaction,
            product=self.product1,
            quantity=Decimal('2.0'),
            unit_price=Decimal('1.75'),
            total_price=Decimal('3.50')
        )
        self.assertEqual(transaction_product.transaction, transaction)
        self.assertEqual(transaction_product.product, self.product1)
        self.assertEqual(transaction_product.quantity, Decimal('2.0'))
        self.assertEqual(transaction_product.unit_price, Decimal('1.75'))
        self.assertEqual(transaction_product.total_price, Decimal('3.50'))
        self.assertEqual(transaction.products.count(), 1)
        self.assertEqual(transaction.products.first(), transaction_product)

    def test_total_amount_calculation(self):
        """Test that total_amount is correctly calculated if not provided for ACTUAL transactions."""
        transaction = Transaction.objects.create(
            user=self.user,
            transaction_date=date.today(),
            transaction_type='ACTUAL',
            total_amount=None # Explicitly set to None to test calculation
        )
        TransactionProduct.objects.create(
            transaction=transaction,
            product=self.product1,
            quantity=Decimal('1.0'),
            unit_price=Decimal('2.50')
        )
        TransactionProduct.objects.create(
            transaction=transaction,
            product=self.product2,
            quantity=Decimal('3.0'),
            unit_price=Decimal('1.50')
        )
        # Re-fetch the transaction to ensure calculated total_amount is loaded
        transaction.refresh_from_db()
        self.assertEqual(transaction.total_amount, Decimal('7.00')) # 2.50 + (3 * 1.50) = 2.50 + 4.50 = 7.00


class TransactionAPITest(APITestCase):
    """Test API endpoints for Transactions."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        self.product1 = Product.objects.create(
            name='Apples',
            category='Fruit',
            default_unit='kg'
        )
        self.product2 = Product.objects.create(
            name='Oranges',
            category='Fruit',
            default_unit='kg'
        )
        self.product3 = Product.objects.create(
            name='Milk',
            category='Dairy',
            default_unit='liter'
        )

        # Create some initial transactions for listing and filtering tests
        self.transaction1 = Transaction.objects.create(
            user=self.user,
            transaction_date=date.today() - timedelta(days=5),
            transaction_type='ACTUAL',
            total_amount=Decimal('15.00')
        )
        TransactionProduct.objects.create(
            transaction=self.transaction1, product=self.product1, quantity=Decimal('2.0'), unit_price=Decimal('7.50')
        )

        self.transaction2 = Transaction.objects.create(
            user=self.user,
            transaction_date=date.today() - timedelta(days=10),
            transaction_type='ESTIMATED',
            total_amount=Decimal('20.00')
        )
        TransactionProduct.objects.create(
            transaction=self.transaction2, product=self.product2, quantity=Decimal('3.0'), unit_price=Decimal('6.00')
        )
        TransactionProduct.objects.create(
            transaction=self.transaction2, product=self.product3, quantity=Decimal('0.5'), unit_price=Decimal('4.00')
        )

        self.transaction_list_url = reverse('transaction-list') # Assumes 'transaction-list' as the name for /transactions/
        self.estimate_missed_url = reverse('transaction-estimate-missed') # Assumes 'transaction-estimate-missed' for /transactions/estimate-missed/

    # --- LIST TRANSACTIONS (/transactions/) ---
    def test_list_transactions_authenticated(self):
        """Ensure authenticated user can list their transactions."""
        response = self.client.get(self.transaction_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Transactions retrieved successfully')
        self.assertEqual(len(response.data['data']['results']), 2)

    def test_list_transactions_unauthenticated(self):
        """Ensure unauthenticated access to list transactions is denied."""
        self.client.credentials() # Clear credentials
        response = self.client.get(self.transaction_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_transactions_filter_by_type(self):
        """Test filtering transactions by transaction_type."""
        response = self.client.get(self.transaction_list_url + '?transaction_type=ACTUAL')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['transaction_type'], 'ACTUAL')

        response = self.client.get(self.transaction_list_url + '?transaction_type=ESTIMATED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['transaction_type'], 'ESTIMATED')

    def test_list_transactions_filter_by_date_range(self):
        """Test filtering transactions by date range."""
        today = date.today()
        # Filter for transactions within the last 7 days (should include transaction1)
        response = self.client.get(
            self.transaction_list_url + f'?date_from={today - timedelta(days=7)}&date_to={today}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['id'], self.transaction1.id)

        # Filter for transactions from a date before any exist
        response = self.client.get(
            self.transaction_list_url + f'?date_from={today - timedelta(days=20)}&date_to={today - timedelta(days=15)}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 0)

    # --- CREATE TRANSACTION (/transactions/) ---
    def test_create_transaction_manual_entry(self):
        """Test creating an actual transaction via manual entry."""
        data = {
            'transaction_date': str(date.today()),
            'total_amount': '25.75',
            'products': [
                {'product_id': self.product1.id, 'quantity': '1.0', 'unit_price': '10.00'},
                {'product_id': self.product2.id, 'quantity': '2.5', 'unit_price': '6.30'}
            ]
        }
        response = self.client.post(self.transaction_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('Transaction created successfully', response.data['message'])
        self.assertIsNotNone(response.data['data']['id'])
        self.assertEqual(response.data['data']['transaction_date'], str(date.today()))
        self.assertEqual(Decimal(response.data['data']['total_amount']), Decimal('25.75'))
        self.assertEqual(len(response.data['data']['products']), 2)

        # Verify creation in DB
        self.assertEqual(Transaction.objects.count(), 3)
        new_transaction = Transaction.objects.get(id=response.data['data']['id'])
        self.assertEqual(new_transaction.products.count(), 2)
        self.assertEqual(new_transaction.transaction_type, 'ACTUAL') # Default for manual creation

    def test_create_transaction_with_calculated_total_amount(self):
        """Test creating an actual transaction where total_amount is calculated from products."""
        data = {
            'transaction_date': str(date.today()),
            'products': [
                {'product_id': self.product1.id, 'quantity': '1.0', 'unit_price': '5.00'},
                {'product_id': self.product2.id, 'quantity': '2.0', 'unit_price': '2.50'}
            ]
        }
        response = self.client.post(self.transaction_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(Decimal(response.data['data']['total_amount']), Decimal('10.00')) # 5.00 + (2 * 2.50) = 10.00

    def test_create_transaction_missing_required_fields(self):
        """Test creating a transaction with missing required fields."""
        data = {
            'products': [ # Missing transaction_date
                {'product_id': self.product1.id, 'quantity': '1.0'}
            ]
        }
        response = self.client.post(self.transaction_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('transaction_date', response.data['errors'])

        data = {
            'transaction_date': str(date.today()) # Missing products
        }
        response = self.client.post(self.transaction_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('products', response.data['errors'])

    def test_create_transaction_with_invalid_product_id(self):
        """Test creating a transaction with a non-existent product ID."""
        data = {
            'transaction_date': str(date.today()),
            'products': [
                {'product_id': 9999, 'quantity': '1.0', 'unit_price': '10.00'} # Non-existent product
            ]
        }
        response = self.client.post(self.transaction_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('products', response.data['errors'])

    # --- GET TRANSACTION DETAILS (/transactions/{id}/) ---
    def test_get_transaction_details_authenticated(self):
        """Ensure authenticated user can retrieve details of their transaction."""
        url = reverse('transaction-detail', args=[self.transaction1.id]) # Assumes 'transaction-detail' for /transactions/{id}/
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], self.transaction1.id)
        self.assertEqual(response.data['data']['transaction_type'], 'ACTUAL')
        self.assertEqual(len(response.data['data']['products']), 1)

    def test_get_transaction_details_unauthenticated(self):
        """Ensure unauthenticated access to transaction details is denied."""
        self.client.credentials()
        url = reverse('transaction-detail', args=[self.transaction1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_transaction_details_not_found(self):
        """Test retrieving details for a non-existent transaction."""
        url = reverse('transaction-detail', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('not found', response.data['message'].lower())

    def test_get_transaction_details_other_user_transaction(self):
        """Ensure a user cannot retrieve another user's transaction."""
        other_user = User.objects.create_user(username='otheruser', password='password')
        other_transaction = Transaction.objects.create(
            user=other_user,
            transaction_date=date.today(),
            transaction_type='ACTUAL',
            total_amount=Decimal('5.00')
        )
        url = reverse('transaction-detail', args=[other_transaction.id])
        response = self.client.get(url) # Still authenticated as testuser
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Should return 404 for security reasons

    # --- UPDATE TRANSACTION (/transactions/{id}/) ---
    def test_update_actual_transaction(self):
        """Test updating an existing actual transaction."""
        url = reverse('transaction-detail', args=[self.transaction1.id])
        data = {
            'transaction_date': str(date.today() - timedelta(days=3)),
            'total_amount': '18.50',
            'products': [
                {'product_id': self.product1.id, 'quantity': '1.5', 'unit_price': '10.00'},
                {'product_id': self.product3.id, 'quantity': '1.0', 'unit_price': '3.50'}
            ]
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], self.transaction1.id)
        self.assertEqual(response.data['data']['transaction_date'], str(date.today() - timedelta(days=3)))
        self.assertEqual(Decimal(response.data['data']['total_amount']), Decimal('18.50'))
        self.assertEqual(len(response.data['data']['products']), 2)

        # Verify update in DB
        self.transaction1.refresh_from_db()
        self.assertEqual(self.transaction1.total_amount, Decimal('18.50'))
        self.assertEqual(self.transaction1.products.count(), 2)

    def test_update_actual_transaction_with_calculated_total_amount(self):
        """Test updating an actual transaction where total_amount is calculated from products."""
        url = reverse('transaction-detail', args=[self.transaction1.id])
        data = {
            'transaction_date': str(date.today() - timedelta(days=3)),
            'products': [
                {'product_id': self.product1.id, 'quantity': '1.0', 'unit_price': '5.00'},
                {'product_id': self.product2.id, 'quantity': '2.0', 'unit_price': '2.50'}
            ]
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(Decimal(response.data['data']['total_amount']), Decimal('10.00')) # 5.00 + (2 * 2.50) = 10.00


    def test_update_estimated_transaction_forbidden(self):
        """Ensure estimated transactions cannot be updated via this endpoint."""
        url = reverse('transaction-detail', args=[self.transaction2.id]) # self.transaction2 is ESTIMATED
        data = {
            'transaction_date': str(date.today()),
            'total_amount': '50.00',
            'products': [{'product_id': self.product1.id, 'quantity': '1.0'}]
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Estimated transactions cannot be updated', response.data['message'])

    def test_update_transaction_not_found(self):
        """Test updating a non-existent transaction."""
        url = reverse('transaction-detail', args=[9999])
        data = {
            'transaction_date': str(date.today()),
            'products': [{'product_id': self.product1.id, 'quantity': '1.0'}]
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- DELETE TRANSACTION (/transactions/{id}/) ---
    def test_delete_actual_transaction(self):
        """Test deleting an actual transaction."""
        url = reverse('transaction-detail', args=[self.transaction1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 1) # Only transaction2 should remain
        with self.assertRaises(Transaction.DoesNotExist):
            Transaction.objects.get(id=self.transaction1.id)
        # Ensure associated TransactionProducts are also deleted
        self.assertEqual(TransactionProduct.objects.filter(transaction=self.transaction1).count(), 0)

    def test_delete_estimated_transaction_forbidden(self):
        """Ensure estimated transactions cannot be deleted."""
        url = reverse('transaction-detail', args=[self.transaction2.id]) # self.transaction2 is ESTIMATED
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Estimated transactions cannot be deleted', response.data['message'])

    def test_delete_transaction_not_found(self):
        """Test deleting a non-existent transaction."""
        url = reverse('transaction-detail', args=[9999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- ESTIMATE MISSED TRANSACTION (/transactions/estimate-missed/) ---
    @patch('transactions.views.ProductService') # Mock the external service for isolation
    def test_estimate_missed_transaction_success(self, MockProductService):
        """Test successful estimation of a missed transaction."""
        mock_instance = MockProductService.return_value
        mock_instance.estimate_missed_products.return_value = {
            self.product1.id: Decimal('1.5'),
            self.product2.id: Decimal('2.0')
        }

        data = {
            'missed_date': str(date.today() - timedelta(days=7))
        }
        response = self.client.post(self.estimate_missed_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('Missed transaction estimated successfully', response.data['message'])
        self.assertIsNotNone(response.data['data']['transaction']['id'])
        self.assertEqual(response.data['data']['transaction']['transaction_type'], 'ESTIMATED')
        self.assertEqual(response.data['data']['transaction']['transaction_date'], data['missed_date'])
        self.assertEqual(len(response.data['data']['transaction']['products']), 2)

        MockProductService.assert_called_once_with(self.user)
        mock_instance.estimate_missed_products.assert_called_once_with(date(date.today().year, date.today().month, date.today().day) - timedelta(days=7))

        # Verify creation in DB
        new_estimated_transaction = Transaction.objects.get(id=response.data['data']['transaction']['id'])
        self.assertEqual(new_estimated_transaction.transaction_type, 'ESTIMATED')
        self.assertEqual(new_estimated_transaction.transaction_date, date.today() - timedelta(days=7))
        self.assertEqual(new_estimated_transaction.products.count(), 2)

    def test_estimate_missed_transaction_invalid_date(self):
        """Test estimating a missed transaction with an invalid date format."""
        data = {
            'missed_date': '2023/10/26' # Invalid format
        }
        response = self.client.post(self.estimate_missed_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('missed_date', response.data['errors'])

    @patch('transactions.views.ProductService')
    def test_estimate_missed_transaction_no_products_estimated(self, MockProductService):
        """Test estimating a missed transaction when no products are estimated."""
        mock_instance = MockProductService.return_value
        mock_instance.estimate_missed_products.return_value = {} # No products estimated

        data = {
            'missed_date': str(date.today() - timedelta(days=1))
        }
        response = self.client.post(self.estimate_missed_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) # Still 201 if empty transaction can be created
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['transaction']['products']), 0)