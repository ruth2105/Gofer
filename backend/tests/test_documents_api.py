"""
Test cases for Document Management API.
"""
import io
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from apps.documents.models import Document
from apps.applications.models import Application
from apps.opportunities.models import Opportunity

User = get_user_model()


class DocumentAPITestCase(TestCase):
    """Test cases for Document API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            role='STUDENT',
            first_name='Test',
            last_name='Student'
        )
        
        self.consultant = User.objects.create_user(
            email='consultant@test.com',
            password='testpass123',
            role='CONSULTANT',
            first_name='Test',
            last_name='Consultant'
        )
        
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role='ADMIN',
            first_name='Test',
            last_name='Admin'
        )
        
        # Create API clients
        self.student_client = APIClient()
        self.student_client.force_authenticate(user=self.student)
        
        self.consultant_client = APIClient()
        self.consultant_client.force_authenticate(user=self.consultant)
        
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)
        
        # Create test file
        self.test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"file_content",
            content_type="application/pdf"
        )
    
    def test_student_can_upload_document(self):
        """Test that students can upload documents."""
        data = {
            'title': 'Test Transcript',
            'description': 'My academic transcript',
            'document_type': 'TRANSCRIPT',
            'file': self.test_file
        }
        
        response = self.student_client.post('/api/v1/documents/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Transcript')
        self.assertEqual(response.data['document_type'], 'TRANSCRIPT')
        self.assertEqual(response.data['status'], 'PENDING')
    
    def test_student_can_list_own_documents(self):
        """Test that students can list their own documents."""
        # Create a document for the student
        Document.objects.create(
            user=self.student,
            title='My Document',
            document_type='TRANSCRIPT',
            file=self.test_file
        )
        
        response = self.student_client.get('/api/v1/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'My Document')
    
    def test_student_cannot_see_other_student_documents(self):
        """Test that students cannot see documents from other students."""
        other_student = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        # Create document for other student
        Document.objects.create(
            user=other_student,
            title='Other Document',
            document_type='TRANSCRIPT',
            file=self.test_file
        )
        
        response = self.student_client.get('/api/v1/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_admin_can_see_all_documents(self):
        """Test that admins can see all documents."""
        # Create documents for different users
        Document.objects.create(
            user=self.student,
            title='Student Document',
            document_type='TRANSCRIPT',
            file=self.test_file
        )
        
        response = self.admin_client.get('/api/v1/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_admin_can_verify_document(self):
        """Test that admins can verify documents."""
        document = Document.objects.create(
            user=self.student,
            title='Test Document',
            document_type='TRANSCRIPT',
            file=self.test_file,
            status='PENDING'
        )
        
        data = {
            'status': 'APPROVED',
            'verification_notes': 'Document verified successfully'
        }
        
        response = self.admin_client.post(
            f'/api/v1/documents/{document.id}/verify/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('document', response.data)
        self.assertEqual(response.data['document']['status'], 'APPROVED')
        
        # Refresh from database
        document.refresh_from_db()
        self.assertEqual(document.status, 'APPROVED')
        self.assertEqual(document.verified_by, self.admin)
        self.assertIsNotNone(document.verified_at)
    
    def test_student_cannot_verify_document(self):
        """Test that students cannot verify documents."""
        document = Document.objects.create(
            user=self.student,
            title='Test Document',
            document_type='TRANSCRIPT',
            file=self.test_file,
            status='PENDING'
        )
        
        data = {
            'status': 'APPROVED',
            'verification_notes': 'Trying to verify'
        }
        
        response = self.student_client.post(
            f'/api/v1/documents/{document.id}/verify/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_filter_documents_by_type(self):
        """Test filtering documents by type."""
        Document.objects.create(
            user=self.student,
            title='Transcript',
            document_type='TRANSCRIPT',
            file=self.test_file
        )
        Document.objects.create(
            user=self.student,
            title='Resume',
            document_type='RESUME',
            file=self.test_file
        )
        
        response = self.student_client.get('/api/v1/documents/by_type/?type=TRANSCRIPT')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # by_type returns a list, not paginated
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['document_type'], 'TRANSCRIPT')
    
    def test_file_size_validation(self):
        """Test that files over 10MB are rejected."""
        # Create a file that's too large (simulated)
        large_file = SimpleUploadedFile(
            "large.pdf",
            b"x" * (11 * 1024 * 1024),  # 11 MB
            content_type="application/pdf"
        )
        
        data = {
            'title': 'Large Document',
            'document_type': 'TRANSCRIPT',
            'file': large_file
        }
        
        response = self.student_client.post('/api/v1/documents/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # ValidationError is wrapped in 'details' key
        self.assertIn('details', response.data)
        self.assertIn('file', response.data['details'])
    
    def test_invalid_file_extension(self):
        """Test that invalid file extensions are rejected."""
        invalid_file = SimpleUploadedFile(
            "test.exe",
            b"file_content",
            content_type="application/x-msdownload"
        )
        
        data = {
            'title': 'Invalid Document',
            'document_type': 'TRANSCRIPT',
            'file': invalid_file
        }
        
        response = self.student_client.post('/api/v1/documents/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # ValidationError is wrapped in 'details' key
        self.assertIn('details', response.data)
        self.assertIn('file', response.data['details'])
    
    def test_student_can_delete_own_document(self):
        """Test that students can delete their own documents."""
        document = Document.objects.create(
            user=self.student,
            title='Test Document',
            document_type='TRANSCRIPT',
            file=self.test_file
        )
        
        response = self.student_client.delete(f'/api/v1/documents/{document.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(id=document.id).exists())
    
    def test_student_cannot_delete_others_document(self):
        """Test that students cannot delete other users' documents."""
        other_student = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        document = Document.objects.create(
            user=other_student,
            title='Other Document',
            document_type='TRANSCRIPT',
            file=self.test_file
        )
        
        response = self.student_client.delete(f'/api/v1/documents/{document.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Document.objects.filter(id=document.id).exists())


class DocumentDownloadTestCase(TestCase):
    """Test cases for document download functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            role='STUDENT'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)
        
        self.test_file = SimpleUploadedFile(
            "test.pdf",
            b"PDF content here",
            content_type="application/pdf"
        )
        
        self.document = Document.objects.create(
            user=self.student,
            title='Test Document',
            document_type='TRANSCRIPT',
            file=self.test_file
        )
    
    def test_download_own_document(self):
        """Test that users can download their own documents."""
        response = self.client.get(f'/api/v1/documents/{self.document.id}/download/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Content-Type is application/octet-stream for safe downloads
        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertIn('attachment', response['Content-Disposition'])
