from .models import Farmer, Notification
from django.db.models import Q

def notifications_processor(request):
    unread_count = 0
    if request.user.is_authenticated:
        farmer = Farmer.objects.filter(user=request.user).first()
        if not farmer:
            farmer = Farmer.objects.filter(
                Q(email__iexact=request.user.email) | Q(mobile=request.user.username)
            ).first()
        if farmer:
            unread_count = Notification.objects.filter(farmer=farmer, is_read=False).count()
    return {'unread_notifications_count': unread_count}
