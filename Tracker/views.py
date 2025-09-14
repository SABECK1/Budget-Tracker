from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from Tracker.models import *
# from serializers import *
from .serializers import GroupSerializer, UserSerializer, TransactionSubtypeSerializer, TransactionSerializer, TransactionTypeSerializer, CSVUploadSerializer
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .models import Transaction
import io
import csv
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
import json

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from .forms import CreateUserForm
from django.db import models
from django.db.models import Sum, F, Case, When
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .API.stocks import get_symbol_for_isin


class CSVUploadView(APIView):
    serializer_class = CSVUploadSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_transaction_subtype(self, is_stock: bool, amount: float):
        try:
            if not is_stock:  # ISIN empty
                if amount < 0:
                    return TransactionSubType.objects.get(name="Outflow") # Regular expense
                else:
                    return TransactionSubType.objects.get(name="Inflow") # Regular income
            else:  # ISIN present
                if amount < 0:
                    return TransactionSubType.objects.get(name="Buy") # Savings for stocks
                else:
                    return TransactionSubType.objects.get(name="Sell") # Income from Stocks
        except TransactionSubType.DoesNotExist:
            # Fallback to "Not assigned" subtype if specific ones don't exist
            return TransactionSubType.objects.get(name="Not assigned")

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

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
                amount_lookup = 'amount__gt' if amount > 0 else 'amount__lt'
                existing_transaction = Transaction.objects.filter(
                    user=request.user,
                    isin=isin,
                     **{amount_lookup: 0}
                ).exclude(transaction_subtype__isnull=True).first()
                if existing_transaction:
                    transaction_subtype = existing_transaction.transaction_subtype
            elif note:
                existing_transaction = Transaction.objects.filter(
                    user=request.user,
                    note=note
                ).exclude(transaction_subtype__isnull=True).first()
                if existing_transaction:
                    transaction_subtype = existing_transaction.transaction_subtype

            Transaction.objects.create(
                user=request.user,
                created_at=row[0],
                transaction_subtype=transaction_subtype,
                amount=amount,
                note=note,
                isin=row[4] if len(row) > 4 and row[4] else "",
                quantity=float(row[5]) if len(row) > 5 and row[5] else float(0.0),
                fee=float(row[6]) if len(row) > 6 and row[6] else float(0.0),
                tax=float(row[7]) if len(row) > 7 and row[7] else float(0.0),
            )
            created_count += 1

        return Response({"status": f"Imported {created_count} rows"}, status=status.HTTP_201_CREATED)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class TransactionSubtypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Subtypes of Transactions to be edited
    """
    queryset = TransactionSubType.objects.all().order_by('name')
    serializer_class = TransactionSubtypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Subtypes of Transactions to be edited
    """
    queryset = Transaction.objects.all().order_by('created_at')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user).order_by('created_at')

        # Filter by transaction_subtype if provided
        subtype_id = self.request.query_params.get('transaction_subtype', None)
        if subtype_id is not None:
            queryset = queryset.filter(transaction_subtype=subtype_id)

        return queryset

    @action(detail=False, methods=['patch'])
    def bulk_update_by_note(self, request):
        note = request.data.get('note')
        transaction_subtype_id = request.data.get('transaction_subtype')

        if not note or not transaction_subtype_id:
            return Response({"error": "Note and transaction_subtype are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction_subtype = TransactionSubType.objects.get(id=transaction_subtype_id)
        except TransactionSubType.DoesNotExist:
            return Response({"error": "Invalid transaction_subtype"}, status=status.HTTP_400_BAD_REQUEST)

        # Update all transactions for the current user with the same note
        updated_count = Transaction.objects.filter(
            user=request.user,
            note=note
        ).update(transaction_subtype=transaction_subtype)

        return Response({"updated_count": updated_count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'])
    def bulk_update_by_isin(self, request):
        isin = request.data.get('isin')
        is_buy = request.data.get('is_buy')
        transaction_subtype_id = request.data.get('transaction_subtype')

        if not isin or not transaction_subtype_id:
            return Response({"error": "ISIN and transaction_subtype are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaction_subtype = TransactionSubType.objects.get(id=transaction_subtype_id)
        except TransactionSubType.DoesNotExist:
            return Response({"error": "Invalid transaction_subtype"}, status=status.HTTP_400_BAD_REQUEST)

        # Update all transactions for the current user with the same ISIN
        amount_lookup = 'amount__gt' if is_buy else 'amount__lt'
        updated_count = Transaction.objects.filter(
            user=request.user,
            isin=isin,
            **{amount_lookup: 0}
        ).update(transaction_subtype=transaction_subtype)

        return Response({"updated_count": updated_count}, status=status.HTTP_200_OK)


class TransactionTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction Types (Income/Expense categories) to be viewed or edited.
    """
    queryset = TransactionType.objects.all().order_by('name')
    serializer_class = TransactionTypeSerializer
    permission_classes = [permissions.IsAuthenticated]



@require_http_methods(['GET'])
@ensure_csrf_cookie
def portfolio_view(request):
    """
    Calculate portfolio holdings from transactions.
    Only show stocks where net quantity > 0 (buys and sells don't cancel out completely).
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    # Group transactions by ISIN and calculate net quantities
    holdings = Transaction.objects.filter(
        user=request.user,
        isin__isnull=False
    ).exclude(isin='').values('isin').annotate(
        net_quantity=Sum(F('quantity') * 
            Case(
                When(transaction_subtype__name="Sell", then=-1),
                When(transaction_subtype__name="Buy", then=1),
                default=1,
                output_field=models.FloatField()
            ),
            output_field=models.FloatField()),
        # Via CSV import, buys are negative amounts (money going out), sells positive (money coming in)
        # So we multiply by -1 to get the actual invested amount, buying is now positive and selling negative
        total_invested=Sum(
            F('amount') * -1
        )
    ).filter(net_quantity__gt=0.01)


    # Format the response
    portfolio_data = []
    total_value = 0

    for holding in holdings:
        # Calculate average price from total invested / net quantity
        net_quantity = holding['net_quantity']
        total_invested = abs(holding['total_invested']) or 0
        avg_price = float(total_invested) / float(net_quantity) if net_quantity > 0 else 0

        # For now, we'll use the average price as current price (in a real app, you'd fetch current prices)
        current_price = avg_price
        value = float(net_quantity) * current_price
        total_value += value

        # Get symbol for the ISIN
        symbol_info = get_symbol_for_isin(holding['isin'], request.user) or {}
        symbol = symbol_info.get('symbol', 'Not found')
        name = symbol_info.get('name', 'Not found')

        portfolio_data.append({
            'name': name,
            'symbol': symbol,
            'isin': holding['isin'],
            'shares': float(net_quantity),
            'avg_price': float(avg_price),
            'current_price': float(current_price),
            'value': float(value),
            'total_invested': float(total_invested),
        })

    return JsonResponse({
        'holdings': portfolio_data,
        'total_value': float(total_value),
        'total_gain_loss': 0,  # Would need current prices to calculate
        'holdings_count': len(portfolio_data)
    }, status=status.HTTP_200_OK)
 
@ensure_csrf_cookie
@require_http_methods(['GET'])
def set_csrf_token(request):
    """
    We set the CSRF cookie on the frontend.
    """
    return JsonResponse({'message': 'CSRF cookie set'})
 
@require_http_methods(['POST'])
def login_view(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data['email']
        password = data['password']
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'message': 'Invalid JSON'}, status=400
        )
 
    user = authenticate(request, username=email, password=password)
 
    if user:
        login(request, user)
        return JsonResponse({'success': True})
    return JsonResponse(
        {'success': False, 'message': 'Invalid credentials'}, status=401
    )
 
def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logged out'})
 
@require_http_methods(['GET'])
def user(request):
    if request.user.is_authenticated:
        return JsonResponse(
            {'username': request.user.username, 'email': request.user.email}
        )
    return JsonResponse(
        {'message': 'Not logged in'}, status=401
    )
 
@require_http_methods(['POST'])
@ensure_csrf_cookie
def save_symbol(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        data = json.loads(request.body.decode('utf-8'))
        isin = data.get('isin')
        symbol = data.get('symbol')
        name = data.get('name', '')

        if not isin or not symbol:
            return JsonResponse({"error": "ISIN and symbol are required"}, status=400)

        # Check if already exists for this user
        existing = UserProvidedSymbol.objects.filter(user=request.user, isin=isin).first()
        if existing:
            existing.symbol = symbol
            existing.name = name
            existing.save()
        else:
            UserProvidedSymbol.objects.create(
                user=request.user,
                isin=isin,
                symbol=symbol,
                name=name
            )

        return JsonResponse({"message": "Symbol saved successfully"}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(['POST'])
def register(request):
    data = json.loads(request.body.decode('utf-8'))
    form = CreateUserForm(data)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': 'User registered successfully'}, status=201)
    else:
        errors = form.errors.as_json()
        return JsonResponse({'error': errors}, status=400)
