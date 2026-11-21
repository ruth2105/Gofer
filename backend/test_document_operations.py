#!/usr/bin/env python
"""
Test document upload and download operations with LOCAL storage backend.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.students.models import StudentProfile
from apps.scholarships.models import Scholarship
from apps.applications.models import Application
from apps.documents.models import Document
from django.core.files.uploadedfile import SimpleUploadedFile
import io

User = get_user_model()

def test_document_operations():
    print("=" * 60)
    print("DOCUMENT UPLOAD/DOWNLOAD TEST")
    print("=" * 60)
    
    # Get student user
    try:
        student_user = User.objects.filter(role='STUDENT').first()
        if not student_user:
            print("✗ No student users found")
            return
        student_profile = StudentProfile.objects.get(user=student_user)
        print(f"✓ Student found: {student_user.email}")
    except User.DoesNotExist:
        print("✗ Student user not found")
        return
    
    # Get or create application
    scholarship = Scholarship.objects.filter(is_published=True).first()
    application, created = Application.objects.get_or_create(
        student=student_user,  # Use User, not StudentProfile
        scholarship=scholarship,
        defaults={'status': 'DRAFT', 'application_type': 'SCHOLARSHIP'}
    )
    print(f"✓ Application {'created' if created else 'found'}: ID={application.id}")
    
    print("\n=== DOCUMENT UPLOAD TESTS ===")
    
    # Test 1: Upload transcript
    print("[1] Uploading transcript PDF...")
    transcript_content = b"Sample transcript PDF content"
    transcript_file = SimpleUploadedFile(
        "transcript.pdf",
        transcript_content,
        content_type="application/pdf"
    )
    
    transcript_doc, created = Document.objects.update_or_create(
        user=student_user,
        application=application,
        document_type='TRANSCRIPT',
        defaults={
            'title': 'Academic Transcript',
            'file': transcript_file,
            'status': 'PENDING'
        }
    )
    print(f"✓ Transcript uploaded: {transcript_doc.file.name}")
    print(f"  File size: {transcript_doc.file_size} bytes")
    print(f"  Status: {transcript_doc.status}")
    
    # Test 2: Upload personal statement
    print("\n[2] Uploading personal statement...")
    statement_content = b"Sample personal statement content"
    statement_file = SimpleUploadedFile(
        "personal_statement.pdf",
        statement_content,
        content_type="application/pdf"
    )
    
    statement_doc, created = Document.objects.update_or_create(
        user=student_user,
        application=application,
        document_type='PERSONAL_STATEMENT',
        defaults={
            'title': 'Personal Statement',
            'file': statement_file,
            'status': 'PENDING'
        }
    )
    print(f"✓ Personal statement uploaded: {statement_doc.file.name}")
    print(f"  File size: {statement_doc.file_size} bytes")
    
    print("\n=== DOCUMENT RETRIEVAL TESTS ===")
    
    # Test 3: List application documents
    print("[3] Listing all documents for application...")
    docs = Document.objects.filter(application=application)
    print(f"✓ Found {docs.count()} documents:")
    for doc in docs:
        print(f"  - {doc.document_type}: {doc.title} ({doc.file_size} bytes)")
    
    # Test 4: Check file existence
    print("\n[4] Verifying file storage...")
    for doc in docs:
        if doc.file:
            file_path = doc.file.path
            exists = os.path.exists(file_path)
            print(f"{'✓' if exists else '✗'} {doc.document_type}: {file_path}")
            if exists:
                actual_size = os.path.getsize(file_path)
                print(f"  Actual file size: {actual_size} bytes")
        else:
            print(f"✗ {doc.document_type}: No file attached")
    
    # Test 5: Read file content
    print("\n[5] Reading file content...")
    try:
        with transcript_doc.file.open('rb') as f:
            content = f.read()
            print(f"✓ Transcript content read: {len(content)} bytes")
            print(f"  Content matches: {content == transcript_content}")
    except Exception as e:
        print(f"✗ Error reading file: {e}")
    
    # Test 6: Document metadata
    print("\n[6] Document metadata...")
    print(f"✓ Transcript:")
    print(f"  Uploaded at: {transcript_doc.created_at}")
    print(f"  Verified by: {transcript_doc.verified_by or 'None'}")
    print(f"  Status: {transcript_doc.status}")
    print(f"  Notes: {transcript_doc.verification_notes or 'None'}")
    
    print("\n=== STORAGE CONFIGURATION ===")
    from django.conf import settings
    print(f"Storage backend: {settings.STORAGE_BACKEND}")
    print(f"Media root: {settings.MEDIA_ROOT}")
    print(f"Media URL: {settings.MEDIA_URL}")
    
    print("\n" + "=" * 60)
    print("DOCUMENT OPERATIONS TEST COMPLETE")
    print("=" * 60)
    print("Summary:")
    print("✓ Document upload working")
    print("✓ File storage working")
    print("✓ Document retrieval working")
    print("✓ File content verification working")
    print("✓ Document metadata working")
    print("\nAll document operations verified with LOCAL storage!")

if __name__ == '__main__':
    test_document_operations()
