# react_app/views.py
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
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    serializer = RegisterSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    user = serializer.save(role="AUTHOR")  # Default AUTHOR

    return JsonResponse(
        {"message": "User created successfully", "user": UserSerializer(user).data},
        status=201,
    )


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
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
# PUBLIC POSTS
# -------------------------------------------------
@csrf_exempt
@require_http_methods(["GET"])
def public_posts(request):
    posts = Post.objects.filter(status="APPROVED").order_by("-created_at")
    serializer = PostSerializer(posts, many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@require_http_methods(["GET"])
def public_post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id, status="APPROVED")
    serializer = PostSerializer(post)
    return JsonResponse(serializer.data)


# -------------------------------------------------
# AUTHOR APIs
# -------------------------------------------------
@csrf_exempt
@auth_required
@role_required(["AUTHOR", "ADMIN"])
@require_http_methods(["POST"])
def create_post(request):
    try:
        data = json.loads(request.body)
        title = data.get("title")
        content = data.get("content")
        if not title or not content:
            return JsonResponse({"error": "title and content required"}, status=400)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Use serializer to validate
    serializer = PostSerializer(data=data)
    if serializer.is_valid():
        # Save post with author and auto status
        post = serializer.save(author=request.user, status="APPROVED")  # Change to "PENDING" if needed
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
    post = get_object_or_404(Post, id=post_id)

    if request.user.role != "ADMIN" and post.author_id != request.user.id:
        return JsonResponse({"error": "Permission denied"}, status=403)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    serializer = PostSerializer(post, data=data, partial=True)
    if serializer.is_valid():
        updated = serializer.save(status="PENDING", updated_at=timezone.now())
        return JsonResponse({"message": "Post updated", "post": PostSerializer(updated).data})

    return JsonResponse(serializer.errors, status=400)


@csrf_exempt
@auth_required
@role_required(["AUTHOR", "ADMIN"])
@require_http_methods(["DELETE"])
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user.role != "ADMIN" and post.author_id != request.user.id:
        return JsonResponse({"error": "Permission denied"}, status=403)

    post.delete()
    return JsonResponse({"message": "Post deleted"})


# -------------------------------------------------
# ADMIN APIs
# -------------------------------------------------
@csrf_exempt
@auth_required
@role_required(["ADMIN"])
@require_http_methods(["GET"])
def admin_list_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@auth_required
@role_required(["ADMIN"])
@require_http_methods(["PUT"])
def admin_update_user_role(request, user_id):
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
def admin_delete_post(request, post_id):
    # Allow only DELETE method
    if request.method != "DELETE":
        return JsonResponse({"error": "Invalid method"}, status=405)

    # Authenticate admin using JWT token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JsonResponse({"error": "Missing Authorization header"}, status=401)

    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = User.objects.get(id=payload["id"])
    except Exception:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    # Only ADMIN can delete any post
    if user.role != "ADMIN":
        return JsonResponse({"error": "Only ADMIN can delete posts"}, status=403)

    # Find post
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "Post not found"}, status=404)

    # Delete post
    post.delete()
    return JsonResponse({"message": "Post deleted successfully"}, status=200)
