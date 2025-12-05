import json
import datetime
import jwt

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import User, Post
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer, PostSerializer

# Constants
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


# -------------------------------------------------
# JWT HELPERS
# -------------------------------------------------
def generate_token(user):
    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None


def auth_required(view_func):
    def wrapper(request, *args, **kwargs):
        token = get_token(request)
        if not token:
            return JsonResponse({"error": "Authorization missing"}, status=401)

        payload = decode_token(token)
        if not payload:
            return JsonResponse({"error": "Invalid or expired token"}, status=401)

        try:
            # Attach the authenticated user object to the request
            request.user = User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

        return view_func(request, *args, **kwargs)

    wrapper.__name__ = view_func.__name__
    return wrapper


def role_required(roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                return JsonResponse({"error": "Permission denied"}, status=403)
            return view_func(request, *args, **kwargs)

        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorator


# -------------------------------------------------
# AUTH APIs
# -------------------------------------------------
@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """Allows public registration (defaults to AUTHOR role)."""
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    serializer = RegisterSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    # All new users are registered as AUTHOR by default
    user = serializer.save(role="AUTHOR") 

    return JsonResponse(
        {"message": "User created successfully", "user": UserSerializer(user).data},
        status=201,
    )


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """Handles user login for all roles and issues a JWT token."""
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    serializer = LoginSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    if not user.check_password(password):
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    token = generate_token(user)

    return JsonResponse(
        {"message": "Login successful", "access": token, "user": UserSerializer(user).data}
    )


# -------------------------------------------------
# PUBLIC POSTS (VIEWER Role)
# -------------------------------------------------
@csrf_exempt
@require_http_methods(["GET"])
def public_posts(request):
    """Lists all APPROVED posts (accessible by anyone, including VIEWERS)."""
    posts = Post.objects.filter(status="APPROVED").order_by("-created_at")
    serializer = PostSerializer(posts, many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@require_http_methods(["GET"])
def public_post_detail(request, post_id):
    """Gets details for a single APPROVED post."""
    post = get_object_or_404(Post, id=post_id, status="APPROVED")
    serializer = PostSerializer(post)
    return JsonResponse(serializer.data)


# -------------------------------------------------
# AUTHOR APIs (AUTHOR, ADMIN Role)
# -------------------------------------------------
@csrf_exempt
@auth_required
@role_required(["AUTHOR", "ADMIN"])
@require_http_methods(["POST"])
def create_post(request):
    """Allows AUTHOR/ADMIN to create a new post."""
    try:
        data = json.loads(request.body)
        title = data.get("title")
        content = data.get("content")
        if not title or not content:
            return JsonResponse({"error": "title and content required"}, status=400)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    serializer = PostSerializer(data=data)
    if serializer.is_valid():
        # Set the author and initial status
        post = serializer.save(author=request.user, status="APPROVED")  # Use "PENDING" for review flow
        return JsonResponse({
            "message": "Post created",
            "post": PostSerializer(post).data
        }, status=201)

    return JsonResponse(serializer.errors, status=400)


@csrf_exempt
@auth_required
@role_required(["AUTHOR", "ADMIN"])
@require_http_methods(["PUT"])
def edit_post(request, post_id):
    """Allows AUTHOR to edit their own post, or ADMIN to edit any post."""
    post = get_object_or_404(Post, id=post_id)

    # Permission Check: Must be the author or an ADMIN
    if request.user.role != "ADMIN" and post.author_id != request.user.id:
        return JsonResponse({"error": "Permission denied"}, status=403)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    serializer = PostSerializer(post, data=data, partial=True)
    if serializer.is_valid():
        # Force status change to PENDING on edit for review
        updated = serializer.save(status="PENDING", updated_at=timezone.now()) 
        return JsonResponse({"message": "Post updated", "post": PostSerializer(updated).data})

    return JsonResponse(serializer.errors, status=400)


@csrf_exempt
@auth_required
@role_required(["AUTHOR", "ADMIN"])
@require_http_methods(["DELETE"])
def delete_post(request, post_id):
    """Allows AUTHOR to delete their own post, or ADMIN to delete any post."""
    post = get_object_or_404(Post, id=post_id)

    # Permission Check: Must be the author or an ADMIN
    if request.user.role != "ADMIN" and post.author_id != request.user.id:
        return JsonResponse({"error": "Permission denied"}, status=403)

    post.delete()
    return JsonResponse({"message": "Post deleted"})


# -------------------------------------------------
# ADMIN APIs (ADMIN Role)
# -------------------------------------------------
@csrf_exempt
@auth_required
@role_required(["ADMIN"])
@require_http_methods(["GET"])
def admin_list_users(request):
    """ADMIN endpoint to list all users."""
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@auth_required
@role_required(["ADMIN"])
@require_http_methods(["PUT"])
def admin_update_user_role(request, user_id):
    """ADMIN endpoint to change a user's role (e.g., promote to ADMIN)."""
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user = get_object_or_404(User, id=user_id)
    role = data.get("role")

    if role not in ["ADMIN", "AUTHOR", "VIEWER"]:
        return JsonResponse({"error": "Invalid role"}, status=400)

    user.role = role
    user.save()

    return JsonResponse({"message": "Role updated", "user": UserSerializer(user).data})


@csrf_exempt
@auth_required
@role_required(["ADMIN"])
@require_http_methods(["PUT"])
def admin_update_post_status(request, post_id):
    """ADMIN endpoint to approve/reject a post (change its status)."""
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    post = get_object_or_404(Post, id=post_id)
    status_val = data.get("status")

    if status_val not in ["APPROVED", "REJECTED", "PENDING"]:
        return JsonResponse({"error": "Invalid status"}, status=400)

    post.status = status_val
    post.save()

    return JsonResponse({"message": "Status updated", "post": PostSerializer(post).data})


@csrf_exempt
@auth_required
@role_required(["ADMIN"])
@require_http_methods(["DELETE"])
def admin_delete_post(request, post_id):
    """ADMIN only endpoint to permanently delete any post."""
    post = get_object_or_404(Post, id=post_id) 
    
    # Auth and role check are handled by decorators
    post.delete()
    return JsonResponse({"message": "Post deleted successfully"}, status=200)