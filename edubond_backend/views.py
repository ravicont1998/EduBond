
from django.shortcuts import render
from django.utils.timezone import localtime, pytz
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from users.models import UserFeatureConfig, Organization, TeacherOrganization, TeacherRequestLog, Notification, Student, TeacherUploadingVideo
from users.serializers import NotificationSerializer
from django.conf import settings
from django.core.files.storage import default_storage
import logging, os
import subprocess
import pandas as pd
logger = logging.getLogger(__name__)
# Create a view to list all users
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "gserv_account_file.json"

class LogoutAPIView(APIView):
    """
    API view to handle user logout by deleting the authentication token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get the token associated with the user
        try:
            token = Token.objects.get(user=request.user)
            token.delete()  # Delete the token to log the user out
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({"detail": "No active session found."}, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    """
    API view to handle user login and token generation
    """
    permission_classes = [AllowAny]  # Allow public access for login

    def post(self, request):
        """
        Authenticate user and generate token
        """
        # Get data from the request
        email = request.data.get('email')
        password = request.data.get('password')

        # Validate the input data
        if not email or not password:
            return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate the user
        user = authenticate(username=email, password=password)

        if user is not None:
            # User is authenticated, now create or fetch the token
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "detail": "Login successful",
                "token": token.key
            }, status=status.HTTP_200_OK)
        else:
            # Authentication failed
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class UserListCreateAPIView(APIView):
    """
    API view to handle user registration and user listing
    """
    # Permissions
    #permission_classes = [AllowAny]  # Allow public access for creating users
    # If you want to restrict user list to authenticated users
    permission_classes = [AllowAny]
    def post(self, request):
        # Get data
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        username = email
        phone_number = request.data.get('phone_number')
        type_of_user = request.data.get('type_of_user')
        password = request.data.get('password')
        # Validate the data
        if not first_name or not last_name or not email or not phone_number or not type_of_user:
            return Response({"detail": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"detail": "Username already exists."}, status=status.HTTP_417_EXPECTATION_FAILED)
        # Handle org-admin flow
        if type_of_user == 'org-admin':
            org_name = request.data.get('org_name')
            state = request.data.get('state')
            address = request.data.get('address')
            pincode = request.data.get('pincode')
            country = request.data.get('country')
            # Create organization
            """
            organization = Organization.objects.create(
                name=org_name,
                state=state,
                address=address,
                pincode=pincode,
                country=country
            )"""
            organization, created = Organization.objects.get_or_create(
                  name=org_name,
                  defaults={
                   'state': state,
                   'address': address,
                   'pincode': pincode,
                   'country': country
             }
            )
            # Create user (org-admin)
            user = User.objects.create_user(username=email, password=password, first_name=first_name, last_name=last_name,
                                            email=email)
            # Link the feature config
            UserFeatureConfig.objects.create(user=user, approved_user = True, phone_number=phone_number, organization_id =organization.id, type_of_user='org-admin')

        # Handle teacher flow
        elif type_of_user == 'teacher':
            # Fetch organizations to allow selection
            #organizations = Organization.objects.all()  # List of organizations for the teacher to select from
            # You can handle class number and admin request log here
            organization_id = request.data.get('organization_id')  # The organization selected by teacher
            class_number = request.data.get('class_number')
            from_admin = request.data.get('from_admin')
            organization = Organization.objects.get(id=organization_id)
            user = User.objects.create_user(username=email, password=password, first_name=first_name, last_name=last_name,
                                            email=email)
            # Link the feature config
            teacher_org = TeacherOrganization.objects.create(
                teacher=user,
                organization_id=organization_id,
                class_number=class_number
            )
            if from_admin:
               TeacherRequestLog.objects.create(teacher=user, organization = organization, status='approved')
            else:
               TeacherRequestLog.objects.create(teacher=user, organization = organization,  status='pending')
            UserFeatureConfig.objects.create(user=user, approved_user = from_admin, phone_number=phone_number, organization_id =organization.id, type_of_user='teacher')
        token, created = Token.objects.get_or_create(user=user)
        return Response({"detail": "User created successfully."}, status=status.HTTP_201_CREATED)

class OrganizationListCreateAPIView(APIView):
    """
    API view to handle organization listing and creation.
    """
    permission_classes = [AllowAny]  # Restrict access to authenticated users

    def get(self, request):
        """
        List all organizations or a specific organization by ID
        """
        org_id = self.request.GET.get('org_id', None)
        if org_id:
            # Fetch a specific organization by ID
            try:
                organization = Organization.objects.get(id=org_id)
                org_data = {
                    'id': organization.id,
                    'name': organization.name,
                    'state': organization.state,
                    'address': organization.address,
                    'pincode': organization.pincode,
                    'country': organization.country,
                }
                return Response(org_data, status=status.HTTP_200_OK)
            except Organization.DoesNotExist:
                return Response({"detail": "Organization not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Fetch all organizations
            organizations = Organization.objects.all()
            org_data_list = [{
                'id': org.id,
                'name': org.name,
                'state': org.state,
                'address': org.address,
                'pincode': org.pincode,
                'country': org.country,
            } for org in organizations]

            return Response(org_data_list, status=status.HTTP_200_OK)


class TeacherRequestListAPIView(APIView):
    """
    API view to handle listing of pending requests and updating their status
    """
    permission_classes = [IsAuthenticated]  # Restrict access to authenticated users

    def get(self, request):
        """
        List all pending requests for the authenticated user's organization.
        """
        # Get the logged-in user's organization
        user = request.user
        user_feature_config = UserFeatureConfig.objects.get(user=user)
        logger.info(user_feature_config)
        organization = user_feature_config.organization
        logger.info(organization)
        # Get all pending requests for that organization
        pending_requests = TeacherRequestLog.objects.filter(organization=organization, status='pending')
        requests_data = [{
            'id': req.id,
            'teacher': req.teacher.username,
            'organization': req.organization.name,
            'status': req.status,
        } for req in pending_requests]

        return Response(requests_data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Update the status of a teacher's request (approve or reject)
        """
        user = request.user
        # Get the new status
        logger.info(request.data)
        record_ids = request.data.get('record_id')
        logger.info(record_ids)
        for record_id in record_ids:
            record_id = int(record_id)
            #request_log = TeacherRequestLog.objects.get(id=int(request.data.get('record_id')))
            request_log = TeacherRequestLog.objects.get(id=record_id)
            logger.info(request_log)
            status_fetch = request.data.get('status')
            if status_fetch not in ['approved', 'rejected']:
               return Response({"detail": "Invalid status. Must be either 'approved' or 'rejected'."}, status=status.HTTP_400_BAD_REQUEST)
            # Update the status
            request_log.status = status_fetch
            request_log.save()
            feature_obj = UserFeatureConfig.objects.get(user = request_log.teacher) 
            feature_obj.approved_user = True
            feature_obj.save()
        
        return Response({"detail": "Approved successfully."}, status=status.HTTP_200_OK)

class CurrentUserConfigAPIView(APIView):
    """
    API to get current user's feature configuration.
    """
    permission_classes = [IsAuthenticated]  # Ensure only logged-in users can access

    def get(self, request):
        try:
            # Fetch the user's feature config
            user_config = UserFeatureConfig.objects.get(user=request.user)

            # Response data
            data = {
                "type_of_user": user_config.type_of_user,
                "organization_id": user_config.organization.id if user_config.organization else None,
                "org_name" : user_config.organization.name if user_config.organization else "",
                "state" : user_config.organization.state if user_config.organization else "",
                "address" : user_config.organization.address if user_config.organization else "",
                "pincode" : user_config.organization.pincode if user_config.organization else "",
                "country" : user_config.organization.country if user_config.organization else "",
            }
            return Response(data, status=status.HTTP_200_OK)

        except UserFeatureConfig.DoesNotExist:
            return Response({"message": "User configuration not found."}, status=status.HTTP_404_NOT_FOUND)

class TeacherofOrgAPIView(APIView):
    """
    API view to list all teachers in the authenticated user's organization.
    """
    permission_classes = [IsAuthenticated]  # Restrict access to authenticated users

    def get(self, request):
        """
        List all teachers in the authenticated user's organization.
        """
        user = request.user

        # Get the organization of the logged-in user
        try:
            user_feature_config = UserFeatureConfig.objects.get(user=user)
            organization = user_feature_config.organization
        except UserFeatureConfig.DoesNotExist:
            return Response({"detail": "User does not belong to any organization."}, status=status.HTTP_400_BAD_REQUEST)

        # Get all teachers in the same organization
        teachers = TeacherOrganization.objects.filter(organization=organization).select_related('teacher')

        # Prepare response data
        teachers_data = [{
            'teacher_id': teacher.teacher.id,
            'first_name': teacher.teacher.first_name,
            'last_name': teacher.teacher.last_name,
            'class_number': teacher.class_number,
            'teacher_email' : teacher.teacher.email,
            'organization': teacher.organization.name
        } for teacher in teachers]

        return Response(teachers_data, status=status.HTTP_200_OK)


class NotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve notifications for the admin's organization"""
        user = request.user
        user_feature_config = UserFeatureConfig.objects.get(user=user)  # Fetch organization details
        notifications = Notification.objects.filter(organization=user_feature_config.organization,is_deleted=False)
        notification_count = notifications.count()
        serializer = NotificationSerializer(notifications, many=True)

        return Response({
            "notification_count": notification_count,
            "notifications": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new notification (announcement)"""
        user = request.user
        user_feature_config = UserFeatureConfig.objects.get(user=user)  # Fetch organization

        notification_content = request.data.get('notification_content')
        type_of_notification = request.data.get('type_of_notification')

        if not notification_content or not type_of_notification:
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

        notification = Notification.objects.create(
            user=user,
            organization=user_feature_config.organization,
            notification_content=notification_content,
            type_of_notification=type_of_notification
        )

        return Response({"detail": "Notification created successfully"}, status=status.HTTP_201_CREATED)

class CheckNotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Fetch all active notifications for the user"""
        IST = pytz.timezone('Asia/Kolkata')
        notifications = Notification.objects.filter(user=request.user, is_deleted=False).order_by('-created_date_time')
        notification_list = []
        for notif in notifications:
            # Convert UTC time to IST
            ist_time = notif.created_date_time.astimezone(IST)
            formatted_date = ist_time.strftime('%Y-%m-%d')  # YYYY-MM-DD format
            formatted_time = ist_time.strftime('%I:%M %p')  # 12-hour format with AM/PM
            notification_list.append({
                'id': notif.id,
                'notification_content': notif.notification_content,
                'type_of_notification': notif.type_of_notification,
                'date': formatted_date,
                'time': formatted_time
            })
        return Response(notification_list, status=status.HTTP_200_OK)
    def post(self, request):
        """Delete a notification by ID"""
        notification_id = request.data.get("notification_id")
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_deleted = True
            notification.save()
            return Response({"detail": "Notification deleted successfully"}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)


class StudentOnboardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        API endpoint for onboarding a single student
        """
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        preferred_language = request.data.get('preferred_language')
        parent_email = request.data.get('parent_email')
        if not first_name or not last_name or not email or not phone_number or not password:
            return Response({"detail": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=email).exists():
            return Response({"detail": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the student user
        user = User.objects.create_user(
            username=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        teacher = request.user

        # Get class_number from TeacherOrganization table
        teacher_org = TeacherOrganization.objects.filter(teacher=teacher).first()
        if not teacher_org:
            return Response({"detail": "Teacher organization not found."}, status=status.HTTP_404_NOT_FOUND)

        student_class = teacher_org.class_number

        # Create the student record
        Student.objects.create(
            user=user,
            phone_number=phone_number,
            student_class=student_class,
            teacher=teacher,
            preferred_language_of_parent=preferred_language,
            parent_email=parent_email
        )
        UserFeatureConfig.objects.create(user=user, approved_user = True, phone_number=phone_number, organization_id = teacher_org.organization.id, type_of_user='student')

        return Response({"detail": "Student onboarded successfully"}, status=status.HTTP_201_CREATED)

class StudentOnboardExcelAPIView(APIView):
    """
    API view to handle student onboarding via Excel file
    """
    permission_classes = [IsAuthenticated]  # Allow access only to logged-in users

    language_code_map = {
        "Assamese": "as",
        "Bengali": "bn",
        "Bodo": "brx",
        "Dogri": "doi",
        "English": "en",
        "French": "fr",
        "Gujarati": "gu",
        "Hindi": "hi",
        "Kannada": "kn",
        "Kashmiri": "ks",
        "Konkani": "kok",
        "Maithili": "mai",
        "Malayalam": "ml",
        "Manipuri": "mni",
        "Marathi": "mr",
        "Nepali": "ne",
        "Odia": "or",
        "Punjabi": "pa",
        "Sanskrit": "sa",
        "Santali": "sat",
        "Sindhi": "sd",
        "Spanish": "es",
        "Tamil": "ta",
        "Telugu": "te",
        "Urdu": "ur"
    }

    def post(self, request):
        excel_file = request.FILES.get('file')
        if not excel_file:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploaded_excels', excel_file.name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)
            # Read the Excel file
            df = pd.read_excel(file_path)

            # Loop through each row
            for _, row in df.iterrows():
                first_name = row.get('first_name')
                last_name = row.get('last_name')
                email = row.get('student_id')
                phone_number = row.get('parent_phone_number')
                password = row.get('password')
                parent_email = row.get('parent_email')
                preferred_language = row.get('preferred_language_of_parent', 'English')
                student_class = row.get('student_class')

                # Convert preferred language name to code
                language_code = self.language_code_map.get(preferred_language, 'en')  # Default to English if not found

                # Check if user already exists
                if User.objects.filter(email=email).exists():
                    continue  # Skip existing user

                # Create user and student record
                user = User.objects.create_user(username=email, password=password, first_name=first_name,
                                                last_name=last_name, email=email)
                teacher = request.user  # Get the logged-in teacher
                teacher_org = TeacherOrganization.objects.filter(teacher=teacher).first()
                if not teacher_org:
                   return Response({"detail": "Teacher organization not found."}, status=status.HTTP_404_NOT_FOUND)
                # Create a new student record
                Student.objects.create(
                    user=user,
                    phone_number=phone_number,
                    student_class=teacher_org.class_number,
                    teacher=teacher,
                    preferred_language_of_parent=language_code,
                    parent_email=parent_email
                )
                UserFeatureConfig.objects.create(user=user, approved_user = True, phone_number=phone_number, organization_id = teacher_org.organization.id, type_of_user='student')

            return Response({"detail": "Students onboarded successfully from Excel."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StudentListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        teacher = request.user
        students = Student.objects.filter(teacher=teacher)
        student_data = []

        for student in students:
            student_data.append({
                'first_name': student.user.first_name,
                'last_name': student.user.last_name,
                'parent_email': student.parent_email,
                'preferred_language': student.preferred_language_of_parent,
                'parent_contact': student.phone_number,
                'student_class': student.student_class,
            })

        return Response({'students': student_data}, status=status.HTTP_200_OK)

class AskEdubond(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        prompt = request.data.get('prompt',None)
        from gemini import get_gemini_response
        if prompt:
           chat_res = get_gemini_response(prompt)
        else:
           chat_res = "Could you provide more info. please...."
        return Response({'response': chat_res}, status=status.HTTP_200_OK)

class UploadVideoView(APIView):
    def post(self, request):
        try:
            import uuid
            video_file = request.FILES.get('video')
            topic_name = request.data.get('topic_name')
            teacher = request.user
            logger.info(video_file)
            logger.info(topic_name)
            if not video_file or not topic_name:
                return Response({"detail": "Video file and topic name are required"}, status=status.HTTP_400_BAD_REQUEST)
            unique_filename = f"{uuid.uuid4()}_{video_file.name}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploaded_videos', unique_filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)
            video_path = file_path
            logger.info(video_path)
            # Extract audio using ffmpeg
            audio_filename = f"{uuid.uuid4()}_{os.path.splitext(video_file.name)[0]}.mp3"
            audio_path = os.path.join(settings.MEDIA_ROOT, 'uploaded_videos', audio_filename)
            ffmpeg_command = ['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path]
            subprocess.run(ffmpeg_command, check=True)
            logger.info(f"Audio extracted and saved at: {audio_path}")
            edubond_report = {
                "analysis": "good",
                "speaking": "slow",
                "clarity": "excellent",
                "engagement": "average"
            }
            # Save to the model
            TeacherUploadingVideo.objects.create(
                teacher=teacher,
                video_path=video_path,
                audio_path=audio_path,
                topic_name=topic_name,
                edubond_report=edubond_report
            )
            return Response({"detail": "Video uploaded successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.info(e)
            return Response({"detail": f"An error occurred while uploading the video: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InsightsAPIView(APIView):
    def get(self, request):
        try:
            videos = TeacherUploadingVideo.objects.filter(teacher=request.user)
            insights_data = []

            for video in videos:
                
                video_url = f"http://34.121.13.79/{video.video_path}".replace("/home/ravi_vemagiri/edubond-be/", "")
                audio_url = f"http://34.121.13.79/{video.audio_path}".replace("/home/ravi_vemagiri/edubond-be/", "")
                insights_data.append({
                    "topic_name": video.topic_name,
                    "created_date": video.created_date_time.strftime('%Y-%m-%d %H:%M'),
                    "video_url": video_url,
                    "audio_url": audio_url,
                    "edubond_report": video.edubond_report,
                    "parent_report": video.parent_report
                })

            return Response({"insights": insights_data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AltView(APIView):
    def post(self, request):
        try:
            import uuid
            image_file = request.FILES.get('image')
            topic_subject = request.data.get('topic_subject')
            teacher = request.user
            image_name = image_file.name
            unique_filename = f"{uuid.uuid4()}_{image_name}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'uploaded_alttext_images', unique_filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)
            temp_data = {
                'chem_aro.png' : {
                    'latex' : '\chemfig { *6 ( = N - = - = - ) }',
                     "alttext" : "A 6-membered heterocyclic hexagonal ring is in a vertical orientation and consists of 1 N and 5 C atoms. N occupies the first position, which is the bottommost vertex. A double bond is present between N and C 1, C 2 and C 3, and C 4 and C 5."

                    },
                'chem_lewis.png' : {
                    'latex' : '\chemfig { H - \lewis { 2: 6:, O } - H }',
                     "alttext" : " H, single bond, O, single bond, H. O has two lone pairs of electrons. "

                    },
                'math_sigma1.png' : {
                      "latex": "\\boldsymbol { n } = \\left( \\frac { z _ { \\alpha / 2 } \\cdot \\sigma } { m } \\right) ^ { 2 }",
                      "alttext" : "n equals (StartFraction z subscript alpha divided by 2 Baseline times sigma over m EndFraction) squared."
                      
                    },
                'math_sigma2.png' : {
                      "latex": "\\sigma _ { \\bar { x } } = \\frac { \\sigma } { \\sqrt { n } } = \\frac { 9.5 } { \\sqrt { 125 } } = 0.8497",
                      "alttext": "Sigma subscript x bar Baseline equals StartFraction sigma over StartRoot n EndRoot EndFraction equals StartFraction 9.5 over StartRoot 125 EndRoot EndFraction equals 0.8497."
                    }


            }
            generated_latex = temp_data[image_name]['latex']
            generated_alttext = temp_data[image_name]['alttext']
            image_url = f"http://34.121.13.79/{file_path}".replace("/home/ravi_vemagiri/edubond-be/", "")
            # Create a response dictionary
            insights_data = {
                "image_url": image_url,
                "latex": generated_latex,
                "alttext": generated_alttext,
                "subject": topic_subject
            }
            return Response(insights_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminNotifs(APIView):
    def get(self, request):
        try:
            # Get the organization ID of the current user
            from g_lang import translate_text
            organization_id = UserFeatureConfig.objects.get(user=request.user).organization_id          
            if UserFeatureConfig.objects.get(user=request.user).type_of_user == 'student':
               org_admin_users = UserFeatureConfig.objects.filter(organization_id=organization_id, type_of_user__in=['org-admin','teacher']).values('user')
            else:
              # Get all users with user_type 'org-admin' belonging to that organization
              org_admin_users = UserFeatureConfig.objects.filter(organization_id=organization_id, type_of_user='org-admin').values('user')
            # Get the notifications for all those users
            notifications = Notification.objects.filter(
                user__in=org_admin_users, is_deleted=False
            ).order_by('-created_date_time')
            
            # Structure the response data
            data = [{
                'id': notif.id,
                'content': notif.notification_content,
                'type': notif.type_of_notification,
                'date': notif.created_date_time.strftime('%Y-%m-%d'),
                'time': notif.created_date_time.strftime('%H:%M:%S')
            } for notif in notifications]
            if UserFeatureConfig.objects.get(user=request.user).type_of_user == 'student':
               student_obj = Student.objects.get(user = request.user)
               lang = student_obj.preferred_language_of_parent
               for dat in data:
                   _, dat['converted_msg'] = translate_text(dat['content'], target_language=lang)
            return Response({'notifications': data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.info(e)
            return Response({'detail': f'Error fetching notifications: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
