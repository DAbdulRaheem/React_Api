# users/backends.py
import jwt
from django.conf import settings
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User

class CustomJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None # Not authenticated, let other auth classes or permission handle it

        try:
            # Expected format: "Bearer <token>"
            token_prefix, token = auth_header.split()
            if token_prefix.lower() != 'bearer':
                return None
        except ValueError:
            return None # Invalid header format

        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get('user_id')
            
            if user_id is None:
                raise AuthenticationFailed('User identifier not found in token.')

            user = User.objects.get(pk=user_id)
            return (user, token) # Authentication successful
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired.')
        except jwt.InvalidSignatureError:
            raise AuthenticationFailed('Invalid token signature.')
        except jwt.DecodeError:
            raise AuthenticationFailed('Token is invalid.')
        except User.DoesNotExist:
            raise AuthenticationFailed('User associated with token not found.')
        except Exception as e:
            raise AuthenticationFailed(str(e))