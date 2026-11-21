#!/usr/bin/env python
"""
Complete end-to-end functionality test for Gofer Exam.
Tests all major features: auth, profiles, scholarships, opportunities, documents, etc.
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import authenticate
from django.core.files.base import ContentFile
from apps.accounts.models import User
from apps.students.models import StudentProfile, Education, WorkExperience, Skill
from apps.scholarships.models import Scholarship
from apps.opportunities.models import Opportunity
from apps.documents.models import Document
from apps.consultants.models import ConsultantProfile
from apps.applications.models import Application

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_status(message, status="info"):
    """Print colored status message."""
    colors = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLUE}
    color = colors.get(status, RESET)
    symbol = {"success": "✓", "error": "✗", "warning": "⚠", "info": "ℹ"}
    print(f"{color}{symbol.get(status, '')} {message}{RESET}")

def test_authentication():
    """Test user authentication."""
    print("\n" + "="*60)
    print("Testing Authentication")
    print("="*60)
    
    # Test student login
    user = authenticate(email='testuser@gofer.test', password='TestPass123!')
    if user:
        print_status("Student authentication successful", "success")
        print(f"  User: {user.email} ({user.role})")
    else:
        print_status("Student authentication FAILED", "error")
        return False
    
    # Test admin login
    admin = authenticate(email='admin@gofer.test', password='AdminPass123!')
    if admin:
        print_status("Admin authentication successful", "success")
        print(f"  User: {admin.email} ({admin.role})")
    else:
        print_status("Admin authentication FAILED", "error")
        return False
    
    # Test consultant login
    consultant = authenticate(email='consultant@gofer.test', password='ConsultPass123!')
    if consultant:
        print_status("Consultant authentication successful", "success")
        print(f"  User: {consultant.email} ({consultant.role})")
    else:
        print_status("Consultant authentication FAILED", "error")
        return False
    
    return True

def test_student_profile():
    """Test student profile management."""
    print("\n" + "="*60)
    print("Testing Student Profile")
    print("="*60)
    
    user = User.objects.get(email='testuser@gofer.test')
    profile = StudentProfile.objects.get(user=user)
    
    # Update profile
    profile.nationality = 'ET'
    profile.current_education_level = 'UNDERGRADUATE'
    profile.field_of_study = 'Computer Science'
    profile.gpa = 3.5
    profile.target_countries = ['US', 'UK', 'CA']
    profile.preferred_fields = ['Technology', 'Engineering']
    profile.save()
    
    print_status("Profile updated successfully", "success")
    print(f"  Nationality: {profile.nationality}")
    print(f"  GPA: {profile.gpa}")
    print(f"  Target countries: {', '.join(profile.target_countries)}")
    
    # Test profile completion
    completion = profile.get_completion_percentage()
    print_status(f"Profile completion: {completion['percentage']}%", "info")
    if completion['missing_fields']:
        print(f"  Missing fields: {', '.join(completion['missing_fields'][:5])}")
    
    return True

def test_education_history():
    """Test education history management."""
    print("\n" + "="*60)
    print("Testing Education History")
    print("="*60)
    
    user = User.objects.get(email='testuser@gofer.test')
    profile = StudentProfile.objects.get(user=user)
    
    # Create education record
    edu = Education.objects.create(
        student=profile,
        institution_name='Addis Ababa University',
        degree_level='BACHELOR',
        field_of_study='Computer Science',
        country='ET',
        start_date='2020-09-01',
        is_current=True,
        gpa=3.5,
        gpa_scale=4.0
    )
    
    print_status("Education record created", "success")
    print(f"  Institution: {edu.institution_name}")
    print(f"  Degree: {edu.degree_level}")
    print(f"  Field: {edu.field_of_study}")
    
    return True

def test_scholarships():
    """Test scholarship queries."""
    print("\n" + "="*60)
    print("Testing Scholarships")
    print("="*60)
    
    # Get all scholarships
    scholarships = Scholarship.objects.filter(is_published=True)
    print_status(f"Found {scholarships.count()} published scholarships", "success")
    
    for s in scholarships[:3]:
        print(f"  - {s.name} ({s.country})")
        print(f"    Type: {s.type}, Level: {s.level}")
        print(f"    Deadline: {s.application_deadline}")
    
    # Test nationality filtering
    eth_scholarships = scholarships.filter(nationality_eligibility='ALL')
    print_status(f"{eth_scholarships.count()} scholarships open to all nationalities", "info")
    
    return True

def test_opportunities():
    """Test opportunity management."""
    print("\n" + "="*60)
    print("Testing Opportunities")
    print("="*60)
    
    opportunities = Opportunity.objects.filter(is_published=True)
    print_status(f"Found {opportunities.count()} published opportunities", "success")
    
    if opportunities.count() == 0:
        print_status("No opportunities to display", "warning")
    else:
        for opp in opportunities[:3]:
            print(f"  - {opp.title} ({opp.country})")
            print(f"    Category: {opp.category}")
    
    return True

def test_consultant_profile():
    """Test consultant profile."""
    print("\n" + "="*60)
    print("Testing Consultant Profile")
    print("="*60)
    
    consultant = User.objects.get(email='consultant@gofer.test')
    
    # Get or create consultant profile
    profile, created = ConsultantProfile.objects.get_or_create(
        user=consultant,
        defaults={
            'company_name': 'Gofer Consulting',
            'job_title': 'Senior Consultant',
            'years_of_experience': 5,
            'bio': 'Experienced study abroad consultant',
            'specializations': ['University Applications', 'Scholarship Guidance'],
            'languages': ['English', 'Amharic'],
            'expertise_countries': ['US', 'UK', 'CA'],
            'consultation_rate': '100.00',
            'timezone': 'Africa/Addis_Ababa',
            'verification_status': 'VERIFIED',
            'is_available': True
        }
    )
    
    if created:
        print_status("Consultant profile created", "success")
    else:
        print_status("Consultant profile exists", "info")
    
    print(f"  Company: {profile.company_name}")
    print(f"  Experience: {profile.years_of_experience} years")
    print(f"  Specializations: {', '.join(profile.specializations)}")
    
    return True

def test_applications():
    """Test application management."""
    print("\n" + "="*60)
    print("Testing Applications")
    print("="*60)
    
    user = User.objects.get(email='testuser@gofer.test')
    profile = StudentProfile.objects.get(user=user)
    
    # Get a scholarship
    scholarship = Scholarship.objects.filter(is_published=True).first()
    
    if not scholarship:
        print_status("No scholarships available to test applications", "warning")
        return True
    
    # Create application
    app, created = Application.objects.get_or_create(
        student=profile,
        application_type='SCHOLARSHIP',
        scholarship=scholarship,
        defaults={
            'program_name': 'Test Program',
            'degree_level': 'UNDERGRADUATE',
            'status': 'DRAFT'
        }
    )
    
    if created:
        print_status("Application created", "success")
    else:
        print_status("Application exists", "info")
    
    print(f"  Type: {app.application_type}")
    print(f"  Scholarship: {scholarship.name}")
    print(f"  Status: {app.status}")
    
    return True

def test_database_counts():
    """Test database record counts."""
    print("\n" + "="*60)
    print("Database Statistics")
    print("="*60)
    
    counts = {
        "Users": User.objects.count(),
        "Students": User.objects.filter(role='STUDENT').count(),
        "Consultants": User.objects.filter(role='CONSULTANT').count(),
        "Admins": User.objects.filter(role='ADMIN').count(),
        "Scholarships (Published)": Scholarship.objects.filter(is_published=True).count(),
        "Scholarships (Draft)": Scholarship.objects.filter(is_published=False).count(),
        "Opportunities (Published)": Opportunity.objects.filter(is_published=True).count(),
        "Applications": Application.objects.count(),
        "Documents": Document.objects.count(),
    }
    
    for label, count in counts.items():
        print(f"  {label}: {count}")
    
    return True

def run_all_tests():
    """Run all tests."""
    print(f"\n{BLUE}{'='*60}")
    print("Gofer Exam Complete Functionality Test")
    print(f"{'='*60}{RESET}\n")
    
    tests = [
        ("Authentication", test_authentication),
        ("Student Profile", test_student_profile),
        ("Education History", test_education_history),
        ("Scholarships", test_scholarships),
        ("Opportunities", test_opportunities),
        ("Consultant Profile", test_consultant_profile),
        ("Applications", test_applications),
        ("Database Counts", test_database_counts),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print_status(f"Error in {name}: {str(e)}", "error")
            results.append((name, False))
    
    # Summary
    print(f"\n{BLUE}{'='*60}")
    print("Test Summary")
    print(f"{'='*60}{RESET}\n")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "success" if success else "error"
        print_status(name, status)
    
    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print_status("\nAll tests PASSED!", "success")
        return 0
    else:
        print_status(f"\n{total - passed} tests FAILED", "error")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
