# users/views.py
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
# Assuming you have an IsAdminUser permission class
from User.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics

from .serializers import UserRegistrationSerializer, UserSerializer, UserRoleUpdateSerializer
from .models import User
from .permissions import IsAdminUser

# Helper function to generate JWT
def get_jwt_token(user):
    payload = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'exp': datetime.now() + timedelta(seconds=settings.JWT_EXPIRATION_DELTA),
        'iat': datetime.now()
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

# --- Auth APIs (No JWT Required) ---

@api_view(['POST'])
@csrf_exempt
def register_user(request):
    """ POST /api/auth/register/ """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Ensure the response adheres to the documentation
        response_data = {
            "message": "User registered successfully",
            "user": UserSerializer(user).data
        }
        # Remove created_at from the final response object structure
        del response_data['user']['created_at']
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
def login_user(request):
    """ POST /api/auth/login/ """
    email = request.data.get('email')
    password = request.data.get('password')
    
    user = authenticate(email=email, password=password)

    if user is not None:
        token = get_jwt_token(user)
        # Ensure the response adheres to the documentation
        user_data = UserSerializer(user).data
        del user_data['created_at']
        
        response_data = {
            "message": "Login successful",
            "token": token,
            "role":user.role,
            "user": user_data
        }
        # print(user.role)
        return Response(response_data)
    else:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

# --- Admin APIs (Requires JWT + Admin Role) ---

class AdminUserListView(generics.ListAPIView):
    """ GET /api/admin/users/ """
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
class AdminUserRoleUpdateView(generics.UpdateAPIView):
    """ PUT /api/admin/users/{id}/role/ """
    queryset = User.objects.all()
    serializer_class = UserRoleUpdateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    http_method_names = ['put'] # Only allow PUT
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_role = serializer.validated_data['role']
        instance.role = new_role
        instance.save()
        
        return Response({
            "message": "Role updated successfully",
            "userId": instance.id,
            "newRole": new_role
        }, status=status.HTTP_200_OK)
        
class UserCountView(APIView):
    """ GET /api/admin/users/count/ - Returns the total user count. """
    permission_classes = [IsAuthenticated, IsAdminUser] # Restrict to logged-in Admins

    def get(self, request, format=None):
        User = get_user_model()
        # Count all users
        user_count = User.objects.count() 
        
        return Response({
            "total_users": user_count
        }) 
    
class AdminUserListView(generics.ListAPIView):
    """ GET /api/admin/users/ """
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]