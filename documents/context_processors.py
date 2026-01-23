from .models import Notification

def notification_count(request):
    if request.user.is_authenticated:
        return {
            'unread_notifications': Notification.objects.filter(
                user=request.user,
                read=False
            ).count()
        }
    return {}