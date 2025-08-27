from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from Tracker.models import *
# from serializers import *
from .serializers import GroupSerializer, UserSerializer, TransactionSubtypeSerializer, TransactionSerializer, TransactionTypeSerializer


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
 