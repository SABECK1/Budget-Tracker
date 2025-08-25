from django.contrib.auth.models import Group, User
from Tracker import models
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class TransactionSubtypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.TransactionSubType
        fields = ['name','description']

class TransactionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Transaction
        fields = ['transaction_subtype','amount','created_at','note']

