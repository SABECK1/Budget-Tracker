from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
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
            is_stock = bool(row[4] if len(row) > 4 else False)
            amount = float(row[2]) if row[2] else float(0.0)

            Transaction.objects.create(
                user=request.user,
                created_at=row[0],
                transaction_subtype=self.get_transaction_subtype(is_stock, amount),
                amount=amount,
                note=row[3] if len(row) > 3 and row[3] else "",
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


class TransactionTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction Types (Income/Expense categories) to be viewed or edited.
    """
    queryset = TransactionType.objects.all().order_by('name')
    serializer_class = TransactionTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
import json
 
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from .forms import CreateUserForm
 
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
def register(request):
    data = json.loads(request.body.decode('utf-8'))
    form = CreateUserForm(data)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': 'User registered successfully'}, status=201)
    else:
        errors = form.errors.as_json()
        return JsonResponse({'error': errors}, status=400)
