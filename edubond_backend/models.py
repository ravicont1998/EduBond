from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField

# Organization Table
class Organization(models.Model):
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    pincode = models.CharField(max_length=50)
    country =  models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return self.name


# User Feature Config Table
class UserFeatureConfig(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    type_of_user = models.CharField(max_length=80, blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    approved_user = models.BooleanField(default=False)  # Whether the user is approved or not
    phone_number=models.CharField(max_length=80, blank=True, null=True)
    def __str__(self):
        return f"{self.user.username} ({self.type_of_user})"


# Teacher Organization Table
class TeacherOrganization(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the User model (teacher)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)  # Link to the Organization model
    class_number = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.teacher.username} - {self.organization.name} ({self.class_number})"


# Teacher Request Log Table
class TeacherRequestLog(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the User model (teacher)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)  # Link to the Organization model
    status = models.CharField(max_length=40, default='pending')
    requested_on = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.teacher.username} - {self.organization.name} - {self.status}"

class Notification(models.Model):
    """
    Stores announcements/notifications created by admins.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # The admin creating the notification
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True)  # Link to the admin's organization
    notification_content = models.TextField()  # Announcement content
    type_of_notification = models.CharField(max_length=50, choices=[
        ('General', 'General'),
        ('Urgent', 'Urgent'),
        ('Reminder', 'Reminder'),
    ])
    created_date_time = models.DateTimeField(auto_now_add=True)  # Timestamp when created
    is_deleted = models.BooleanField(default=False)
    def __str__(self):
        return f"Notification by {self.user.username} - {self.type_of_notification}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    student_class = models.CharField(max_length=20)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="students")  # Teacher assigning the student
    preferred_language_of_parent = models.CharField(max_length=50)
    parent_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - Class {self.student_class}"


class TeacherUploadingVideo(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_videos")
    video_path = models.TextField(blank=True, null=True)
    created_date_time = models.DateTimeField(auto_now_add=True)
    edubond_report = JSONField(default=dict)  # Stores AI-generated analytics
    parent_report = JSONField(default=dict)  # Stores parent comments
    audio_path = models.TextField(blank=True, null=True)
    topic_name = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.teacher.username} - {self.video_path}"
