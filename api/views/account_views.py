from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.models import Account, UserProfile

from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from api.serializers.account_serializer import (
    RegisterSerializer,
    UserSerializer,
    UserProfileSerializer,
    LoginSerializer
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer


class UserProfileView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(request.user)

        return Response(serializer.data)


class FullProfileView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        profile = UserProfile.objects.get(user=request.user)

        serializer = UserProfileSerializer(profile)

        return Response(serializer.data)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            # 1. Authenticate returns an instance of your 'Account' model
            user = authenticate(request, email=email, password=password)

            if not user:
                return Response(
                    {"error": "Invalid email or password"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Token logic remains the same
            token, _ = Token.objects.get_or_create(user=user)

            # 3. FIX: Access the role directly from the 'user' object
            # No need to filter Account again!
            role = user.role 

            return Response({
                "token": token.key,
                "username": user.first_name,
                "role": role  # Use the variable we just got
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
