# Budget Tracker

A comprehensive personal finance management application built with Django REST Framework and Vue.js. Track your income, expenses, investments, and transfers with an intuitive dashboard interface. Made to work with PYTR to give you the best overview over your Trade Republic transactions!

## 🚀 Features

### Core Functionality
- **Transaction Management**: Add, edit, and categorize financial transactions
- **CSV Import**: Bulk import transactions from CSV files
- **Dashboard Analytics**: Visual overview of financial data with metrics cards
- **Category Organization**: Hierarchical transaction types and subtypes
- **Real-time Updates**: Automatic data refresh after operations

### Transaction Categories
- **Income**: Salary, Freelance, Business Income, Investment Returns, Rental Income
- **Expense**: Food & Dining, Transportation, Housing, Utilities, Healthcare, Entertainment, Shopping, Education, Travel, Insurance, Personal Care
- **Investment**: Stocks, Bonds, Mutual Funds, ETFs, Cryptocurrency, Real Estate, Retirement Accounts
- **Transfer**: Bank Transfers, Credit Card Payments, Account Transfers, Wire Transfers
- **Not Assigned**: Default category for uncategorized transactions

## 🛠️ Tech Stack

### Backend
- **Django 4.x** - Web framework
- **Django REST Framework** - API development
- **SQLite** - Database (development)
- **JWT Authentication** - Secure user authentication

### Frontend
- **Vue.js 3** - Progressive JavaScript framework
- **PrimeVue** - UI component library
- **Axios** - HTTP client for API calls
- **Vue Router** - Client-side routing

## 📋 Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

## 🔧 Installation & Setup

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/SABECK1/Budget-Tracker.git
   cd Budget-Tracker
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Setup transaction categories** (optional)
   ```bash
   python setup_transaction_types.py
   ```

6. **Create superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Django server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd tracker_vue
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment** (create .env file)
   ```env
   VUE_APP_API_BASE_URL=http://localhost:8000/api
   ```

4. **Start development server**
   ```bash
   npm run serve
   ```

## 🚀 Usage

### Accessing the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin

### CSV Import Format

This project is made for use with PYTR. You should use the standard transactions.csv file you get by using dl_docs.

### API Endpoints

#### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/logout/` - User logout

#### Transactions
- `GET /api/transactions/` - List all transactions
- `POST /api/transactions/` - Create new transaction
- `GET /api/transactions/{id}/` - Get transaction details
- `PUT /api/transactions/{id}/` - Update transaction
- `DELETE /api/transactions/{id}/` - Delete transaction

#### Categories
- `GET /api/transactiontypes/` - List transaction types
- `GET /api/transactionsubtypes/` - List transaction subtypes

#### File Upload
- `POST /api/upload-csv/` - Upload CSV file

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Django](https://www.djangoproject.com/) - The web framework
- [Vue.js](https://vuejs.org/) - The progressive JavaScript framework
- [PrimeVue](https://www.primefaces.org/primevue/) - UI component library
- [Django REST Framework](https://www.django-rest-framework.org/) - API framework

---

**Happy budgeting! 💰📊**
