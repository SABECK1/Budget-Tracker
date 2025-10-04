# Personal Finance & Stock Portfolio Tracker

A comprehensive personal finance management application with integrated stock portfolio tracking, built with Django REST Framework and Vue.js. Track your income, expenses, investments, transfers, and stock holdings with real-time prices. Designed to work seamlessly with PYTR for importing Trade Republic transactions and providing complete overview of your financial portfolio!

## 🚀 Features

### Core Functionality
- **Transaction Management**: Add, edit, and categorize financial transactions (income, expenses, investments)
- **CSV Import**: Bulk import transactions from CSV files (optimized for Trade Republic transactions via PYTR)
- **Dashboard Analytics**: Visual overview of financial data with metrics cards
- **Category Organization**: Hierarchical transaction types and subtypes for detailed classification

### Stock Portfolio Tracking
- **Real-time Portfolio Calculation**: Automatic portfolio value updates with current stock prices
- **Stock Transaction Import**: Seamless import of buy/sell transactions from Trade Republic CSV
- **Holding Management**: Manual adjustment of share positions and purchase prices
- **Symbol Support**: Custom stock symbol mapping for unsupported ISINs
- **Profit/Loss Tracking**: Detailed P/L calculations across entire portfolio

## 🛠️ Tech Stack

### Backend
- **Django 4.x** - Web framework
- **Django REST Framework** - API development
- **SQLite** - Database (development)

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

5. **Setup transaction categories** 
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
### CSV Import Format

This project is made for use with PYTR. You should use the standard transactions.csv file you get by using dl_docs.

### API Endpoints

#### Authentication
- `POST /api/login/` - User login
- `POST /api/register/` - User registration
- `POST /api/logout/` - User logout
- `GET /api/set-csrf-token/` - Set CSRF token

#### Transactions
- `GET /api/transactions/` - List all transactions
- `POST /api/transactions/` - Create new transaction
- `GET /api/transactions/{id}/` - Get transaction details
- `PUT /api/transactions/{id}/` - Update transaction
- `DELETE /api/transactions/{id}/` - Delete transaction

#### Categories
- `GET /api/transactiontypes/` - List transaction types
- `GET /api/transactionsubtypes/` - List transaction subtypes

#### Portfolio & Holdings
- `GET /api/portfolio/` - Get current portfolio with holdings, market values, and P/L
- `POST /api/save-symbol/` - Save custom stock symbol for unsupported ISINs
- `POST /api/adjust-holding/` - Manually adjust stock positions and prices

#### User
- `GET /api/user/` - Get current user information

#### File Upload
- `POST /api/upload-csv/` - Upload CSV file for transaction import

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Django](https://www.djangoproject.com/) - The web framework
- [Vue.js](https://vuejs.org/) - The progressive JavaScript framework
- [PrimeVue](https://www.primefaces.org/primevue/) - UI component library
- [Django REST Framework](https://www.django-rest-framework.org/) - API framework

---

**Happy budgeting! 💰📊**
