# Create your views here.
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from Tracker.models import TransactionType, TransactionSubType, UserProvidedSymbol, BankAccount
from .serializers import (
    GroupSerializer,
    UserSerializer,
    TransactionSubtypeSerializer,
    TransactionSerializer,
    TransactionTypeSerializer,
    CSVUploadSerializer,
    BankAccountSerializer,
)
from datetime import datetime
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .models import Transaction
import io
import csv
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from .forms import CreateUserForm
from django.db import models
from django.db.models import Sum, F, Case, When
from .stocks import get_history, fetch_multiple_prices, get_symbol_and_industry
import asyncio



class CSVUploadView(APIView):
    serializer_class = CSVUploadSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_transaction_subtype(self, is_stock: bool, amount: float):
        try:
            if not is_stock:  # ISIN empty
                if amount < 0:
                    return TransactionSubType.objects.get(
                        name="Outflow"
                    )  # Regular expense
                else:
                    return TransactionSubType.objects.get(
                        name="Inflow"
                    )  # Regular income
            else:  # ISIN present
                if amount < 0:
                    return TransactionSubType.objects.get(
                        name="Stock/ETF/Bond Purchase"
                    )  # Savings for stocks
                else:
                    return TransactionSubType.objects.get(
                        name="Investment Returns"
                    )  # Income from Stocks
        except TransactionSubType.DoesNotExist:
            # Fallback to "Not assigned" subtype if specific ones don't exist
            return TransactionSubType.objects.get(name="Not assigned")

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = CSVUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        csv_file = serializer.validated_data["file"]
        data = csv_file.read().decode("utf-8")
        io_string = io.StringIO(data)
        reader = csv.reader(io_string, delimiter=";")

        # Skip header row manually
        next(reader, None)

        created_count = 0
        for row in reader:
            if not row:  # skip empty lines
                continue
            # Check if ISIN is present and not empty to determine if it's a stock transaction
            isin = row[4] if len(row) > 4 and row[4] else ""
            is_stock = bool(isin)
            amount = float(row[2]) if row[2] else float(0.0)
            note = row[3] if len(row) > 3 and row[3] else ""

            # Default subtype based on amount and ISIN
            transaction_subtype = self.get_transaction_subtype(is_stock, amount)

            # For stock transactions, check for existing transaction with same ISIN
            # For regular transactions, check for existing transaction with same note
            if is_stock and isin:
                amount_lookup = "amount__gt" if amount > 0 else "amount__lt"
                existing_transaction = (
                    Transaction.objects.filter(
                        user=request.user, isin=isin, **{amount_lookup: 0}
                    )
                    .exclude(transaction_subtype__isnull=True)
                    .first()
                )
                if existing_transaction:
                    transaction_subtype = existing_transaction.transaction_subtype
            elif note:
                existing_transaction = (
                    Transaction.objects.filter(user=request.user, note=note)
                    .exclude(transaction_subtype__isnull=True)
                    .first()
                )
                if existing_transaction:
                    transaction_subtype = existing_transaction.transaction_subtype

            #Convert row[0] to timezone-aware datetime
            datetime_from_iso = datetime.fromisoformat(row[0])
            creation_datetime = timezone.make_aware(datetime_from_iso)

            # Helper function to safely convert to float
            def safe_float(value):
                try:
                    return float(value) if value else 0.0
                except (ValueError, TypeError):
                    return 0.0

            Transaction.objects.create(
                user=request.user,
                created_at=creation_datetime,
                transaction_subtype=transaction_subtype,
                amount=amount,
                note=note,
                isin=row[4] if len(row) > 4 and row[4] else "",
                quantity=safe_float(row[5] if len(row) > 5 else None),
                fee=safe_float(row[6] if len(row) > 6 else None),
                tax=safe_float(row[7] if len(row) > 7 else None),
            )
            created_count += 1

        return Response(
            {"status": f"Imported {created_count} rows"}, status=status.HTTP_201_CREATED
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class TransactionSubtypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Subtypes of Transactions to be edited
    """

    queryset = TransactionSubType.objects.all().order_by("name")
    serializer_class = TransactionSubtypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Subtypes of Transactions to be edited
    """

    queryset = Transaction.objects.all().order_by("created_at")
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user).order_by(
            "created_at"
        )

        # Filter by transaction_subtype if provided
        subtype_id = self.request.query_params.get("transaction_subtype", None)
        if subtype_id is not None:
            queryset = queryset.filter(transaction_subtype=subtype_id)

        return queryset

    @action(detail=False, methods=["patch"])
    def bulk_update_by_note(self, request):
        note = request.data.get("note")
        transaction_subtype_id = request.data.get("transaction_subtype")

        if not note or not transaction_subtype_id:
            return Response(
                {"error": "Note and transaction_subtype are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transaction_subtype = TransactionSubType.objects.get(
                id=transaction_subtype_id
            )
        except TransactionSubType.DoesNotExist:
            return Response(
                {"error": "Invalid transaction_subtype"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update all transactions for the current user with the same note
        updated_count = Transaction.objects.filter(user=request.user, note=note).update(
            transaction_subtype=transaction_subtype
        )

        return Response({"updated_count": updated_count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["patch"])
    def bulk_update_by_isin(self, request):
        isin = request.data.get("isin")
        is_buy = request.data.get("is_buy")
        transaction_subtype_id = request.data.get("transaction_subtype")

        if not isin or not transaction_subtype_id:
            return Response(
                {"error": "ISIN and transaction_subtype are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transaction_subtype = TransactionSubType.objects.get(
                id=transaction_subtype_id
            )
        except TransactionSubType.DoesNotExist:
            return Response(
                {"error": "Invalid transaction_subtype"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update all transactions for the current user with the same ISIN
        amount_lookup = "amount__gt" if is_buy else "amount__lt"
        updated_count = Transaction.objects.filter(
            user=request.user, isin=isin, **{amount_lookup: 0}
        ).update(transaction_subtype=transaction_subtype)

        return Response({"updated_count": updated_count}, status=status.HTTP_200_OK)


class BankAccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Bank Accounts to be viewed or edited.
    """

    queryset = BankAccount.objects.all().order_by("name")
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return BankAccount.objects.filter(user=self.request.user).order_by("name")


class TransactionTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction Types (Income/Expense categories) to be viewed or edited.
    """

    queryset = TransactionType.objects.all().order_by("name")
    serializer_class = TransactionTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


@require_http_methods(["GET"])
@ensure_csrf_cookie
def portfolio_view(request):
    """
    Calculate portfolio holdings from transactions.
    Only show stocks where net quantity > 0 (buys and sells don't cancel out completely).
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED
        )

    # Group transactions by ISIN and calculate net quantities
    holdings = (
        Transaction.objects.filter(user=request.user, isin__isnull=False)
        .exclude(isin="")
        .values("isin")
        .annotate(
            net_quantity=Sum(
                F("quantity")
                * Case(
                    When(transaction_subtype__name="Investment Returns", then=-1),
                    When(transaction_subtype__name="Stock/ETF/Bond Purchase", then=1),
                    default=1,
                    output_field=models.FloatField(),
                ),
                output_field=models.FloatField(),
            ),
            # Via CSV import, buys are negative amounts (money going out), sells positive (money coming in)
            # So we multiply by -1 to get the actual invested amount, buying is now positive and selling negative
            total_invested=Sum(F("amount") * -1),
        )
        .filter(net_quantity__gt=0.01)
    )

    # Get list of ISINs for concurrent fetching
    isins = [holding["isin"] for holding in holdings]

    # Fetch all prices concurrently
    try:
        price_data = asyncio.run(fetch_multiple_prices(isins, max_concurrent=5))
    except Exception as e:
        print(f"Error in concurrent fetching: {e}")
        
        # Fallback to synchronous fetching
        price_data = {}
        for isin in isins:
            try:
                name, intraday_data = get_history(isin)
                if intraday_data and len(intraday_data) > 0:
                    current_price = float(intraday_data[-1][1])
                    price_data[isin] = {
                        'isin': isin,
                        'name': name,
                        'current_price': current_price,
                        'success': True
                    }
                else:
                    price_data[isin] = {
                        'isin': isin,
                        'name': f"Unknown ({isin})",
                        'current_price': None,
                        'success': False
                    }
            except Exception as e2:
                print(f"Error fetching price for {isin}: {e2}")
                price_data[isin] = {
                    'isin': isin,
                    'name': f"Error ({isin})",
                    'current_price': None,
                    'success': False
                }

    # Format the response using the fetched price data
    portfolio_data = []
    total_value = 0
    total_invested_sum = 0

    for holding in holdings:
        # Calculate average price from total invested / net quantity
        net_quantity = holding["net_quantity"]
        total_invested = abs(holding["total_invested"]) or 0
        avg_price = (
            float(total_invested) / float(net_quantity) if net_quantity > 0 else 0
        )
        isin = holding["isin"]

        # Get price data from concurrent fetch
        price_info = price_data.get(isin)
        if price_info and price_info['success'] and price_info['current_price']:
            current_price = price_info['current_price']
            name = price_info['name']
            intraday_data = price_info.get('intraday_data', [])
            preday = price_info.get('preday', [])
            history = price_info.get('history_data', [])
            industry = price_info.get('industry', 'Unknown')
            sector = price_info.get('sector', 'Unknown')
        else:
            # Fallback to avg_price if concurrent fetch failed
            current_price = avg_price
            name = f"Unknown ({isin})"
            intraday_data = []
            preday = []
            history = []
            # Try to get industry even in fallback
            symbol_info = get_symbol_and_industry(isin)
            industry = symbol_info.get('industry', 'Unknown')
            sector = symbol_info.get('sector', 'Unknown')

        # Get transaction data for this holding to show on chart
        transactions = Transaction.objects.filter(user=request.user, isin=isin).order_by('created_at')
        transaction_points = []
        for transaction in transactions:
            if transaction.quantity and transaction.amount and transaction.quantity != 0:
                # Calculate transaction price
                transaction_price = abs(float(transaction.amount) / float(transaction.quantity))

                # Convert to unix timestamp
                transaction_timestamp = int(transaction.created_at.timestamp() * 1000)

                transaction_points.append({
                    'timestamp': transaction_timestamp,
                    'price': transaction_price,
                    'type': transaction.transaction_subtype.name,
                    'quantity': float(transaction.quantity)
                })

        value = float(net_quantity) * current_price
        total_value += value
        total_invested_sum += float(total_invested)
        portfolio_data.append(
            {
                "name": name,
                "isin": holding["isin"],
                "shares": float(net_quantity),
                "avg_price": float(avg_price),
                "current_price": float(current_price),
                "value": float(value),
                "total_invested": float(total_invested),
                "intraday_data": intraday_data,
                "preday": preday,
                "history": history,
                "transactions": transaction_points,
                "industry": industry,
                "sector": sector
            }
        )

    # Calculate total gain/loss percentage
    total_gain_loss = (
        ((total_value - total_invested_sum) / total_invested_sum * 100)
        if total_invested_sum > 0
        else 0
    )
    return JsonResponse(
        {
            "holdings": portfolio_data,
            "total_value": float(total_value),
            "total_gain_loss": float(total_gain_loss),
            "holdings_count": len(portfolio_data),
        },
        status=status.HTTP_200_OK,
    )


@ensure_csrf_cookie
@require_http_methods(["GET"])
def set_csrf_token(request):
    """
    We set the CSRF cookie on the frontend.
    """
    return JsonResponse({"message": "CSRF cookie set"})


@require_http_methods(["POST"])
def login_view(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        email = data["email"]
        password = data["password"]
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    user = authenticate(request, username=email, password=password)

    if user:
        login(request, user)
        return JsonResponse({"success": True})
    return JsonResponse(
        {"success": False, "message": "Invalid credentials"}, status=401
    )


def logout_view(request):
    logout(request)
    return JsonResponse({"message": "Logged out"})


@require_http_methods(["GET"])
def user(request):
    if request.user.is_authenticated:
        return JsonResponse(
            {"username": request.user.username, "email": request.user.email}
        )
    return JsonResponse({"message": "Not logged in"}, status=401)


@require_http_methods(["POST"])
@ensure_csrf_cookie
def save_symbol(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        data = json.loads(request.body.decode("utf-8"))
        isin = data.get("isin")
        symbol = data.get("symbol")
        name = data.get("name", "")

        if not isin or not symbol:
            return JsonResponse({"error": "ISIN and symbol are required"}, status=400)

        # Check if already exists for this user
        existing = UserProvidedSymbol.objects.filter(
            user=request.user, isin=isin
        ).first()
        if existing:
            existing.symbol = symbol
            existing.name = name
            existing.save()
        else:
            UserProvidedSymbol.objects.create(
                user=request.user, isin=isin, symbol=symbol, name=name
            )

        return JsonResponse({"message": "Symbol saved successfully"}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
@ensure_csrf_cookie
def adjust_holding_view(request):
    """
    Adjust the shares of a holding by creating a buy or sell transaction.
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        print("Adjust holding request body:", request.body)
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        isin = data.get("isin")
        new_shares = float(data.get("new_shares", 0))
        current_price = float(data.get("current_price", 0))
        note = data.get("note", "Adjusted holding manually")

        # Additional validation
        if "new_shares" not in data:
            return JsonResponse({"error": "new_shares is required"}, status=400)
        if "current_price" not in data:
            return JsonResponse({"error": "current_price is required"}, status=400)

        if not isin:
            return JsonResponse({"error": "ISIN is required"}, status=400)

        if new_shares < 0:
            return JsonResponse({"error": "Shares cannot be negative"}, status=400)

        # Calculate current net quantity for the holding
        current_holding = Transaction.objects.filter(
            user=request.user, isin=isin
        ).aggregate(
            net_quantity=Sum(
                F("quantity")
                * Case(
                    When(transaction_subtype__name="Investment Returns", then=-1),
                    When(transaction_subtype__name="Stock/ETF/Bond Purchase", then=1),
                    default=1,
                    output_field=models.FloatField(),
                ),
                output_field=models.FloatField(),
            )
        )

        # print("Current holding:", current_holding[0])

        if not current_holding or current_holding["net_quantity"] is None:
            current_net_quantity = 0
        else:
            current_net_quantity = current_holding["net_quantity"]

        # Calculate difference
        shares_difference = new_shares - current_net_quantity
        print(shares_difference, new_shares, current_net_quantity)
        if shares_difference == 0:
            return JsonResponse({"message": "No change in shares"}, status=200)

        # Determine transaction type
        if shares_difference > 0:
            # Buy additional shares
            transaction_subtype = TransactionSubType.objects.get(name="Stock/ETF/Bond Purchase")
            amount = -(
                abs(shares_difference) * current_price
            )  # Negative for money going out
            quantity = abs(shares_difference)
        else:
            # Sell shares
            transaction_subtype = TransactionSubType.objects.get(name="Investment Returns")
            amount = (
                abs(shares_difference) * current_price
            )  # Positive for money coming in
            quantity = abs(shares_difference)

        # Create the transaction
        Transaction.objects.create(
            user=request.user,
            transaction_subtype=transaction_subtype,
            amount=amount,
            note=note,
            isin=isin,
            quantity=quantity,
            fee=0,  # No fees for manual adjustments
            tax=0,  # No tax for manual adjustments
        )

        return JsonResponse({"message": "Holding adjusted successfully"}, status=200)

    except json.JSONDecodeError as e:
        return JsonResponse({"error": f"Invalid JSON {e}"}, status=400)
    except TransactionSubType.DoesNotExist:
        return JsonResponse(
            {"error": "Required transaction subtypes not found"}, status=500
        )
    # except Exception as e:
    # return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
def register(request):
    data = json.loads(request.body.decode("utf-8"))
    form = CreateUserForm(data)
    if form.is_valid():
        form.save()
        return JsonResponse({"success": "User registered successfully"}, status=201)
    else:
        errors = form.errors.as_json()
        return JsonResponse({"error": errors}, status=400)
