from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views import View
import json

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

# Get the custom user model
Officer = get_user_model()

# ---------------------------
# Officer Registration View
# ---------------------------
@method_decorator(csrf_exempt, name="dispatch")
class OfficerRegisterView(APIView):
    def post(self, request):
        try:
            # Parse JSON from request body
            data = json.loads(request.body)

            officer_id = data.get("officer_id")
            officer_name = data.get("officer_name")
            batch = data.get("batch")
            location = data.get("location")
            email = data.get("email")
            password = data.get("password")

            # Validate all fields are provided
            if not all([officer_id, officer_name, batch, location, email, password]):
                return JsonResponse({"error": "All fields are required"}, status=400)

            # Check if officer already exists
            if Officer.objects.filter(username=officer_id).exists():
                return JsonResponse({"error": "Officer already exists"}, status=400)

            # Create officer
            officer = Officer.objects.create_user(
                username=officer_id,
                email=email,
                password=password,
                officer_id=officer_id,
                officer_name=officer_name,
                batch=batch,
                location=location,
            )

            return JsonResponse({"message": "Officer registered successfully ✅"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

# ---------------------------
# Officer Login View
# ---------------------------
@method_decorator(csrf_exempt, name="dispatch")
class OfficerLoginView(APIView):
    def post(self, request):
        print("request.data:", request.data)  # Debug print
        try:
            username = request.data.get("username")  # <-- changed
            password = request.data.get("password")

            if not all([username, password]):
                return JsonResponse({"error": "Username and password are required"}, status=400)

            officer = authenticate(request, username=username, password=password)

            if officer is not None:
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(officer)
                return JsonResponse({
                    "message": "Login successful ✅",
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "id": officer.id,
                        "username": officer.username,
                        "officer_name": officer.officer_name,
                        "email": officer.email,
                        "batch": officer.batch,
                        "location": officer.location
                    }
                })
            else:
                return JsonResponse({"error": "Invalid credentials"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        officer = request.user
        return JsonResponse({
            "id": officer.id,
            "username": officer.username,
            "officer_name": officer.officer_name,
            "email": officer.email,
            "batch": officer.batch,
            "location": officer.location,
            "date_joined": officer.date_joined.isoformat() if officer.date_joined else None
        })
