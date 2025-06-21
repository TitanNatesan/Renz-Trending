from django.http import JsonResponse
from .models import Size
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny

@api_view(["GET"])
@permission_classes([AllowAny])
def add_fake_sizes_for_tops_and_pants(request):
    """
    Adds fake size data for tops and pants for all available sizes.
    """
    size_data = [
        {
            "size": "XS",
            # Top measurements
            "bust": 32.0, "chest": 30.0, "shoulder": 14.0, "top_length": 22.0, "sleeve_length": 21.0,
            # Pants measurements
            "waist": 24.0, "hip": 34.0, "thigh": 18.0, "pant_length": 38.0, "inseam_length": 29.0,
        },
        {
            "size": "S",
            "bust": 34.0, "chest": 32.0, "shoulder": 15.0, "top_length": 23.0, "sleeve_length": 22.0,
            "waist": 26.0, "hip": 36.0, "thigh": 19.0, "pant_length": 39.0, "inseam_length": 30.0,
        },
        {
            "size": "M",
            "bust": 36.0, "chest": 34.0, "shoulder": 16.0, "top_length": 24.0, "sleeve_length": 23.0,
            "waist": 28.0, "hip": 38.0, "thigh": 20.0, "pant_length": 40.0, "inseam_length": 31.0,
        },
        {
            "size": "L",
            "bust": 38.0, "chest": 36.0, "shoulder": 17.0, "top_length": 25.0, "sleeve_length": 24.0,
            "waist": 30.0, "hip": 40.0, "thigh": 21.0, "pant_length": 41.0, "inseam_length": 32.0,
        },
        {
            "size": "XL",
            "bust": 40.0, "chest": 38.0, "shoulder": 18.0, "top_length": 26.0, "sleeve_length": 25.0,
            "waist": 32.0, "hip": 42.0, "thigh": 22.0, "pant_length": 42.0, "inseam_length": 33.0,
        },
        {
            "size": "XXL",
            "bust": 42.0, "chest": 40.0, "shoulder": 19.0, "top_length": 27.0, "sleeve_length": 26.0,
            "waist": 34.0, "hip": 44.0, "thigh": 23.0, "pant_length": 43.0, "inseam_length": 34.0,
        },
    ]

    for data in size_data:
        # Avoid duplicates by checking if the size already exists
        if not Size.objects.filter(size=data["size"]).exists():
            Size.objects.create(
                size=data["size"],
                bust=data.get("bust"),
                chest=data.get("chest"),
                shoulder=data.get("shoulder"),
                top_length=data.get("top_length"),
                sleeve_length=data.get("sleeve_length"),
                waist=data.get("waist"),
                hip=data.get("hip"),
                thigh=data.get("thigh"),
                pant_length=data.get("pant_length"),
                inseam_length=data.get("inseam_length"),
            )

    return JsonResponse({"message": "Fake size data for tops and pants added successfully!"})
