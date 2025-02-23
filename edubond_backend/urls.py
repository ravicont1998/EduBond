from django.conf.urls import url
from . import (
    views,
)
from rest_framework.authtoken.views import obtain_auth_token
urlpatterns = [
    url(r'^api-token-auth/', obtain_auth_token, name='api_token_auth'),
    url(r'^user-view/', views.UserListCreateAPIView.as_view(), name='user-list-create'),
    url(r'^login/', views.LoginAPIView.as_view(), name='user-login'),
    url(r'^logout/', views.LogoutAPIView.as_view(), name='user-logout'),
    url(r'^org-list/', views.OrganizationListCreateAPIView.as_view(), name='org-list'),
    url(r'^view-requests/', views.TeacherRequestListAPIView.as_view(), name='org-admin-view-requests'),
    url(r'^current-user-config/',views.CurrentUserConfigAPIView.as_view(), name='current-user'),
    url(r'^get-teachers-of-org/',views.TeacherofOrgAPIView.as_view(), name='fetch-teachers'),
    url(r'^notifications/', views.NotificationAPIView.as_view(), name='noitification-fetch'),
    url(r'^announcement-view/', views.CheckNotificationAPIView.as_view(), name='view-notifs'),  
    url(r'^onboard-student-directupload/', views.StudentOnboardView.as_view(), name='view-notifs'),
    url(r'^upload-student-excel/', views.StudentOnboardExcelAPIView.as_view(), name='view-notifs'),
    url(r'^view-students/', views.StudentListView.as_view(), name='view-students'),
    url(r'^ask-edubond/', views.AskEdubond.as_view(), name = 'ask-edubond'),
    url(r'^video-edubond/', views.UploadVideoView.as_view(), name = 'upload-video'),
    url(r'^view-insights/', views.InsightsAPIView.as_view(), name='view-insights'),
    url(r'^get-altext', views.AltView.as_view(), name='insights'),
    url(r'^get-org-notifs/', views.AdminNotifs.as_view(), name='notifs')
]
