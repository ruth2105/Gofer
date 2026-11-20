'use client';

import axios from 'axios';
import { ChangeEvent, FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Award,
  BookOpen,
  BriefcaseBusiness,
  Download,
  FileText,
  PencilLine,
  Trash2,
  Upload,
} from 'lucide-react';
import { Footer } from '@/components/layout/Footer';
import { Navigation } from '@/components/layout/Navigation';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import {
  api,
  CountryApiRecord,
  DocumentApiRecord,
  EducationApiRecord,
  SkillApiRecord,
  StudentProfileApiRecord,
  StudentProfileCompletionApiRecord,
  StudentProfileDetailApiRecord,
  WorkExperienceApiRecord,
} from '@/lib/api/client';
import { getApiErrorMessage } from '@/lib/api/errors';

const EDUCATION_LEVELS: StudentProfileApiRecord['current_education_level'][] = [
  'HIGH_SCHOOL',
  'UNDERGRADUATE',
  'GRADUATE',
  'POSTGRADUATE',
];

const EMPTY_EDUCATION_FORM = {
  institution_name: '',
  degree_level: 'BACHELOR' as EducationApiRecord['degree_level'],
  field_of_study: '',
  country: '',
  start_date: '',
  end_date: '',
  is_current: false,
  gpa: '',
  gpa_scale: '4.0',
  achievements: '',
  description: '',
};

const EMPTY_EXPERIENCE_FORM = {
  company_name: '',
  position_title: '',
  employment_type: 'FULL_TIME' as WorkExperienceApiRecord['employment_type'],
  location: '',
  country: '',
  start_date: '',
  end_date: '',
  is_current: false,
  description: '',
  skills_used: '',
};

const EMPTY_SKILL_FORM = {
  name: '',
  category: 'TECHNICAL' as SkillApiRecord['category'],
  proficiency: 'INTERMEDIATE' as SkillApiRecord['proficiency'],
  years_of_experience: '',
};

const EMPTY_DOCUMENT_FORM = {
  document_type: 'CV' as DocumentApiRecord['document_type'],
  title: '',
  description: '',
  expiry_date: '',
  file: null as File | null,
};

const VALID_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'];
const MAX_DOCUMENT_BYTES = 10 * 1024 * 1024;

function labelFor(value: string): string {
  return value.replaceAll('_', ' ').toLocaleLowerCase().replace(/(^|\s)\S/g, (letter) => letter.toLocaleUpperCase());
}

function parseInteger(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) ? parsed : null;
}

function toDateLabel(value?: string | null): string {
  if (!value) return 'Present';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: 'short', year: 'numeric' });
}

export default function StudentProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<StudentProfileApiRecord | null>(null);
  const [detail, setDetail] = useState<StudentProfileDetailApiRecord | null>(null);
  const [completion, setCompletion] = useState<StudentProfileCompletionApiRecord | null>(null);
  const [countries, setCountries] = useState<CountryApiRecord[]>([]);
  const [documents, setDocuments] = useState<DocumentApiRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [saveError, setSaveError] = useState('');
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  const [educationForm, setEducationForm] = useState(EMPTY_EDUCATION_FORM);
  const [educationEditingId, setEducationEditingId] = useState<string | null>(null);
  const [educationSaving, setEducationSaving] = useState(false);
  const [educationMessage, setEducationMessage] = useState('');

  const [experienceForm, setExperienceForm] = useState(EMPTY_EXPERIENCE_FORM);
  const [experienceEditingId, setExperienceEditingId] = useState<string | null>(null);
  const [experienceSaving, setExperienceSaving] = useState(false);
  const [experienceMessage, setExperienceMessage] = useState('');

  const [skillForm, setSkillForm] = useState(EMPTY_SKILL_FORM);
  const [skillEditingId, setSkillEditingId] = useState<string | null>(null);
  const [skillSaving, setSkillSaving] = useState(false);
  const [skillMessage, setSkillMessage] = useState('');

  const [documentForm, setDocumentForm] = useState(EMPTY_DOCUMENT_FORM);
  const [uploadingDocument, setUploadingDocument] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [documentMessage, setDocumentMessage] = useState('');
  const [documentError, setDocumentError] = useState('');

  useEffect(() => {
    let active = true;

    api.auth.getCurrentUser()
      .then(async (user) => {
        if (!active) return;
        if (user.role !== 'STUDENT') {
          router.replace(user.role === 'CONSULTANT' ? '/consultant' : '/admin');
          return;
        }

        const [studentProfile, studentDetail, profileCompletion, countryOptions, documentList] = await Promise.all([
          api.students.profile(),
          api.students.detail(),
          api.students.profileCompletion(),
          api.countries.list(),
          api.documents.list(),
        ]);

        if (!active) return;
        setProfile(studentProfile);
        setDetail(studentDetail);
        setCompletion(profileCompletion);
        setCountries(countryOptions);
        setDocuments(documentList);
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          router.replace('/student/login');
          return;
        }
        setLoadError(getApiErrorMessage(error, 'Your profile could not be loaded.'));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [retryKey, router]);

  const update = <K extends keyof StudentProfileApiRecord>(
    key: K,
    value: StudentProfileApiRecord[K]
  ) => {
    setProfile((current) => current ? { ...current, [key]: value } : current);
    setSaved(false);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!profile) return;
    setSaving(true);
    setSaveError('');
    setSaved(false);
    try {
      const updatedProfile = await api.students.updateProfile({
        date_of_birth: profile.date_of_birth,
        gender: profile.gender,
        nationality_country: profile.nationality_country,
        passport_number: profile.passport_number,
        address: profile.address,
        city: profile.city,
        residence_country: profile.residence_country,
        postal_code: profile.postal_code,
        emergency_contact_name: profile.emergency_contact_name,
        emergency_contact_phone: profile.emergency_contact_phone,
        emergency_contact_relationship: profile.emergency_contact_relationship,
        current_education_level: profile.current_education_level,
        school_name: profile.school_name,
        field_of_study: profile.field_of_study,
        graduation_year: profile.graduation_year,
        gpa: profile.gpa,
        target_countries: profile.target_countries,
        target_degree_level: profile.target_degree_level,
        preferred_fields: profile.preferred_fields,
        budget_range: profile.budget_range,
        english_test_type: profile.english_test_type,
        english_test_score: profile.english_test_score,
        gre_score: profile.gre_score,
        gmat_score: profile.gmat_score,
        sat_score: profile.sat_score,
      });
      setProfile(updatedProfile);
      setDetail(await api.students.detail());
      setCompletion(await api.students.profileCompletion());
      setSaved(true);
    } catch (error: unknown) {
      setSaveError(getApiErrorMessage(error, 'Your profile could not be saved.'));
    } finally {
      setSaving(false);
    }
  };

  const handleEducationSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedInstitution = educationForm.institution_name.trim();
    const trimmedField = educationForm.field_of_study.trim();
    if (!trimmedInstitution || !trimmedField || !educationForm.start_date) {
      setEducationMessage('Institution, field of study, and start date are required.');
      return;
    }

    setEducationSaving(true);
    setEducationMessage('');

    try {
      const payload = {
        institution_name: trimmedInstitution,
        degree_level: educationForm.degree_level,
        field_of_study: trimmedField,
        country: educationForm.country || null,
        start_date: educationForm.start_date,
        end_date: educationForm.is_current ? null : educationForm.end_date || null,
        is_current: educationForm.is_current,
        gpa: educationForm.gpa ? Number(educationForm.gpa) : null,
        gpa_scale: Number(educationForm.gpa_scale || '4.0'),
        achievements: educationForm.achievements,
        description: educationForm.description,
      };

      if (educationEditingId) {
        const updated = await api.students.education.update(educationEditingId, payload);
        setDetail((current) => (current ? { ...current, education_history: (current.education_history ?? []).map((record) => record.id === updated.id ? updated : record) } : current));
      } else {
        const created = await api.students.education.create(payload);
        setDetail((current) => (current ? { ...current, education_history: [created, ...(current.education_history ?? [])] } : current));
      }

      setEducationForm(EMPTY_EDUCATION_FORM);
      setEducationEditingId(null);
      setEducationMessage(educationEditingId ? 'Education record updated.' : 'Education record added.');
    } catch (error: unknown) {
      setEducationMessage(getApiErrorMessage(error, 'Education could not be saved.'));
    } finally {
      setEducationSaving(false);
    }
  };

  const handleEditEducation = (record: EducationApiRecord) => {
    setEducationEditingId(record.id);
    setEducationForm({
      institution_name: record.institution_name,
      degree_level: record.degree_level,
      field_of_study: record.field_of_study,
      country: record.country ?? '',
      start_date: record.start_date,
      end_date: record.end_date ?? '',
      is_current: record.is_current,
      gpa: record.gpa !== null && record.gpa !== undefined ? String(record.gpa) : '',
      gpa_scale: String(record.gpa_scale ?? '4.0'),
      achievements: record.achievements ?? '',
      description: record.description ?? '',
    });
  };

  const handleDeleteEducation = async (id: string) => {
    if (!window.confirm('Remove this education record?')) return;
    try {
      await api.students.education.delete(id);
      setDetail((current) => (current ? { ...current, education_history: (current.education_history ?? []).filter((record) => record.id !== id) } : current));
    } catch (error: unknown) {
      setEducationMessage(getApiErrorMessage(error, 'Education record could not be deleted.'));
    }
  };

  const handleExperienceSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedCompany = experienceForm.company_name.trim();
    const trimmedTitle = experienceForm.position_title.trim();
    if (!trimmedCompany || !trimmedTitle || !experienceForm.start_date) {
      setExperienceMessage('Company, role, and start date are required.');
      return;
    }
    if (!experienceForm.is_current && !experienceForm.end_date) {
      setExperienceMessage('Completed roles require an end date.');
      return;
    }

    setExperienceSaving(true);
    setExperienceMessage('');

    try {
      const payload = {
        company_name: trimmedCompany,
        position_title: trimmedTitle,
        employment_type: experienceForm.employment_type,
        location: experienceForm.location,
        country: experienceForm.country || null,
        start_date: experienceForm.start_date,
        end_date: experienceForm.is_current ? null : experienceForm.end_date || null,
        is_current: experienceForm.is_current,
        description: experienceForm.description,
        skills_used: experienceForm.skills_used.split(',').map((skill) => skill.trim()).filter(Boolean),
      };

      if (experienceEditingId) {
        const updated = await api.students.experience.update(experienceEditingId, payload);
        setDetail((current) => (current ? { ...current, work_experience: (current.work_experience ?? []).map((record) => record.id === updated.id ? updated : record) } : current));
      } else {
        const created = await api.students.experience.create(payload);
        setDetail((current) => (current ? { ...current, work_experience: [created, ...(current.work_experience ?? [])] } : current));
      }

      setExperienceForm(EMPTY_EXPERIENCE_FORM);
      setExperienceEditingId(null);
      setExperienceMessage(experienceEditingId ? 'Work experience updated.' : 'Work experience added.');
    } catch (error: unknown) {
      setExperienceMessage(getApiErrorMessage(error, 'Work experience could not be saved.'));
    } finally {
      setExperienceSaving(false);
    }
  };

  const handleEditExperience = (record: WorkExperienceApiRecord) => {
    setExperienceEditingId(record.id);
    setExperienceForm({
      company_name: record.company_name,
      position_title: record.position_title,
      employment_type: record.employment_type,
      location: record.location,
      country: record.country ?? '',
      start_date: record.start_date,
      end_date: record.end_date ?? '',
      is_current: record.is_current,
      description: record.description,
      skills_used: Array.isArray(record.skills_used) ? record.skills_used.join(', ') : '',
    });
  };

  const handleDeleteExperience = async (id: string) => {
    if (!window.confirm('Remove this work experience record?')) return;
    try {
      await api.students.experience.delete(id);
      setDetail((current) => (current ? { ...current, work_experience: (current.work_experience ?? []).filter((record) => record.id !== id) } : current));
    } catch (error: unknown) {
      setExperienceMessage(getApiErrorMessage(error, 'Work experience could not be deleted.'));
    }
  };

  const handleSkillSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedSkill = skillForm.name.trim();
    if (!trimmedSkill) {
      setSkillMessage('Skill name is required.');
      return;
    }

    const duplicateSkill = (detail?.skills ?? []).some(
      (skill) => skill.id !== skillEditingId && skill.name.toLowerCase() === trimmedSkill.toLowerCase()
    );
    if (duplicateSkill) {
      setSkillMessage('This skill is already on your profile.');
      return;
    }

    setSkillSaving(true);
    setSkillMessage('');

    try {
      const payload = {
        name: trimmedSkill,
        category: skillForm.category,
        proficiency: skillForm.proficiency,
        years_of_experience: skillForm.years_of_experience ? Number(skillForm.years_of_experience) : null,
      };

      if (skillEditingId) {
        const updated = await api.students.skills.update(skillEditingId, payload);
        setDetail((current) => (current ? { ...current, skills: (current.skills ?? []).map((record) => record.id === updated.id ? updated : record) } : current));
        setSkillMessage('Skill updated.');
      } else {
        const created = await api.students.skills.create(payload);
        setDetail((current) => (current ? { ...current, skills: [created, ...(current.skills ?? [])] } : current));
        setSkillMessage('Skill added.');
      }

      setSkillForm(EMPTY_SKILL_FORM);
      setSkillEditingId(null);
    } catch (error: unknown) {
      setSkillMessage(getApiErrorMessage(error, skillEditingId ? 'Skill could not be updated.' : 'Skill could not be added.'));
    } finally {
      setSkillSaving(false);
    }
  };

  const handleEditSkill = (record: SkillApiRecord) => {
    setSkillEditingId(record.id);
    setSkillForm({
      name: record.name,
      category: record.category,
      proficiency: record.proficiency,
      years_of_experience: record.years_of_experience !== null && record.years_of_experience !== undefined ? String(record.years_of_experience) : '',
    });
    setSkillMessage('');
  };

  const handleCancelSkillEdit = () => {
    setSkillEditingId(null);
    setSkillForm(EMPTY_SKILL_FORM);
    setSkillMessage('');
  };

  const handleDeleteSkill = async (id: string) => {
    if (!window.confirm('Remove this skill?')) return;
    try {
      await api.students.skills.delete(id);
      setDetail((current) => (current ? { ...current, skills: (current.skills ?? []).filter((record) => record.id !== id) } : current));
      if (skillEditingId === id) {
        handleCancelSkillEdit();
      }
    } catch (error: unknown) {
      setSkillMessage(getApiErrorMessage(error, 'Skill could not be removed.'));
    }
  };

  const handleDocumentUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const selectedFile = documentForm.file;
    if (!selectedFile) {
      setDocumentError('Please select a file to upload.');
      return;
    }

    const extension = selectedFile.name.split('.').pop()?.toLowerCase();
    if (!extension || !VALID_DOCUMENT_EXTENSIONS.includes(extension)) {
      setDocumentError('Unsupported file type. Allowed: PDF, DOC, DOCX, JPG, JPEG, PNG.');
      return;
    }

    if (selectedFile.size > MAX_DOCUMENT_BYTES) {
      setDocumentError('File size must be 10MB or less.');
      return;
    }

    setUploadingDocument(true);
    setDocumentError('');
    setDocumentMessage('');

    try {
      const formData = new FormData();
      formData.append('document_type', documentForm.document_type);
      formData.append('title', documentForm.title.trim() || selectedFile.name);
      formData.append('description', documentForm.description.trim());
      if (documentForm.expiry_date) formData.append('expiry_date', documentForm.expiry_date);
      formData.append('file', selectedFile);

      const createdDocument = await api.documents.create(formData, (progress) => {
        if (progress.total && progress.total > 0) {
          setUploadProgress(Math.round((progress.loaded / progress.total) * 100));
        }
      });

      setDocuments((current) => [createdDocument, ...current]);
      setDocumentForm(EMPTY_DOCUMENT_FORM);
      setUploadProgress(0);
      setDocumentMessage('Document uploaded successfully.');
    } catch (error: unknown) {
      setDocumentError(getApiErrorMessage(error, 'Document upload failed.'));
    } finally {
      setUploadingDocument(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (!window.confirm('Delete this document? This action cannot be undone.')) return;
    try {
      await api.documents.delete(documentId);
      setDocuments((current) => current.filter((record) => record.id !== documentId));
      setDocumentMessage('Document deleted.');
    } catch (error: unknown) {
      setDocumentError(getApiErrorMessage(error, 'Document could not be deleted.'));
    }
  };

  const handleDownloadDocument = async (documentRecord: DocumentApiRecord) => {
    try {
      const blob = await api.documents.download(documentRecord.id);
      const objectUrl = window.URL.createObjectURL(blob);
      const link = window.document.createElement('a');
      const safeFilename = (documentRecord.file || `${documentRecord.title || 'document'}.${documentRecord.file_extension || 'bin'}`)
        .split('/')
        .pop() || `${documentRecord.title || 'document'}.${documentRecord.file_extension || 'bin'}`;

      link.href = objectUrl;
      link.download = safeFilename;
      link.rel = 'noopener';
      window.document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 1000);
    } catch (error: unknown) {
      setDocumentError(getApiErrorMessage(error, 'Document download failed. Please verify you are signed in and have access to this file.'));
    }
  };

  let content;
  if (loading) {
    content = <p className="py-16 text-center text-gray-600" role="status">Loading your profile…</p>;
  } else if (loadError) {
    content = (
      <div className="py-16 text-center" role="alert">
        <h1 className="text-2xl font-bold text-gray-900">Profile unavailable</h1>
        <p className="mt-2 text-gray-600">{loadError}</p>
        <Button
          className="mt-5"
          onClick={() => {
            setLoading(true);
            setLoadError('');
            setRetryKey((key) => key + 1);
          }}
        >
          Try Again
        </Button>
      </div>
    );
  } else if (profile) {
    content = (
      <>
        <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <Link href="/student" className="text-sm font-medium text-primary-700 hover:underline">Student Portal</Link>
            <h1 className="mt-2 text-3xl font-bold text-gray-900">My Student Profile</h1>
            <p className="mt-2 text-gray-600">Keep your information current for scholarship matching and application support.</p>
          </div>
          {completion && (
            <div className="min-w-48 rounded-lg bg-white p-4 shadow-sm" aria-live="polite">
              <p className="text-sm font-medium text-gray-700">Profile completion</p>
              <p className="mt-1 text-xl font-bold text-primary-800">{Math.round(completion.percentage)}%</p>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-gray-200">
                <div className="h-full rounded-full bg-brand-gold" style={{ width: `${completion.percentage}%` }} />
              </div>
            </div>
          )}
        </header>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Personal information</CardTitle>
              <CardDescription>Private details used to personalize your account and eligibility results.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5 sm:grid-cols-2">
              <Input label="Date of birth" type="date" value={profile.date_of_birth ?? ''} onChange={(event) => update('date_of_birth', event.target.value || null)} />
              <Input label="Gender (optional)" value={profile.gender} onChange={(event) => update('gender', event.target.value)} />
              <div>
                <label htmlFor="nationality-country" className="mb-1.5 block text-sm font-medium text-gray-700">Nationality</label>
                <select id="nationality-country" value={profile.nationality_country ?? ''} onChange={(event) => update('nationality_country', event.target.value || null)} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                  <option value="">Select a country</option>
                  {countries.map((country) => <option key={country.code} value={country.code}>{country.flag_emoji} {country.name}</option>)}
                </select>
              </div>
              <Input label="Passport number (optional)" value={profile.passport_number} onChange={(event) => update('passport_number', event.target.value)} autoComplete="off" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Contact and residence</CardTitle>
              <CardDescription>Your residential country is separate from your nationality.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5 sm:grid-cols-2">
              <Input label="City" value={profile.city} onChange={(event) => update('city', event.target.value)} />
              <div>
                <label htmlFor="residence-country" className="mb-1.5 block text-sm font-medium text-gray-700">Country of residence</label>
                <select id="residence-country" value={profile.residence_country ?? ''} onChange={(event) => update('residence_country', event.target.value || null)} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                  <option value="">Select a country</option>
                  {countries.map((country) => <option key={country.code} value={country.code}>{country.flag_emoji} {country.name}</option>)}
                </select>
              </div>
              <Input label="Postal code" value={profile.postal_code} onChange={(event) => update('postal_code', event.target.value)} />
              <label className="sm:col-span-2">
                <span className="mb-1.5 block text-sm font-medium text-gray-700">Address</span>
                <textarea value={profile.address} onChange={(event) => update('address', event.target.value)} rows={2} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600" />
              </label>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Education and study goals</CardTitle>
              <CardDescription>These structured details inform personalized scholarship matches.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5 sm:grid-cols-2">
              <div>
                <label htmlFor="education-level" className="mb-1.5 block text-sm font-medium text-gray-700">Current education level</label>
                <select id="education-level" value={profile.current_education_level} onChange={(event) => update('current_education_level', event.target.value as StudentProfileApiRecord['current_education_level'])} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                  {EDUCATION_LEVELS.map((level) => <option key={level} value={level}>{labelFor(level)}</option>)}
                </select>
              </div>
              <Input label="School or university" value={profile.school_name} onChange={(event) => update('school_name', event.target.value)} />
              <Input label="Field of study" value={profile.field_of_study} onChange={(event) => update('field_of_study', event.target.value)} />
              <Input label="Graduation year" type="number" min={1950} max={2050} value={profile.graduation_year ?? ''} onChange={(event) => update('graduation_year', parseInteger(event.target.value))} />
              <Input label="GPA (0–4 scale)" type="number" min={0} max={4} step="0.01" value={profile.gpa ?? ''} onChange={(event) => update('gpa', event.target.value || null)} />
              <Input label="Target degree level" value={profile.target_degree_level} onChange={(event) => update('target_degree_level', event.target.value)} />
              <div className="sm:col-span-2">
                <label htmlFor="target-countries" className="mb-1.5 block text-sm font-medium text-gray-700">Countries you are considering</label>
                <select id="target-countries" multiple value={profile.target_countries} onChange={(event) => update('target_countries', Array.from(event.target.selectedOptions, (option) => option.value))} className="min-h-36 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                  {countries.map((country) => <option key={country.code} value={country.code}>{country.flag_emoji} {country.name}</option>)}
                </select>
                <p className="mt-1 text-sm text-gray-500">Select multiple countries with Ctrl (Windows) or Command (Mac).</p>
              </div>
              <Input label="Preferred fields (comma-separated)" value={profile.preferred_fields.join(', ')} onChange={(event) => update('preferred_fields', event.target.value.split(',').map((field) => field.trim()).filter(Boolean))} />
              <Input label="Budget range (optional)" value={profile.budget_range} onChange={(event) => update('budget_range', event.target.value)} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Test scores and emergency contact</CardTitle>
              <CardDescription>Only provide information you are comfortable storing in your account.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5 sm:grid-cols-2">
              <Input label="English test (IELTS, TOEFL, DET…)" value={profile.english_test_type} onChange={(event) => update('english_test_type', event.target.value)} />
              <Input label="English test score" value={profile.english_test_score} onChange={(event) => update('english_test_score', event.target.value)} />
              <Input label="GRE score" type="number" min={0} value={profile.gre_score ?? ''} onChange={(event) => update('gre_score', parseInteger(event.target.value))} />
              <Input label="GMAT score" type="number" min={0} value={profile.gmat_score ?? ''} onChange={(event) => update('gmat_score', parseInteger(event.target.value))} />
              <Input label="SAT score" type="number" min={0} value={profile.sat_score ?? ''} onChange={(event) => update('sat_score', parseInteger(event.target.value))} />
              <Input label="Emergency contact name" value={profile.emergency_contact_name} onChange={(event) => update('emergency_contact_name', event.target.value)} />
              <Input label="Emergency contact phone" type="tel" value={profile.emergency_contact_phone} onChange={(event) => update('emergency_contact_phone', event.target.value)} />
              <Input label="Relationship" value={profile.emergency_contact_relationship} onChange={(event) => update('emergency_contact_relationship', event.target.value)} />
            </CardContent>
          </Card>

          {saveError && <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800" role="alert">{saveError}</p>}
          {saved && <p className="rounded-lg border border-green-200 bg-green-50 p-4 text-green-800" role="status">Your profile was saved.</p>}
          <div className="flex flex-wrap gap-3">
            <Button type="submit" isLoading={saving}>Save Profile</Button>
            <Link href="/student"><Button type="button" variant="outline">Back to Student Portal</Button></Link>
          </div>
        </form>

        <div className="mt-8 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Upload className="h-5 w-5" />Document Management</CardTitle>
              <CardDescription>Upload, review, and manage your personal documents securely.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <form onSubmit={handleDocumentUpload} className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Document type</label>
                  <select value={documentForm.document_type} onChange={(event) => setDocumentForm((current) => ({ ...current, document_type: event.target.value as DocumentApiRecord['document_type'] }))} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                    {['PASSPORT', 'TRANSCRIPT', 'DIPLOMA', 'RECOMMENDATION', 'PERSONAL_STATEMENT', 'CV', 'FINANCIAL', 'TEST_SCORE', 'PHOTO', 'OTHER'].map((type) => (
                      <option key={type} value={type}>{type.replaceAll('_', ' ')}</option>
                    ))}
                  </select>
                </div>
                <Input label="Title" value={documentForm.title} onChange={(event) => setDocumentForm((current) => ({ ...current, title: event.target.value }))} placeholder="For example: IELTS score report" />
                <div className="md:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Description</label>
                  <textarea value={documentForm.description} onChange={(event) => setDocumentForm((current) => ({ ...current, description: event.target.value }))} rows={3} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600" />
                </div>
                <Input label="Expiry date (optional)" type="date" value={documentForm.expiry_date} onChange={(event) => setDocumentForm((current) => ({ ...current, expiry_date: event.target.value }))} />
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Select file</label>
                  <input type="file" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png" onChange={(event: ChangeEvent<HTMLInputElement>) => setDocumentForm((current) => ({ ...current, file: event.target.files?.[0] ?? null }))} className="block w-full text-sm text-gray-700 file:mr-4 file:rounded-md file:border-0 file:bg-primary-100 file:px-4 file:py-2 file:text-sm file:font-medium file:text-primary-700" />
                  <p className="mt-1 text-xs text-gray-500">Allowed: PDF, DOC, DOCX, JPG, PNG • max 10MB</p>
                </div>
                <div className="md:col-span-2 flex flex-wrap items-center gap-3">
                  <Button type="submit" isLoading={uploadingDocument} variant="primary">
                    <Upload className="h-4 w-4" /> Upload Document
                  </Button>
                  {uploadingDocument && <span className="text-sm text-gray-600">Uploading {uploadProgress}%</span>}
                </div>
              </form>

              {documentError && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{documentError}</p>}
              {documentMessage && <p className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800">{documentMessage}</p>}

              <div className="space-y-3">
                {documents.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-5 text-sm text-gray-600">No documents uploaded yet.</div>
                ) : documents.map((document) => (
                  <div key={document.id} className="flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-4 md:flex-row md:items-center md:justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-primary-700" />
                        <span className="font-semibold text-gray-900">{document.title}</span>
                      </div>
                      <p className="text-sm text-gray-600">{document.document_type.replaceAll('_', ' ')} • {document.file_extension.toUpperCase()} • {document.file_size_mb}MB</p>
                      <p className="text-xs text-gray-500">Status: <span className="font-medium">{document.status}</span> • Uploaded {new Date(document.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button type="button" variant="outline" size="sm" onClick={() => handleDownloadDocument(document)}>
                        <Download className="h-4 w-4" /> Download
                      </Button>
                      <Button type="button" variant="danger" size="sm" onClick={() => handleDeleteDocument(document.id)}>
                        <Trash2 className="h-4 w-4" /> Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><BookOpen className="h-5 w-5" />Education History</CardTitle>
              <CardDescription>Track your academic background and qualifications.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <form onSubmit={handleEducationSubmit} className="grid gap-4 md:grid-cols-2">
                <Input label="Institution" value={educationForm.institution_name} onChange={(event) => setEducationForm((current) => ({ ...current, institution_name: event.target.value }))} />
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Degree level</label>
                  <select value={educationForm.degree_level} onChange={(event) => setEducationForm((current) => ({ ...current, degree_level: event.target.value as EducationApiRecord['degree_level'] }))} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                    {['HIGH_SCHOOL', 'ASSOCIATE', 'BACHELOR', 'MASTER', 'DOCTORATE', 'DIPLOMA', 'CERTIFICATE'].map((level) => (
                      <option key={level} value={level}>{labelFor(level)}</option>
                    ))}
                  </select>
                </div>
                <Input label="Field of study" value={educationForm.field_of_study} onChange={(event) => setEducationForm((current) => ({ ...current, field_of_study: event.target.value }))} />
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Country</label>
                  <select value={educationForm.country} onChange={(event) => setEducationForm((current) => ({ ...current, country: event.target.value }))} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                    <option value="">Select a country</option>
                    {countries.map((country) => <option key={country.code} value={country.code}>{country.flag_emoji} {country.name}</option>)}
                  </select>
                </div>
                <Input label="Start date" type="date" value={educationForm.start_date} onChange={(event) => setEducationForm((current) => ({ ...current, start_date: event.target.value }))} />
                <Input label="End date" type="date" value={educationForm.end_date} disabled={educationForm.is_current} onChange={(event) => setEducationForm((current) => ({ ...current, end_date: event.target.value }))} />
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 md:col-span-2">
                  <input type="checkbox" checked={educationForm.is_current} onChange={(event) => setEducationForm((current) => ({ ...current, is_current: event.target.checked, end_date: event.target.checked ? '' : current.end_date }))} />
                  I am currently studying here
                </label>
                <Input label="GPA" type="number" min="0" max="10" step="0.01" value={educationForm.gpa} onChange={(event) => setEducationForm((current) => ({ ...current, gpa: event.target.value }))} />
                <Input label="GPA scale" type="number" min="1" max="10" step="0.1" value={educationForm.gpa_scale} onChange={(event) => setEducationForm((current) => ({ ...current, gpa_scale: event.target.value }))} />
                <Input label="Achievements" value={educationForm.achievements} onChange={(event) => setEducationForm((current) => ({ ...current, achievements: event.target.value }))} className="md:col-span-2" />
                <label className="md:col-span-2">
                  <span className="mb-1.5 block text-sm font-medium text-gray-700">Notes</span>
                  <textarea value={educationForm.description} onChange={(event) => setEducationForm((current) => ({ ...current, description: event.target.value }))} rows={3} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600" />
                </label>
                <div className="md:col-span-2 flex flex-wrap gap-3">
                  <Button type="submit" isLoading={educationSaving}>
                    {educationEditingId ? 'Update Education' : 'Add Education'}
                  </Button>
                  {educationEditingId && (
                    <Button type="button" variant="outline" onClick={() => { setEducationEditingId(null); setEducationForm(EMPTY_EDUCATION_FORM); }}>
                      Cancel
                    </Button>
                  )}
                </div>
              </form>

              {educationMessage && <p className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">{educationMessage}</p>}

              <div className="space-y-3">
                {detail?.education_history?.length ? detail.education_history.map((record) => (
                  <div key={record.id} className="rounded-xl border border-gray-200 bg-white p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900">{record.institution_name}</h3>
                        <p className="text-sm text-gray-600">{labelFor(record.degree_level)} • {record.field_of_study}</p>
                        <p className="mt-1 text-sm text-gray-500">{toDateLabel(record.start_date)} – {record.is_current ? 'Present' : toDateLabel(record.end_date)}</p>
                        {record.gpa ? <p className="mt-1 text-sm text-gray-500">GPA: {record.gpa} / {record.gpa_scale}</p> : null}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button type="button" variant="outline" size="sm" onClick={() => handleEditEducation(record)}>
                          <PencilLine className="h-4 w-4" /> Edit
                        </Button>
                        <Button type="button" variant="danger" size="sm" onClick={() => handleDeleteEducation(record.id)}>
                          <Trash2 className="h-4 w-4" /> Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                )) : <p className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-5 text-sm text-gray-600">No education history yet.</p> }
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><BriefcaseBusiness className="h-5 w-5" />Work Experience</CardTitle>
              <CardDescription>Record your professional background and current employment.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <form onSubmit={handleExperienceSubmit} className="grid gap-4 md:grid-cols-2">
                <Input label="Company name" value={experienceForm.company_name} onChange={(event) => setExperienceForm((current) => ({ ...current, company_name: event.target.value }))} />
                <Input label="Job title" value={experienceForm.position_title} onChange={(event) => setExperienceForm((current) => ({ ...current, position_title: event.target.value }))} />
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Employment type</label>
                  <select value={experienceForm.employment_type} onChange={(event) => setExperienceForm((current) => ({ ...current, employment_type: event.target.value as WorkExperienceApiRecord['employment_type'] }))} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                    {['FULL_TIME', 'PART_TIME', 'INTERNSHIP', 'CONTRACT', 'FREELANCE', 'VOLUNTEER'].map((type) => <option key={type} value={type}>{labelFor(type)}</option>)}
                  </select>
                </div>
                <Input label="Location" value={experienceForm.location} onChange={(event) => setExperienceForm((current) => ({ ...current, location: event.target.value }))} />
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Country</label>
                  <select value={experienceForm.country} onChange={(event) => setExperienceForm((current) => ({ ...current, country: event.target.value }))} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                    <option value="">Select a country</option>
                    {countries.map((country) => <option key={country.code} value={country.code}>{country.flag_emoji} {country.name}</option>)}
                  </select>
                </div>
                <Input label="Start date" type="date" value={experienceForm.start_date} onChange={(event) => setExperienceForm((current) => ({ ...current, start_date: event.target.value }))} />
                <Input label="End date" type="date" value={experienceForm.end_date} disabled={experienceForm.is_current} onChange={(event) => setExperienceForm((current) => ({ ...current, end_date: event.target.value }))} />
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 md:col-span-2">
                  <input type="checkbox" checked={experienceForm.is_current} onChange={(event) => setExperienceForm((current) => ({ ...current, is_current: event.target.checked, end_date: event.target.checked ? '' : current.end_date }))} />
                  I am currently employed in this role
                </label>
                <label className="md:col-span-2">
                  <span className="mb-1.5 block text-sm font-medium text-gray-700">Responsibilities and achievements</span>
                  <textarea value={experienceForm.description} onChange={(event) => setExperienceForm((current) => ({ ...current, description: event.target.value }))} rows={3} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600" />
                </label>
                <Input label="Skills used (comma-separated)" value={experienceForm.skills_used} onChange={(event) => setExperienceForm((current) => ({ ...current, skills_used: event.target.value }))} className="md:col-span-2" />
                <div className="md:col-span-2 flex flex-wrap gap-3">
                  <Button type="submit" isLoading={experienceSaving}>
                    {experienceEditingId ? 'Update Experience' : 'Add Experience'}
                  </Button>
                  {experienceEditingId && (
                    <Button type="button" variant="outline" onClick={() => { setExperienceEditingId(null); setExperienceForm(EMPTY_EXPERIENCE_FORM); }}>
                      Cancel
                    </Button>
                  )}
                </div>
              </form>

              {experienceMessage && <p className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">{experienceMessage}</p>}

              <div className="space-y-3">
                {detail?.work_experience?.length ? detail.work_experience.map((record) => (
                  <div key={record.id} className="rounded-xl border border-gray-200 bg-white p-4">
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900">{record.position_title}</h3>
                        <p className="text-sm text-gray-600">{record.company_name} • {labelFor(record.employment_type)}</p>
                        <p className="mt-1 text-sm text-gray-500">{toDateLabel(record.start_date)} – {record.is_current ? 'Present' : toDateLabel(record.end_date)}</p>
                        {record.description ? <p className="mt-2 text-sm text-gray-700">{record.description}</p> : null}
                        {record.skills_used.length > 0 && <p className="mt-2 text-xs text-gray-500">Skills: {record.skills_used.join(', ')}</p>}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button type="button" variant="outline" size="sm" onClick={() => handleEditExperience(record)}>
                          <PencilLine className="h-4 w-4" /> Edit
                        </Button>
                        <Button type="button" variant="danger" size="sm" onClick={() => handleDeleteExperience(record.id)}>
                          <Trash2 className="h-4 w-4" /> Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                )) : <p className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-5 text-sm text-gray-600">No work experience added yet.</p> }
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Award className="h-5 w-5" />Skills</CardTitle>
              <CardDescription>List your strongest skills to improve opportunity matching.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <form onSubmit={handleSkillSubmit} className="grid gap-4 md:grid-cols-3">
                <Input label="Skill name" value={skillForm.name} onChange={(event) => setSkillForm((current) => ({ ...current, name: event.target.value }))} />
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Category</label>
                  <select value={skillForm.category} onChange={(event) => setSkillForm((current) => ({ ...current, category: event.target.value as SkillApiRecord['category'] }))} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                    {['TECHNICAL', 'LANGUAGE', 'SOFT_SKILL', 'ACADEMIC', 'OTHER'].map((category) => <option key={category} value={category}>{labelFor(category)}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">Proficiency</label>
                  <select value={skillForm.proficiency} onChange={(event) => setSkillForm((current) => ({ ...current, proficiency: event.target.value as SkillApiRecord['proficiency'] }))} className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-gray-900 focus:border-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-600">
                    {['BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT'].map((level) => <option key={level} value={level}>{labelFor(level)}</option>)}
                  </select>
                </div>
                <Input label="Years of experience" type="number" min="0" max="50" value={skillForm.years_of_experience} onChange={(event) => setSkillForm((current) => ({ ...current, years_of_experience: event.target.value }))} className="md:col-span-2" />
                <div className="flex flex-wrap items-end gap-2">
                  <Button type="submit" isLoading={skillSaving}>{skillEditingId ? 'Update Skill' : 'Add Skill'}</Button>
                  {skillEditingId && (
                    <Button type="button" variant="outline" onClick={handleCancelSkillEdit}>Cancel</Button>
                  )}
                </div>
              </form>

              {skillMessage && <p className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">{skillMessage}</p>}

              <div className="flex flex-wrap gap-2">
                {detail?.skills?.length ? detail.skills.map((skill) => (
                  <div key={skill.id} className="inline-flex items-center gap-2 rounded-full border border-primary-200 bg-primary-50 px-3 py-2 text-sm text-primary-800">
                    <span>{skill.name}</span>
                    <button type="button" aria-label={`Edit ${skill.name}`} onClick={() => handleEditSkill(skill)} className="text-primary-700 hover:text-primary-900" title="Edit skill">
                      <PencilLine className="h-4 w-4" />
                    </button>
                    <button type="button" aria-label={`Remove ${skill.name}`} onClick={() => handleDeleteSkill(skill.id)} className="text-primary-700 hover:text-primary-900" title="Remove skill">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                )) : <p className="w-full rounded-xl border border-dashed border-gray-300 bg-gray-50 p-5 text-sm text-gray-600">No skills added yet.</p> }
              </div>
            </CardContent>
          </Card>
        </div>
      </>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Navigation />
      <main id="main-content" tabIndex={-1} className="flex-1 bg-gray-50 px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">{content}</div>
      </main>
      <Footer />
    </div>
  );
}
