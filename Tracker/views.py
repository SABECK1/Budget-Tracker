from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from Tracker.models import *
# from serializers import *
from .serializers import GroupSerializer, UserSerializer, TransactionSubtypeSerializer, TransactionSerializer


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