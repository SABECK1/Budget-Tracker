from django.contrib.auth.models import Group, User
from Tracker import models
from rest_framework import serializers

# serializers.py
from rest_framework import serializers

class CSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    class Meta:
        fields = ['file']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class TransactionTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.TransactionType
        fields = ['url', 'id', 'name', 'description', 'expense_factor']

class TransactionSubtypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.TransactionSubType
        fields = ['transaction_type','name','description']

class TransactionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Transaction
        fields = ['transaction_subtype','amount','created_at','note']

