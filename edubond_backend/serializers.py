from rest_framework import serializers
from users.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'organization', 'notification_content', 'type_of_notification', 'created_date_time']
