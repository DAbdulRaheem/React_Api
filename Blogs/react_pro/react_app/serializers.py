from rest_framework import serializers
from .models import User, Post


# Basic User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role']


# Register Serializer
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'password']

    def create(self, validated_data): 
        user = User(
            name=validated_data['name'],
            email=validated_data['email'],
            role="AUTHOR"  # default role
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


# Login Serializer
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


# Post Serializer
class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)  # author should be readonly

    class Meta:
        model = Post
        fields = ["id", "title", "content", "author", "status", "created_at"]
        read_only_fields = ["author", "status", "created_at"]
