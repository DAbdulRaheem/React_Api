# react_app/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import Group, Permission # Import Group and Permission

# --- CHOICES ---
ROLE_CHOICES = (
    ("ADMIN", "Admin"),
    ("AUTHOR", "Author"),
    ("VIEWER", "Viewer"),
)

STATUS_CHOICES = (
    ("PENDING", "Pending"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
)

# --- USER MANAGER ---
class UserManager(BaseUserManager):
    def create_user(self, email, name=None, password=None, role="VIEWER", **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, role=role, **extra_fields)
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name=None, password=None, **extra_fields):
        # Default role for superuser is ADMIN
        user = self.create_user(email, name=name, password=password, role="ADMIN", **extra_fields)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

# --- USER MODEL ---
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="VIEWER")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Required for PermissionsMixin to avoid reverse accessor clashes
    # The fix is to add unique related_name arguments:
    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        # Unique related name
        related_name="custom_user_groups", 
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        # Unique related name
        related_name="custom_user_permissions",
        related_query_name="user",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"
        
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest answer: Yes, always for is_admin
        return self.is_admin

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest answer: Yes, always for is_admin
        return self.is_admin

# --- POST MODEL ---
class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    # ForeignKey to the custom User model
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.status}"