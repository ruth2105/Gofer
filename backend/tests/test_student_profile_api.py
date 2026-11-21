"""
Test cases for Student Profile API including education, experience, and skills.
"""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.students.models import StudentProfile, Education, WorkExperience, Skill
from apps.common.models import Country

User = get_user_model()


class StudentProfileAPITestCase(TestCase):
    """Test cases for student profile API."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            role='STUDENT',
            first_name='John',
            last_name='Doe'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        
        # Create a test country
        self.country = Country.objects.create(
            code='US',
            name='United States',
            is_active=True
        )
    
    def test_profile_autocreated_on_access(self):
        """Test that profile is auto-created when accessed."""
        response = self.client.get('/api/v1/students/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(StudentProfile.objects.filter(user=self.student).exists())
    
    def test_update_student_profile(self):
        """Test updating student profile."""
        data = {
            'gender': 'Male',
            'date_of_birth': '2000-01-01',
            'nationality_country': 'US',
            'current_education_level': 'UNDERGRADUATE',
            'school_name': 'Test University',
            'field_of_study': 'Computer Science'
        }
        
        response = self.client.patch('/api/v1/students/me/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['gender'], 'Male')
        self.assertEqual(response.data['school_name'], 'Test University')
    
    def test_profile_completion(self):
        """Test profile completion calculation."""
        response = self.client.get('/api/v1/students/me/completion/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('percentage', response.data)
        self.assertIn('is_completed', response.data)
        self.assertIn('missing_fields', response.data)


class EducationAPITestCase(TestCase):
    """Test cases for education history API."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        
        # Ensure profile exists
        self.profile = StudentProfile.objects.create(user=self.student)
        
        self.country = Country.objects.create(
            code='US',
            name='United States',
            is_active=True
        )
    
    def test_create_education(self):
        """Test creating education record."""
        data = {
            'institution_name': 'Harvard University',
            'degree_level': 'BACHELOR',
            'field_of_study': 'Computer Science',
            'country': 'US',
            'start_date': '2018-09-01',
            'end_date': '2022-05-31',
            'is_current': False,
            'gpa': 3.8,
            'gpa_scale': 4.0
        }
        
        response = self.client.post('/api/v1/students/education/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['institution_name'], 'Harvard University')
        self.assertEqual(response.data['degree_level'], 'BACHELOR')
    
    def test_list_education(self):
        """Test listing education records."""
        Education.objects.create(
            student_profile=self.profile,
            institution_name='Test University',
            degree_level='BACHELOR',
            field_of_study='Engineering',
            start_date=date(2018, 9, 1),
            end_date=date(2022, 5, 31),
            gpa=3.5,
            gpa_scale=4.0
        )
        
        response = self.client.get('/api/v1/students/education/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['institution_name'], 'Test University')
    
    def test_current_education_no_end_date(self):
        """Test that current education should not have end date."""
        data = {
            'institution_name': 'MIT',
            'degree_level': 'MASTER',
            'field_of_study': 'AI',
            'start_date': '2023-09-01',
            'end_date': '2024-05-31',
            'is_current': True,
            'gpa': 3.9,
            'gpa_scale': 4.0
        }
        
        response = self.client.post('/api/v1/students/education/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.data)
        self.assertIn('non_field_errors', response.data['details'])
    
    def test_end_date_before_start_date(self):
        """Test validation for end date before start date."""
        data = {
            'institution_name': 'Test Uni',
            'degree_level': 'BACHELOR',
            'field_of_study': 'Math',
            'start_date': '2020-09-01',
            'end_date': '2019-05-31',
            'is_current': False,
            'gpa': 3.5,
            'gpa_scale': 4.0
        }
        
        response = self.client.post('/api/v1/students/education/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_education(self):
        """Test updating education record."""
        education = Education.objects.create(
            student_profile=self.profile,
            institution_name='Old University',
            degree_level='BACHELOR',
            field_of_study='Physics',
            start_date=date(2018, 9, 1),
            end_date=date(2022, 5, 31),
            is_current=False,
            gpa=3.2,
            gpa_scale=4.0
        )
        
        # PATCH should allow partial updates
        data = {
            'gpa': 3.7,
            'achievements': 'Dean\'s List'
        }
        response = self.client.patch(f'/api/v1/students/education/{education.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['gpa']), 3.7)
        self.assertEqual(response.data['achievements'], 'Dean\'s List')
    
    def test_delete_education(self):
        """Test deleting education record."""
        education = Education.objects.create(
            student_profile=self.profile,
            institution_name='Delete Me University',
            degree_level='BACHELOR',
            field_of_study='Biology',
            start_date=date(2018, 9, 1),
            end_date=date(2022, 5, 31),
            gpa=3.0,
            gpa_scale=4.0
        )
        
        response = self.client.delete(f'/api/v1/students/education/{education.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Education.objects.filter(id=education.id).exists())


class WorkExperienceAPITestCase(TestCase):
    """Test cases for work experience API."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        
        self.profile = StudentProfile.objects.create(user=self.student)
        
        self.country = Country.objects.create(
            code='US',
            name='United States',
            is_active=True
        )
    
    def test_create_work_experience(self):
        """Test creating work experience record."""
        data = {
            'company_name': 'Tech Corp',
            'position_title': 'Software Engineer',
            'employment_type': 'FULL_TIME',
            'location': 'San Francisco, CA',
            'country': 'US',
            'start_date': '2022-06-01',
            'end_date': '2024-08-31',
            'is_current': False,
            'description': 'Developed web applications',
            'skills_used': ['Python', 'Django', 'React']
        }
        
        response = self.client.post('/api/v1/students/experience/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], 'Tech Corp')
        self.assertEqual(response.data['position_title'], 'Software Engineer')
    
    def test_list_work_experience(self):
        """Test listing work experience records."""
        WorkExperience.objects.create(
            student_profile=self.profile,
            company_name='Company A',
            position_title='Developer',
            employment_type='INTERNSHIP',
            start_date=date(2021, 6, 1),
            end_date=date(2021, 8, 31),
            description='Summer internship'
        )
        
        response = self.client.get('/api/v1/students/experience/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_current_position_no_end_date(self):
        """Test that current position should not have end date."""
        data = {
            'company_name': 'Current Corp',
            'position_title': 'Engineer',
            'employment_type': 'FULL_TIME',
            'start_date': '2024-01-01',
            'end_date': '2025-01-01',
            'is_current': True,
            'description': 'Current role'
        }
        
        response = self.client.post('/api/v1/students/experience/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SkillAPITestCase(TestCase):
    """Test cases for skills API."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        
        self.profile = StudentProfile.objects.create(user=self.student)
    
    def test_create_skill(self):
        """Test creating skill."""
        data = {
            'name': 'Python Programming',
            'category': 'TECHNICAL',
            'proficiency': 'ADVANCED',
            'years_of_experience': 5
        }
        
        response = self.client.post('/api/v1/students/skills/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Python Programming')
        self.assertEqual(response.data['proficiency'], 'ADVANCED')
    
    def test_list_skills(self):
        """Test listing skills."""
        Skill.objects.create(
            student_profile=self.profile,
            name='JavaScript',
            category='TECHNICAL',
            proficiency='INTERMEDIATE',
            years_of_experience=3
        )
        
        response = self.client.get('/api/v1/students/skills/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_duplicate_skill_prevented(self):
        """Test that duplicate skills are prevented."""
        # Create first skill
        data = {
            'name': 'React',
            'category': 'TECHNICAL',
            'proficiency': 'INTERMEDIATE'
        }
        
        response1 = self.client.post('/api/v1/students/skills/', data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Try to create duplicate
        response2 = self.client.post('/api/v1/students/skills/', data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response2.data)
        self.assertIn('name', response2.data['details'])
    
    def test_delete_skill(self):
        """Test deleting skill."""
        skill = Skill.objects.create(
            student_profile=self.profile,
            name='Old Skill',
            category='OTHER',
            proficiency='BEGINNER'
        )
        
        response = self.client.delete(f'/api/v1/students/skills/{skill.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Skill.objects.filter(id=skill.id).exists())


class StudentProfileDetailTestCase(TestCase):
    """Test cases for comprehensive profile detail view."""
    
    def setUp(self):
        """Set up test data with complete profile."""
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        
        self.profile = StudentProfile.objects.create(user=self.student)
        
        # Add education
        Education.objects.create(
            student_profile=self.profile,
            institution_name='Test University',
            degree_level='BACHELOR',
            field_of_study='CS',
            start_date=date(2018, 9, 1),
            end_date=date(2022, 5, 31),
            gpa=3.8,
            gpa_scale=4.0
        )
        
        # Add work experience
        WorkExperience.objects.create(
            student_profile=self.profile,
            company_name='Tech Inc',
            position_title='Developer',
            employment_type='INTERNSHIP',
            start_date=date(2021, 6, 1),
            end_date=date(2021, 8, 31),
            description='Summer internship'
        )
        
        # Add skill
        Skill.objects.create(
            student_profile=self.profile,
            name='Python',
            category='TECHNICAL',
            proficiency='ADVANCED'
        )
    
    def test_get_detailed_profile(self):
        """Test retrieving detailed profile with all related records."""
        response = self.client.get('/api/v1/students/me/detail/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('education_history', response.data)
        self.assertIn('work_experience', response.data)
        self.assertIn('skills', response.data)
        
        self.assertEqual(len(response.data['education_history']), 1)
        self.assertEqual(len(response.data['work_experience']), 1)
        self.assertEqual(len(response.data['skills']), 1)
        
        self.assertEqual(response.data['education_history'][0]['institution_name'], 'Test University')
        self.assertEqual(response.data['work_experience'][0]['company_name'], 'Tech Inc')
        self.assertEqual(response.data['skills'][0]['name'], 'Python')
