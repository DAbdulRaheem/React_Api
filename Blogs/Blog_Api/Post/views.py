# posts/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Post
from .serializers import PostSerializer, PublicPostSerializer
from User.permissions import IsAdminUser, IsAuthor, IsAuthorOrAdmin

# --- Public APIs (No JWT Needed) ---

class PublicPostListView(generics.ListAPIView):
    """ GET /api/public/posts/ - Returns only APPROVED posts. """
    serializer_class = PublicPostSerializer
    permission_classes = [] # Publicly accessible

    def get_queryset(self):
        return Post.objects.filter(status='APPROVED')

class PublicPostDetailView(generics.RetrieveAPIView):
    """ GET /api/public/posts/{postId}/ - Fetch single APPROVED post. """
    serializer_class = PublicPostSerializer
    permission_classes = [] # Publicly accessible
    lookup_field = 'id'
    
    def get_object(self):
        # Fetch the object, ensuring it is APPROVED
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, id=self.kwargs.get(self.lookup_field))
        
        if obj.status != 'APPROVED':
            # Optionally raise a 404/403 for posts that exist but aren't approved
            # For simplicity matching public visibility, 404 is common for non-existent
            raise status.HTTP_404_NOT_FOUND
            
        return obj

# --- AUTHOR APIs (Requires JWT) ---

class AuthorPostListCreateView(generics.ListCreateAPIView):
    """ POST /api/posts/ (Create) & GET /api/posts/my-posts/ (List) """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self):
        # Only return posts for the authenticated user
        return Post.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        # Set the author to the current authenticated user. Status is PENDING by default.
        post = serializer.save(author=self.request.user)
        # Manually construct the response as per documentation
        response_data = {
            "message": "Post created and pending approval",
            "post": {
                "id": post.id,
                "title": post.title,
                "status": post.status
            }
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

class AuthorPostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """ PUT /api/posts/{postId}/ (Edit own) & DELETE /api/posts/{postId}/ (Delete own) & GET /api/posts/{postId}/ (Fetch single) """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    # Allows Admin to manage any post, or Author to manage own
    permission_classes = [IsAuthenticated, IsAuthorOrAdmin]
    lookup_field = 'id'

    def perform_update(self, serializer):
        post = serializer.save()
        # Manually construct the response as per documentation
        response_data = {
            "message": "Post updated successfully",
            "post": {
                "id": post.id,
                "title": post.title,
                "status": post.status
            }
        }
        return Response(response_data)
        
    def perform_destroy(self, instance):
        instance.delete()
        return Response({"message": "Your post has been deleted"}, status=status.HTTP_204_NO_CONTENT)

# --- ADMIN APIs (Requires JWT + Admin Role) ---

class AdminPendingPostListView(generics.ListAPIView):
    """ GET /api/admin/posts/pending/ - Returns all posts awaiting approval. """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        return Post.objects.filter(status='PENDING')

class AdminPostStatusUpdateView(generics.UpdateAPIView):
    """ PUT /api/admin/posts/{postId}/status/ - Approve or reject a post. """
    queryset = Post.objects.all()
    serializer_class = PostSerializer # Can use PostSerializer, but we'll override validation
    permission_classes = [IsAuthenticated, IsAdminUser]
    http_method_names = ['put']
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['APPROVED', 'REJECTED']:
            return Response({"detail": "Status must be 'APPROVED' or 'REJECTED'"}, status=status.HTTP_400_BAD_REQUEST)
        
        instance.status = new_status
        instance.save(update_fields=['status', 'updated_at'])
        
        return Response({
            "message": "Post status updated",
            "postId": instance.id,
            "status": instance.status
        }, status=status.HTTP_200_OK)

class AdminPostDeleteView(generics.DestroyAPIView):
    """ DELETE /api/admin/posts/{postId}/ - Admin deletes any post. """
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'id'
    
    def perform_destroy(self, instance):
        instance.delete()
        return Response({"message": "Post deleted successfully"}, status=status.HTTP_204_NO_CONTENT)