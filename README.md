# Shopping List Management API

## Technical Test for Cloud Ascension Global

A Django REST API for managing shopping lists, products, transactions, and user profiles. This application allows users to create, manage, and track their shopping activities with features like predicted pricing, actual purchase tracking, and transaction history.

## 🎯 Key Deliverable Endpoints

This project implements four core technical test endpoints:

1. **Predict N Shopping Lists** - Generate multiple shopping lists with predicted items
2. **Estimate Missing Items** - Calculate estimated costs for items not purchased
3. **Mock Inconsistent Use** - Simulate real-world usage patterns with inconsistencies
4. **Convert Expired to Estimated** - Transform expired shopping lists into estimated transactions

*See the [Core Deliverable Endpoints](#core-deliverable-endpoints) section below for detailed implementation.*

## Features

- **User Authentication**: Token-based authentication system
- **Shopping List Management**: Create, update, and manage shopping lists with different statuses
- **Product Tracking**: Track predicted vs actual quantities and prices
- **Transaction Recording**: Record actual purchases with receipt image support
- **Profile Management**: User profile functionality
- **CORS Support**: Cross-origin resource sharing enabled
- **Admin Interface**: Django admin panel for data management

## Technology Stack

- **Backend**: Django 4.2.6
- **API Framework**: Django REST Framework
- **Database**: SQLite (development)
- **Authentication**: Token Authentication
- **File Storage**: Local media storage for receipt images
- **CORS**: django-cors-headers

## Project Structure

```
backend/
├── authentication/       # User authentication app
├── shoppingList/        # Shopping list management
├── products/            # Product catalog
├── transactions/        # Transaction tracking
├── profiles/            # User profiles
├── media/              # Uploaded files (receipts)
├── backend/            # Main project settings
└── manage.py
```

## Installation & Setup

### Prerequisites

- Python 3.8+
- pip
- virtualenv (recommended)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django djangorestframework django-cors-headers pillow
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

## API Endpoints

### Core Deliverable Endpoints

#### 🎯 Technical Test Requirements

1. **Predict N Shopping Lists**
   ```
   POST /api/shopping-lists/generate/
   ```
   - **Location**: `shoppingList/views.py` - `ShoppingListGenerateView`
   - **Serializer**: `ShoppingListGenerateSerializer`
   - **Purpose**: Generate multiple shopping lists with predicted items and pricing
   - **Parameters**: `num_lists`, `start_date`

2. **Estimate Missing Items**
   ```
   POST /api/shopping-lists/{id}/estimate-missing/
   ```
   - **Location**: `shoppingList/views.py` - Custom endpoint in shopping list viewset
   - **Purpose**: Calculate estimated costs for items that weren't purchased
   - **Use Case**: When users didn't complete their shopping list

3. **Mock Inconsistent Use**
   ```
   POST /api/shopping-lists/simulate/
   ```
   - **Location**: `shoppingList/views.py` - `ShoppingListSimulateView`
   - **Serializer**: `ShoppingListSimulateSerializer`
   - **Purpose**: Simulate real-world usage with inconsistent completion patterns
   - **Parameters**: `num_lists`, `start_date`, `completion_pattern`

4. **Convert Expired to Estimated**
   ```
   POST /api/shopping-lists/convert-expired/
   ```
   - **Location**: `shoppingList/views.py` - Custom endpoint
   - **Purpose**: Convert expired shopping lists into estimated transaction records
   - **Process**: Finds expired lists → Creates estimated transactions → Updates status

### Standard CRUD Endpoints

#### Authentication
- `POST /api/auth/` - Authentication endpoints

#### Shopping Lists
- `GET /api/shopping-lists/` - List all shopping lists
- `POST /api/shopping-lists/` - Create new shopping list
- `GET /api/shopping-lists/{id}/` - Get specific shopping list
- `PUT /api/shopping-lists/{id}/` - Update shopping list
- `DELETE /api/shopping-lists/{id}/` - Delete shopping list
- `POST /api/shopping-lists/{id}/complete/` - Mark shopping list as completed

#### Transactions
- `GET /api/transactions/` - List all transactions
- `POST /api/transactions/` - Create new transaction

#### Profile
- `GET /api/profile/` - Get user profile
- `PUT /api/profile/` - Update user profile

## Models Overview

### ShoppingList
- **Status Flow**: IN_PROGRESS → TRIAGED → PENDING → COMPLETED/EXPIRED
- **Fields**: user, scheduled_date, status, timestamps
- **Methods**: `can_be_deleted()`, `is_expired()`

### ShoppingListItem
- **Fields**: product, predicted_quantity, predicted_price, actual_quantity, unit_price, is_purchased
- **Properties**: `predicted_total`, `actual_total`

### Transaction
- **Types**: ACTUAL (real purchase), ESTIMATED (missed purchase estimation)
- **Fields**: user, transaction_date, transaction_type, total_amount, receipt_image, shopping_list
- **Method**: `_calculate_total_from_products()`

### TransactionProduct
- **Fields**: transaction, product, quantity, unit_price, total_price
- **Auto-calculation**: total_price = quantity × unit_price

## Serializers

### ShoppingListSerializer
- Includes nested items with product details
- Calculated fields: `total_predicted_amount`, `item_count`

### ShoppingListCreateUpdateSerializer
- Handles shopping list creation and updates
- Validates status transitions
- Manages nested item creation/updates

### Specialized Serializers
- `ShoppingListGenerateSerializer`: For bulk list generation
- `ShoppingListCompleteSerializer`: For marking lists as complete
- `ShoppingListSimulateSerializer`: For simulation functionality

## Authentication

The API uses **Token Authentication**. To access protected endpoints:

1. **Obtain token** (login endpoint)
2. **Include in headers**:
   ```
   Authorization: Token <your-token-here>
   ```

## File Uploads

Receipt images are supported for transactions:
- **Upload Path**: `/media/receipts/`
- **Supported Formats**: Standard image formats (JPEG, PNG, etc.)
- **Access URL**: `http://localhost:8000/media/receipts/<filename>`

## Status Workflow

### Shopping List Status Transitions
```
IN_PROGRESS → TRIAGED → PENDING → COMPLETED
                    ↘         ↘
                      EXPIRED   EXPIRED
```

- **IN_PROGRESS**: Initial state, list being created
- **TRIAGED**: List reviewed and organized
- **PENDING**: Ready for shopping
- **COMPLETED**: Shopping completed successfully
- **EXPIRED**: Past scheduled date without completion

## Configuration

### Key Settings
- `DEBUG = True` (development only)
- `CORS_ALLOW_ALL_ORIGINS = True` (configure for production)
- `MEDIA_URL = '/media/'` (file serving)
- Token authentication enabled by default

### Security Notes
⚠️ **Important for Production**:
- Change `SECRET_KEY` in settings
- Set `DEBUG = False`
- Configure `ALLOWED_HOSTS`
- Restrict CORS origins
- Use production database (PostgreSQL recommended)
- Configure proper media file serving

## Development

### 🎯 Core Deliverable Implementation

The four main technical test endpoints are implemented in:

**File**: `shoppingList/views.py`
- `ShoppingListGenerateView` - Handles bulk shopping list generation
- `ShoppingListSimulateView` - Manages inconsistent usage simulation  
- Custom endpoint methods within the main viewset for missing item estimation and expired list conversion

**File**: `shoppingList/serializers.py`
- `ShoppingListGenerateSerializer` - Validates generation parameters
- `ShoppingListSimulateSerializer` - Handles simulation patterns
- `ShoppingListCompleteSerializer` - Manages completion data

**File**: `shoppingList/urls.py` (inferred)
- URL routing for the custom endpoints

### Adding New Features
1. Create new Django app: `python manage.py startapp <app_name>`
2. Add to `INSTALLED_APPS` in settings
3. Create models, serializers, and views
4. Add URL patterns
5. Run migrations

### Testing
```bash
python manage.py test
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development)
python manage.py flush
```

## API Usage Examples

### 🎯 Core Deliverable Examples

#### 1. Predict N Shopping Lists
```python
POST /api/shopping-lists/generate/
{
    "num_lists": 4,
    "start_date": "2025-06-25"
}
```

#### 2. Estimate Missing Items
```python
POST /api/shopping-lists/123/estimate-missing/
# Automatically calculates estimated costs for unpurchased items
# Creates estimated transaction records
```

#### 3. Mock Inconsistent Use
```python
POST /api/shopping-lists/simulate/
{
    "num_lists": 6,
    "start_date": "2025-06-25",
    "completion_pattern": [true, false, true, true, false, true]
}
```

#### 4. Convert Expired to Estimated
```python
POST /api/shopping-lists/convert-expired/
# Finds all expired shopping lists
# Converts them to estimated transactions
# Updates shopping list status
```

### Standard CRUD Examples

#### Create Shopping List
```python
POST /api/shopping-lists/
{
    "scheduled_date": "2025-06-25",
    "items": [
        {
            "product_id": 1,
            "predicted_quantity": 2.5,
            "predicted_price": 3.50
        }
    ]
}
```

#### Complete Shopping List
```python
POST /api/shopping-lists/{id}/complete/
{
    "total_amount": 25.50,
    "items": [
        {
            "item_id": 1,
            "actual_quantity": 2.0,
            "unit_price": 3.75,
            "is_purchased": true
        }
    ]
}
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## License

[Add your license information here]

## Support

[Add contact information or support channels]