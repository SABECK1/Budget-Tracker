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

class TransactionSubtypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TransactionSubType
        fields = ['id', 'transaction_type','name','description']

class TransactionSerializer(serializers.HyperlinkedModelSerializer):
    transaction_subtype = serializers.PrimaryKeyRelatedField(
        queryset=models.TransactionSubType.objects.all()
    )

    class Meta:
        model = models.Transaction
        fields = ['id', 'transaction_subtype', 'amount', 'created_at', 'note', 'isin', 'quantity', 'fee', 'tax']
