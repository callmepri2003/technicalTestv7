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

from products.models import Product
from shoppingList.models import ShoppingList, ShoppingListItem
from transactions.models import Transaction, TransactionProduct
from profiles.models import UserProfile

from decimal import Decimal, ROUND_HALF_UP

User = get_user_model()

def round_decimal(value):
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class ApplicationIntegrationTest(APITestCase):
    """
    Integration test that exercises the complete application flow:
    1. Create user and products
    2. Generate shopping lists with predictions
    3. Complete some shopping trips (create actual transactions)
    4. Let some lists expire and convert to estimated transactions
    5. Verify all data flows correctly between apps
    """

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Create test products representing a typical grocery shopping scenario
        self.products = {
            'milk': Product.objects.create(
                name='Milk',
                category='Dairy',
                default_unit='litre'
            ),
            'bread': Product.objects.create(
                name='Whole Wheat Bread',
                category='Bakery',
                default_unit='loaf'
            ),
            'apples': Product.objects.create(
                name='Gala Apples',
                category='Fruit',
                default_unit='kg'
            ),
            'chicken': Product.objects.create(
                name='Chicken Breast',
                category='Meat',
                default_unit='kg'
            ),
            'rice': Product.objects.create(
                name='Basmati Rice',
                category='Grains',
                default_unit='kg'
            )
        }

    def test_complete_application_workflow(self):
        """
        Test the complete happy path workflow:
        - Generate shopping lists
        - Complete some shopping trips
        - Let some expire and convert to estimated transactions
        - Verify data integrity across all apps
        """
        
        # Step 1: Generate shopping lists for the next month
        print("\n=== Step 1: Generating Shopping Lists ===")
        
        with patch('shoppingList.services.ShoppingListGenerator') as mock_generator:
            # Mock the generator to create realistic shopping lists
            mock_instance = MagicMock()
            mock_generator.return_value = mock_instance
            
            # Create 4 shopping lists with different schedules
            generated_lists = []
            for i in range(4):
                shopping_list = ShoppingList.objects.create(
                    user=self.user,
                    scheduled_date=date.today() + timedelta(days=7 * (i + 1)),
                    status='IN_PROGRESS'
                )
                
                # Add items to each list with realistic quantities and prices
                items_data = [
                    (self.products['milk'], Decimal('1.0'), Decimal('3.50')),
                    (self.products['bread'], Decimal('1.0'), Decimal('2.80')),
                    (self.products['apples'], Decimal('1.5'), Decimal('4.99')),
                    (self.products['chicken'], Decimal('0.8'), Decimal('13.99')),
                    (self.products['rice'], Decimal('2.0'), Decimal('5.99'))
                ]
                
                for product, quantity, price in items_data:
                    ShoppingListItem.objects.create(
                        shopping_list=shopping_list,
                        product=product,
                        predicted_quantity=quantity,
                        predicted_price=price
                    )
                
                generated_lists.append(shopping_list)
            
            mock_instance.generate_lists.return_value = generated_lists
            
            # Test the generate endpoint
            url = reverse('shopping-list-generate')
            data = {
                'num_lists': 4,
                'start_date': str(date.today() + timedelta(days=7))
            }
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            print(f"Generated {len(generated_lists)} shopping lists")

        # Step 2: Verify shopping lists were created correctly
        print("\n=== Step 2: Verifying Shopping Lists ===")
        
        url = reverse('shopping-list-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 4)
        
        for shopping_list_data in response.data['data']['results']:
            self.assertEqual(shopping_list_data['status'], 'IN_PROGRESS')
            self.assertEqual(len(shopping_list_data['items']), 5)
            print(f"Shopping list {shopping_list_data['id']} has {len(shopping_list_data['items'])} items")

        # Step 3: Complete first two shopping lists (successful shopping trips)
        print("\n=== Step 3: Completing Shopping Trips ===")
        
        first_two_lists = generated_lists[:2]
        completed_transactions = []
        
        for shopping_list in first_two_lists:
            # First update status to TRIAGED (ready for shopping)
            url = reverse('shopping-list-detail', kwargs={'pk': shopping_list.id})
            data = {
                'scheduled_date': str(shopping_list.scheduled_date),
                'status': 'TRIAGED',
                'items': [
                    {
                        'product_id': item.product.id,
                        'predicted_quantity': float(item.predicted_quantity),
                        'predicted_price': float(item.predicted_price)
                    }
                    for item in shopping_list.items.all()
                ]
            }
            response = self.client.put(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Now complete the shopping trip
            url = reverse('shopping-list-complete', kwargs={'pk': shopping_list.id})
            completion_data = {
                'total_amount': 31.27,  # Realistic total
                'items': []
            }
            
            for item in shopping_list.items.all():
              actual_quantity = round_decimal(Decimal(item.predicted_quantity) * Decimal('0.95'))
              unit_price = round_decimal(Decimal(item.predicted_price) * Decimal('1.02'))

              completion_data['items'].append({
                  'item_id': item.id,
                  'actual_quantity': actual_quantity,
                  'is_purchased': True,
                  'unit_price': unit_price
              })
            
            response = self.client.post(url, completion_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify shopping list is now completed
            shopping_list.refresh_from_db()
            self.assertEqual(shopping_list.status, 'COMPLETED')
            self.assertIsNotNone(shopping_list.completed_at)
            
            print(f"Completed shopping list {shopping_list.id}")

        # Step 4: Verify actual transactions were created
        print("\n=== Step 4: Verifying Actual Transactions ===")
        
        url = reverse('transaction-list')
        response = self.client.get(url + '?transaction_type=ACTUAL')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_transactions = response.data['data']['results']
        self.assertEqual(len(actual_transactions), 2)
        
        for transaction in actual_transactions:
            self.assertEqual(transaction['transaction_type'], 'ACTUAL')
            self.assertEqual(len(transaction['products']), 5)
            self.assertGreater(float(transaction['total_amount']), 0)
            print(f"Created actual transaction {transaction['id']} with total ${transaction['total_amount']}")

        # Step 5: Let remaining shopping lists expire and convert to estimated transactions
        print("\n=== Step 5: Handling Expired Shopping Lists ===")
        
        remaining_lists = generated_lists[2:]
        
        for shopping_list in remaining_lists:
            # Simulate expiration by setting scheduled_date to past
            shopping_list.scheduled_date = date.today() - timedelta(days=1)
            shopping_list.status = 'EXPIRED'
            shopping_list.save()
            
            # Convert expired list to estimated transaction
            url = reverse('shopping-list-convert-to-transaction', kwargs={'pk': shopping_list.id})
            response = self.client.post(url)
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(response.data['success'])
            
            print(f"Converted expired shopping list {shopping_list.id} to estimated transaction")

        # Step 6: Verify estimated transactions were created
        print("\n=== Step 6: Verifying Estimated Transactions ===")
        
        url = reverse('transaction-list')
        response = self.client.get(url + '?transaction_type=ESTIMATED')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        estimated_transactions = response.data['data']['results']
        self.assertEqual(len(estimated_transactions), 2)
        
        for transaction in estimated_transactions:
            self.assertEqual(transaction['transaction_type'], 'ESTIMATED')
            self.assertEqual(len(transaction['products']), 5)
            self.assertGreater(float(transaction['total_amount']), 0)
            print(f"Created estimated transaction {transaction['id']} with total ${transaction['total_amount']}")

        # Step 7: Test missed transaction estimation
        print("\n=== Step 7: Testing Missed Transaction Estimation ===")
        
        with patch('transactions.views.ProductService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            
            # Mock estimation of missed products
            mock_instance.estimate_missed_products.return_value = {
                self.products['milk'].id: Decimal('1.0'),
                self.products['bread'].id: Decimal('2.0'),
                self.products['apples'].id: Decimal('1.5')
            }
            
            url = reverse('transaction-estimate-missed')
            data = {
                'transaction_date': str(date.today() - timedelta(days=3))
            }
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(response.data['success'])
            self.assertEqual(response.data['data']['transaction']['transaction_type'], 'ESTIMATED')
            
            print(f"Created missed transaction estimation for {len(response.data['data']['transaction']['products'])} products")

        # Step 8: Final verification - check all data integrity
        print("\n=== Step 8: Final Data Integrity Check ===")
        
        # Verify total transactions
        url = reverse('transaction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        all_transactions = response.data['data']['results']
        actual_count = len([t for t in all_transactions if t['transaction_type'] == 'ACTUAL'])
        estimated_count = len([t for t in all_transactions if t['transaction_type'] == 'ESTIMATED'])
        
        self.assertEqual(actual_count, 2)  # 2 completed shopping trips
        self.assertEqual(estimated_count, 3)  # 2 expired + 1 missed estimation
        
        # Verify shopping lists final states
        url = reverse('shopping-list-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        all_lists = response.data['data']['results']
        completed_count = len([sl for sl in all_lists if sl['status'] == 'COMPLETED'])
        expired_count = len([sl for sl in all_lists if sl['status'] == 'EXPIRED'])
        
        self.assertEqual(completed_count, 2)
        self.assertEqual(expired_count, 2)
        
        # Verify products are still intact
        self.assertEqual(Product.objects.count(), 5)
        
        print("\n=== Integration Test Summary ===")
        print(f"✓ Created 5 products")
        print(f"✓ Generated 4 shopping lists")
        print(f"✓ Completed 2 shopping trips → 2 actual transactions")
        print(f"✓ Expired 2 shopping lists → 2 estimated transactions")
        print(f"✓ Created 1 missed transaction estimation")
        print(f"✓ Total transactions: {len(all_transactions)} (2 actual, 3 estimated)")
        print(f"✓ All data integrity checks passed")
        
        
        # Verify transaction products were created correctly
        total_transaction_products = TransactionProduct.objects.filter(
            transaction__user=self.user
        ).count()
        self.assertGreater(total_transaction_products, 0)
        
        # Verify shopping list items were created correctly
        total_shopping_list_items = ShoppingListItem.objects.filter(
            shopping_list__user=self.user
        ).count()
        self.assertEqual(total_shopping_list_items, 20)  # 4 lists × 5 items each
        
        # Verify user owns all created data
        self.assertEqual(
            Transaction.objects.filter(user=self.user).count(),
            len(all_transactions)
        )
        self.assertEqual(
            ShoppingList.objects.filter(user=self.user).count(),
            len(all_lists)
        )
        
        print("✓ All integration tests passed successfully!")

    def test_error_handling_in_workflow(self):
        """Test that the workflow handles errors gracefully"""
        
        # Test completing a shopping list with invalid data
        shopping_list = ShoppingList.objects.create(
            user=self.user,
            scheduled_date=date.today() + timedelta(days=7),
            status='TRIAGED'
        )
        
        url = reverse('shopping-list-complete', kwargs={'pk': shopping_list.id})
        invalid_data = {
            'total_amount': 'invalid_amount',  # Invalid amount
            'items': []
        }
        
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify shopping list status didn't change
        shopping_list.refresh_from_db()
        self.assertEqual(shopping_list.status, 'TRIAGED')
        
        print("✓ Error handling test passed")