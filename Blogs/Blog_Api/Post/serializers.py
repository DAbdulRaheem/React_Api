# posts/serializers.py
from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ('id', 'title', 'content', 'author', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'author', 'status', 'created_at', 'updated_at')

    def get_author(self, obj):
        # Return the author's name
        return obj.author.name
    
    def create(self, validated_data):
        # The author is set in the view based on the authenticated user
        return Post.objects.create(**validated_data)

class PublicPostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ('id', 'title', 'content', 'author', 'created_at')
        
    def get_author(self, obj):
        return obj.author.name