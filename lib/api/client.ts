/**
 * API client for GOFER EXAM.
 * Browser sessions use HttpOnly JWT cookies and a CSRF token kept in memory.
 */

import axios, {
  AxiosError,
  AxiosInstance,
  InternalAxiosRequestConfig,
} from 'axios';

const API_BASE_URL = '/api/v1';

export interface VerifiedSourceApiRecord {
  url: string;
  organization: string;
  verified_at: string;
  verified_by: string;
}

export interface ScholarshipApiRecord {
  id: string;
  slug: string;
  name: string;
  short_description: string;
  description?: string;
  provider: string;
  country: string;
  type: string;
  level: string;
  amount: string;
  amount_type: string;
  application_deadline: string;
  application_url?: string;
  website_url?: string;
  status: string;
  is_featured: boolean;
  eligibility?: string[];
  fields?: string[];
  nationality_eligibility?: 'ALL' | 'SPECIFIC' | 'NOT_CONFIRMED';
  target_countries?: string[];
  excluded_countries?: string[];
  documents_required?: string[];
  verified_sources?: VerifiedSourceApiRecord[];
}

export interface UniversityApiRecord {
  id: string;
  slug: string;
  name: string;
  country: string;
  city: string;
  type: string;
  description?: string;
  world_ranking: number | null;
  total_students: number;
  international_students: number;
  international_student_percentage: number;
  tuition_fee: string | null;
  national_ranking?: number | null;
  founded_year?: number | null;
  acceptance_rate?: string | null;
  application_fee?: string;
  minimum_gpa?: string | null;
  is_featured: boolean;
  is_partner: boolean;
  website_url?: string;
  programs?: string[];
  popular_majors?: string[];
  required_tests?: string[];
  address?: string;
  image?: string | null;
  logo?: string | null;
}

export interface DestinationApiRecord {
  id: string;
  slug: string;
  name: string;
  flag_emoji: string;
  description: string;
  total_universities: number;
  international_students: number;
  is_popular: boolean;
  is_featured: boolean;
  average_tuition_fee: string;
  average_living_cost: string;
  primary_language: string;
  highlights?: string[];
  work_while_studying?: boolean;
  work_hours_per_week?: number;
  post_study_work_visa?: boolean;
  post_study_work_duration?: string;
  required_tests?: string[];
  scholarship_availability?: string;
  visa_processing_time?: string;
  official_education_website?: string;
  embassy_website?: string;
}

export interface ServiceApiRecord {
  id: string;
  slug: string;
  title: string;
  description: string;
  short_description: string;
  category: string;
  price: string;
  currency: string;
  duration: string;
  features: string[];
  is_featured: boolean;
  image: string | null;
}

export interface OpportunityApiRecord {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  description: string;
  organization: string;
  country: string;
  location: string;
  category: 'JOB' | 'INTERNSHIP' | 'FELLOWSHIP' | 'EXCHANGE' | 'TRAINING' | 'RESEARCH' | 'COMPETITION' | 'GRANT' | 'OTHER';
  level: 'HIGH_SCHOOL' | 'UNDERGRADUATE' | 'GRADUATE' | 'POSTGRADUATE' | 'DOCTORATE' | 'ALL_LEVELS';
  eligibility: string[];
  eligibility_scope?: 'UNSPECIFIED' | 'ETHIOPIA_ONLY' | 'ETHIOPIA_AND_OTHERS' | 'OTHER_NATIONALITIES';
  eligible_nationalities?: string[];
  excluded_nationalities?: string[];
  eligibility_notes?: string;
  benefits: string[];
  documents_required?: string[];
  required_skills: string[];
  employment_type: 'UNKNOWN' | 'FULL_TIME' | 'PART_TIME' | 'CONTRACT' | 'TEMPORARY' | 'OTHER';
  work_mode: 'UNKNOWN' | 'ON_SITE' | 'HYBRID' | 'REMOTE';
  compensation_status: 'UNKNOWN' | 'PAID' | 'UNPAID';
  compensation_amount: string | null;
  compensation_currency: string;
  compensation_period: 'HOURLY' | 'MONTHLY' | 'ANNUAL' | 'PROJECT' | 'OTHER' | '';
  duration: string;
  experience_requirement: string;
  minimum_experience_years: number | null;
  verified_sources: VerifiedSourceApiRecord[];
  application_deadline: string | null;
  application_url: string;
  official_website: string;
  status: 'UPCOMING' | 'OPEN' | 'CLOSED';
  is_published: boolean;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

export interface CountryApiRecord {
  code: string;
  name: string;
  official_name: string;
  alpha3_code: string;
  flag_emoji: string;
  region: string;
  subregion: string;
}

export interface StudentProfileApiRecord {
  id: string;
  date_of_birth: string | null;
  gender: string;
  nationality: string;
  nationality_country: string | null;
  passport_number: string;
  address: string;
  city: string;
  country: string;
  residence_country: string | null;
  postal_code: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  emergency_contact_relationship: string;
  current_education_level: 'HIGH_SCHOOL' | 'UNDERGRADUATE' | 'GRADUATE' | 'POSTGRADUATE';
  school_name: string;
  field_of_study: string;
  graduation_year: number | null;
  gpa: string | null;
  target_countries: string[];
  target_degree_level: string;
  preferred_fields: string[];
  budget_range: string;
  english_test_type: string;
  english_test_score: string;
  gre_score: number | null;
  gmat_score: number | null;
  sat_score: number | null;
  profile_completed: boolean;
}

export interface EducationApiRecord {
  id: string;
  institution_name: string;
  degree_level: 'HIGH_SCHOOL' | 'ASSOCIATE' | 'BACHELOR' | 'MASTER' | 'DOCTORATE' | 'DIPLOMA' | 'CERTIFICATE';
  field_of_study: string;
  country: string | null;
  country_name?: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  gpa: string | number | null;
  gpa_scale: string | number;
  achievements: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface WorkExperienceApiRecord {
  id: string;
  company_name: string;
  position_title: string;
  employment_type: 'FULL_TIME' | 'PART_TIME' | 'INTERNSHIP' | 'CONTRACT' | 'FREELANCE' | 'VOLUNTEER';
  location: string;
  country: string | null;
  country_name?: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string;
  skills_used: string[];
  created_at: string;
  updated_at: string;
}

export interface SkillApiRecord {
  id: string;
  name: string;
  category: 'TECHNICAL' | 'LANGUAGE' | 'SOFT_SKILL' | 'ACADEMIC' | 'OTHER';
  proficiency: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED' | 'EXPERT';
  years_of_experience: number | null;
  created_at: string;
  updated_at: string;
}

export interface StudentProfileDetailApiRecord extends StudentProfileApiRecord {
  education_history: EducationApiRecord[];
  work_experience: WorkExperienceApiRecord[];
  skills: SkillApiRecord[];
}

export interface DocumentApiRecord {
  id: string;
  user?: string;
  owner_email?: string;
  owner_name?: string;
  document_type: 'PASSPORT' | 'TRANSCRIPT' | 'DIPLOMA' | 'RECOMMENDATION' | 'PERSONAL_STATEMENT' | 'CV' | 'FINANCIAL' | 'TEST_SCORE' | 'PHOTO' | 'OTHER';
  title: string;
  description: string;
  file: string;
  file_size: number;
  file_size_mb: number;
  file_extension: string;
  application?: string | null;
  consultation?: string | null;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED';
  verified_by?: string | null;
  verified_by_name?: string | null;
  verification_notes?: string | null;
  verified_at?: string | null;
  expiry_date?: string | null;
  is_expired: boolean;
  is_confidential: boolean;
  created_at: string;
  updated_at: string;
}

export interface StudentProfileCompletionApiRecord {
  percentage: number;
  is_completed: boolean;
  missing_fields: string[];
}

export interface ConsultantDirectoryApiRecord {
  consultant_id: string;
  name: string;
  company_name: string;
  job_title: string;
  years_of_experience: number;
  bio: string;
  specializations: string[];
  languages: string[];
  expertise_countries: string[];
  expertise_fields: string[];
  consultation_rate: string;
  availability_hours: string;
  timezone: string;
}

export interface ConsultationApiRecord {
  id: string;
  consultant?: string;
  consultant_name?: string;
  student_name?: string;
  student_email?: string;
  service?: string | null;
  service_title?: string;
  type: 'VIDEO' | 'PHONE' | 'IN_PERSON' | 'CHAT';
  title: string;
  description: string;
  scheduled_date: string;
  scheduled_time: string;
  duration_minutes: number;
  timezone: string;
  meeting_url: string;
  meeting_id: string;
  meeting_password: string;
  status: 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW';
  student_notes?: string;
  consultant_notes?: string;
  action_items?: string[];
  student_rating?: number | null;
  student_feedback?: string;
  created_at: string;
  updated_at: string;
}

export interface NotificationApiRecord {
  id: string;
  type: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  title: string;
  message: string;
  action_url: string;
  action_text: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface UserApiRecord {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number: string;
  role: 'STUDENT' | 'CONSULTANT' | 'ADMIN' | 'SUPERADMIN';
  is_verified: boolean;
  date_joined: string;
}

export interface ConsultantProfileApiRecord {
  company_name: string;
  job_title: string;
  years_of_experience: number;
  bio: string;
  specializations: string[];
  languages: string[];
  expertise_countries: string[];
  expertise_fields: string[];
  consultation_rate: string;
  availability_hours: string;
  timezone: string;
  verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED';
  is_available: boolean;
  is_featured: boolean;
  total_consultations: number;
  total_students_helped: number;
  average_rating: string;
  success_rate: string;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationApiRecord {
  id: string;
  application_type: 'UNIVERSITY' | 'SCHOLARSHIP';
  university: string | null;
  university_name: string | null;
  program_name: string;
  degree_level: string;
  scholarship: string | null;
  scholarship_name: string | null;
  status: 'DRAFT' | 'SUBMITTED' | 'UNDER_REVIEW' | 'ACCEPTED' | 'REJECTED' | 'WAITLISTED' | 'WITHDRAWN';
  submission_date: string | null;
  deadline_date: string | null;
  decision_date: string | null;
  application_id: string;
  application_url: string;
  notes: string;
  status_updates: Array<{
    status: string;
    note: string;
    timestamp: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface ConsultantApplicationApiRecord {
  id: string;
  student_name: string;
  student_email: string;
  application_type: 'UNIVERSITY' | 'SCHOLARSHIP';
  target_name: string;
  program_name: string;
  degree_level: string;
  status: ApplicationApiRecord['status'];
  deadline_date: string | null;
  submission_date: string | null;
  updated_at: string;
}

export interface AdminOverviewApiRecord {
  users: {
    students: number;
    consultants: number;
    administrators: number;
  };
  catalogues: {
    published_scholarships: number;
    universities: number;
    destinations: number;
    active_services: number;
  };
  applications: {
    total: number;
    by_status: Partial<Record<ApplicationApiRecord['status'], number>>;
  };
  consultations: {
    total: number;
    by_status: Record<string, number>;
  };
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface SecurityAuditEventApiRecord {
  id: number;
  action: string;
  actor_id: string | null;
  actor_role: string;
  target_id: string | null;
  target_role: string;
  details: Record<string, unknown>;
  created_at: string;
}

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
  withCredentials: true,
});

let csrfToken: string | null = null;
let currentUser: UserApiRecord | null = null;

async function getCsrfToken(): Promise<string> {
  if (!csrfToken) {
    const response = await axios.get<{ csrfToken: string }>(
      `${API_BASE_URL}/auth/csrf/`,
      { withCredentials: true, timeout: 30000 }
    );
    csrfToken = response.data.csrfToken;
  }
  return csrfToken;
}

export const clearAuth = (): void => {
  currentUser = null;
  csrfToken = null;
};

function notifyAuthChanged(): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event('gofer:auth-changed'));
  }
}

apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const method = config.method?.toUpperCase();
    if (method && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
      config.headers.set('X-CSRFToken', await getCsrfToken());
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue: Array<{
  resolve: () => void;
  reject: (reason: unknown) => void;
}> = [];

function processQueue(error: unknown = null): void {
  failedQueue.forEach((request) => {
    if (error) request.reject(error);
    else request.resolve();
  });
  failedQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;
    const url = originalRequest?.url ?? '';
    const isSessionRequest = [
      '/auth/csrf/',
      '/auth/login/',
      '/auth/register/',
      '/auth/logout/',
      '/auth/token/refresh/',
    ].some((path) => url.includes(path));

    if (
      error.response?.status !== 401
      || !originalRequest
      || originalRequest._retry
      || isSessionRequest
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    if (isRefreshing) {
      return new Promise<void>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then(() => apiClient(originalRequest));
    }

    isRefreshing = true;
    try {
      await api.auth.refreshToken();
      processQueue();
      return await apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError);
      clearAuth();
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('gofer:session-expired'));
      }
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export const api = {
  auth: {
    register: async (data: {
      email: string;
      password: string;
      password2: string;
      first_name: string;
      last_name: string;
      phone_number?: string;
    }) => {
      const response = await apiClient.post<{
        user: UserApiRecord;
        email: string;
        message: string;
        resend_cooldown_seconds: number;
      }>('/auth/register/', data);
      return response.data;
    },

    verifyEmail: async (token: string) => {
      const response = await apiClient.post<{
        status: 'verified' | 'already_verified';
        message: string;
      }>('/auth/verify-email/', { token });
      return response.data;
    },

    resendVerificationEmail: async (email: string) => {
      const response = await apiClient.post<{ message: string; cooldown_seconds: number }>(
        '/auth/resend-verification/',
        { email }
      );
      return response.data;
    },

    requestPasswordReset: async (email: string) => {
      const response = await apiClient.post<{ message: string }>(
        '/auth/password/reset/',
        { email }
      );
      return response.data;
    },

    confirmPasswordReset: async (data: {
      uid: string;
      token: string;
      new_password: string;
      new_password2: string;
    }) => {
      const response = await apiClient.post<{ message: string }>(
        '/auth/password/reset/confirm/',
        data
      );
      return response.data;
    },

    changePassword: async (data: {
      old_password: string;
      new_password: string;
      new_password2: string;
    }) => {
      const response = await apiClient.post<{ message: string }>(
        '/auth/password/change/',
        data
      );
      clearAuth();
      notifyAuthChanged();
      return response.data;
    },

    login: async (data: { email: string; password: string }) => {
      const response = await apiClient.post<{
        user: UserApiRecord;
        message: string;
      }>('/auth/login/', data);
      currentUser = response.data.user;
      notifyAuthChanged();
      return response.data;
    },

    logout: async () => {
      try {
        await apiClient.post('/auth/logout/', {});
      } finally {
        clearAuth();
        notifyAuthChanged();
      }
    },

    refreshToken: async () => {
      const response = await apiClient.post<{ message: string }>(
        '/auth/token/refresh/',
        {}
      );
      return response.data;
    },

    getCurrentUser: async () => {
      const response = await apiClient.get<UserApiRecord>('/auth/me/');
      currentUser = response.data;
      return response.data;
    },

    updateProfile: async (data: {
      first_name?: string;
      last_name?: string;
      phone_number?: string;
    }) => {
      const response = await apiClient.patch<UserApiRecord>('/auth/me/', data);
      currentUser = response.data;
      return response.data;
    },
  },

  applications: {
    list: async (params?: { page?: number }) => {
      const response = await apiClient.get<PaginatedResponse<ApplicationApiRecord>>(
        '/applications/',
        { params }
      );
      return response.data;
    },

    create: async (data: {
      application_type: 'UNIVERSITY' | 'SCHOLARSHIP';
      university?: string | null;
      scholarship?: string | null;
      program_name?: string;
      degree_level?: string;
      deadline_date?: string | null;
      application_id?: string;
      application_url?: string;
      notes?: string;
    }) => {
      const response = await apiClient.post<ApplicationApiRecord>('/applications/', data);
      return response.data;
    },

    submit: async (id: string) => {
      const response = await apiClient.post<ApplicationApiRecord>(
        `/applications/${id}/submit/`,
        {}
      );
      return response.data;
    },

    withdraw: async (id: string) => {
      const response = await apiClient.post<ApplicationApiRecord>(
        `/applications/${id}/withdraw/`,
        {}
      );
      return response.data;
    },
  },

  consultations: {
    consultants: async () => {
      const response = await apiClient.get<ConsultantDirectoryApiRecord[]>(
        '/consultations/consultants/'
      );
      return response.data;
    },
    list: async (params?: { page?: number }) => {
      const response = await apiClient.get<PaginatedResponse<ConsultationApiRecord>>(
        '/consultations/',
        { params }
      );
      return response.data;
    },
    create: async (data: {
      consultant: string;
      type: ConsultationApiRecord['type'];
      title: string;
      description?: string;
      scheduled_date: string;
      scheduled_time: string;
      duration_minutes: number;
      timezone: string;
      student_notes?: string;
    }) => {
      const response = await apiClient.post<ConsultationApiRecord>('/consultations/', data);
      return response.data;
    },
    cancel: async (id: string) => {
      const response = await apiClient.post<ConsultationApiRecord>(
        `/consultations/${id}/cancel/`,
        {}
      );
      return response.data;
    },
    feedback: async (id: string, rating: number, feedback: string) => {
      const response = await apiClient.post<ConsultationApiRecord>(
        `/consultations/${id}/feedback/`,
        { rating, feedback }
      );
      return response.data;
    },
    assigned: async (params?: {
      page?: number;
      search?: string;
      status?: ConsultationApiRecord['status'] | '';
    }) => {
      const response = await apiClient.get<PaginatedResponse<ConsultationApiRecord>>(
        '/consultations/consultant/assigned/',
        { params }
      );
      return response.data;
    },
    consultantAction: async (
      id: string,
      action: 'confirm' | 'cancel' | 'complete',
      data: { meeting_url?: string; consultant_notes?: string; action_items?: string[] } = {}
    ) => {
      const response = await apiClient.post<ConsultationApiRecord>(
        `/consultations/consultant/assigned/${id}/${action}/`,
        data
      );
      return response.data;
    },
  },

  notifications: {
    list: async (params?: { page?: number; unread?: boolean }) => {
      const response = await apiClient.get<PaginatedResponse<NotificationApiRecord>>(
        '/notifications/',
        { params }
      );
      return response.data;
    },
    unreadCount: async () => {
      const response = await apiClient.get<{ count: number }>('/notifications/unread-count/');
      return response.data.count;
    },
    markRead: async (id: string) => {
      const response = await apiClient.post<NotificationApiRecord>(
        `/notifications/${id}/read/`,
        {}
      );
      return response.data;
    },
    markAllRead: async () => {
      const response = await apiClient.post<{ updated_count: number }>(
        '/notifications/read-all/',
        {}
      );
      return response.data.updated_count;
    },
  },

  students: {
    profile: async () => {
      const response = await apiClient.get<StudentProfileApiRecord>('/students/me/');
      return response.data;
    },
    detail: async () => {
      const response = await apiClient.get<StudentProfileDetailApiRecord>('/students/me/detail/');
      return response.data;
    },
    updateProfile: async (
      data: Partial<Omit<StudentProfileApiRecord, 'id' | 'profile_completed'>>
    ) => {
      const response = await apiClient.patch<StudentProfileApiRecord>('/students/me/', data);
      return response.data;
    },
    profileCompletion: async () => {
      const response = await apiClient.get<StudentProfileCompletionApiRecord>(
        '/students/me/completion/'
      );
      return response.data;
    },
    education: {
      list: async () => {
        const response = await apiClient.get<EducationApiRecord[]>('/students/education/');
        return response.data;
      },
      create: async (data: Omit<EducationApiRecord, 'id' | 'country_name' | 'created_at' | 'updated_at'>) => {
        const response = await apiClient.post<EducationApiRecord>('/students/education/', data);
        return response.data;
      },
      update: async (id: string, data: Partial<Omit<EducationApiRecord, 'id' | 'country_name' | 'created_at' | 'updated_at'>>) => {
        const response = await apiClient.patch<EducationApiRecord>(`/students/education/${id}/`, data);
        return response.data;
      },
      delete: async (id: string) => {
        const response = await apiClient.delete(`/students/education/${id}/`);
        return response.data;
      },
    },
    experience: {
      list: async () => {
        const response = await apiClient.get<WorkExperienceApiRecord[]>('/students/experience/');
        return response.data;
      },
      create: async (data: Omit<WorkExperienceApiRecord, 'id' | 'country_name' | 'created_at' | 'updated_at'>) => {
        const response = await apiClient.post<WorkExperienceApiRecord>('/students/experience/', data);
        return response.data;
      },
      update: async (id: string, data: Partial<Omit<WorkExperienceApiRecord, 'id' | 'country_name' | 'created_at' | 'updated_at'>>) => {
        const response = await apiClient.patch<WorkExperienceApiRecord>(`/students/experience/${id}/`, data);
        return response.data;
      },
      delete: async (id: string) => {
        const response = await apiClient.delete(`/students/experience/${id}/`);
        return response.data;
      },
    },
    skills: {
      list: async () => {
        const response = await apiClient.get<SkillApiRecord[]>('/students/skills/');
        return response.data;
      },
      create: async (data: { name: string; category?: SkillApiRecord['category']; proficiency?: SkillApiRecord['proficiency']; years_of_experience?: number | null; }) => {
        const response = await apiClient.post<SkillApiRecord>('/students/skills/', data);
        return response.data;
      },
      update: async (id: string, data: Partial<Pick<SkillApiRecord, 'name' | 'category' | 'proficiency' | 'years_of_experience'>>) => {
        const response = await apiClient.patch<SkillApiRecord>(`/students/skills/${id}/`, data);
        return response.data;
      },
      delete: async (id: string) => {
        const response = await apiClient.delete(`/students/skills/${id}/`);
        return response.data;
      },
    },
  },

  documents: {
    list: async () => {
      const response = await apiClient.get<PaginatedResponse<DocumentApiRecord>>('/documents/');
      return response.data.results;
    },
    create: async (data: FormData, onUploadProgress?: (progressEvent: { loaded: number; total?: number | null }) => void) => {
      const response = await apiClient.post<DocumentApiRecord>('/documents/', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          onUploadProgress?.(progressEvent);
        },
      });
      return response.data;
    },
    update: async (id: string, data: Partial<Pick<DocumentApiRecord, 'title' | 'description' | 'document_type' | 'expiry_date' | 'is_confidential'>>) => {
      const response = await apiClient.patch<DocumentApiRecord>(`/documents/${id}/`, data);
      return response.data;
    },
    delete: async (id: string) => {
      const response = await apiClient.delete(`/documents/${id}/`);
      return response.data;
    },
    download: async (id: string) => {
      const response = await apiClient.get<Blob>(`/documents/${id}/download/`, {
        responseType: 'blob',
      });
      return response.data;
    },
  },

  consultant: {
    profile: async () => {
      const response = await apiClient.get<ConsultantProfileApiRecord>(
        '/consultations/me/'
      );
      return response.data;
    },
    updateProfile: async (data: Partial<Pick<
      ConsultantProfileApiRecord,
      | 'company_name'
      | 'job_title'
      | 'years_of_experience'
      | 'bio'
      | 'specializations'
      | 'languages'
      | 'expertise_countries'
      | 'expertise_fields'
      | 'consultation_rate'
      | 'availability_hours'
      | 'timezone'
      | 'is_available'
    >>) => {
      const response = await apiClient.patch<ConsultantProfileApiRecord>(
        '/consultations/me/',
        data
      );
      return response.data;
    },
    assignedApplications: async (params?: {
      page?: number;
      search?: string;
      status?: ConsultantApplicationApiRecord['status'] | '';
    }) => {
      const response = await apiClient.get<PaginatedResponse<ConsultantApplicationApiRecord>>(
        '/applications/consultant/assigned/',
        { params }
      );
      return response.data;
    },
    startApplicationReview: async (applicationId: string, note: string) => {
      const response = await apiClient.post<ConsultantApplicationApiRecord>(
        `/applications/consultant/assigned/${applicationId}/start-review/`,
        { note }
      );
      return response.data;
    },
  },

  admin: {
    overview: async () => {
      const response = await apiClient.get<AdminOverviewApiRecord>(
        '/applications/admin/overview/'
      );
      return response.data;
    },
    auditEvents: async (params?: { page?: number }) => {
      const response = await apiClient.get<PaginatedResponse<SecurityAuditEventApiRecord>>(
        '/auth/security/audit/',
        { params }
      );
      return response.data;
    },
  },

  scholarships: {
    list: async (params?: {
      country?: string;
      type?: string;
      funding?: string;
      level?: string;
      nationality?: string;
      status?: string;
      is_featured?: boolean;
      search?: string;
      ordering?: string;
      page?: number;
    }) => {
      const response = await apiClient.get<PaginatedResponse<ScholarshipApiRecord>>(
        '/scholarships/',
        { params }
      );
      return response.data;
    },

    eligibleForMe: async (): Promise<PersonalizedScholarshipsResponse> => {
      const response = await apiClient.get<PersonalizedScholarshipsResponse>(
        '/scholarships/eligible-for-me/'
      );
      return response.data;
    },

    get: async (slug: string) => {
      const response = await apiClient.get<ScholarshipApiRecord>(
        `/scholarships/${slug}/`
      );
      return response.data;
    },
  },

  universities: {
    list: async (params?: {
      country?: string;
      city?: string;
      type?: string;
      is_featured?: boolean;
      is_partner?: boolean;
      search?: string;
      ordering?: string;
      page?: number;
    }) => {
      const response = await apiClient.get<PaginatedResponse<UniversityApiRecord>>(
        '/universities/',
        { params }
      );
      return response.data;
    },

    get: async (slug: string) => {
      const response = await apiClient.get<UniversityApiRecord>(
        `/universities/${slug}/`
      );
      return response.data;
    },
  },

  destinations: {
    list: async (params?: {
      is_popular?: boolean;
      is_featured?: boolean;
      english_required?: boolean;
      work_while_studying?: boolean;
      search?: string;
      ordering?: string;
      page?: number;
    }) => {
      const response = await apiClient.get<PaginatedResponse<DestinationApiRecord>>(
        '/destinations/',
        { params }
      );
      return response.data;
    },

    get: async (slug: string) => {
      const response = await apiClient.get<DestinationApiRecord>(
        `/destinations/${slug}/`
      );
      return response.data;
    },
  },

  services: {
    list: async (params?: {
      category?: string;
      is_featured?: boolean;
      search?: string;
      ordering?: string;
      page?: number;
    }) => {
      const response = await apiClient.get<PaginatedResponse<ServiceApiRecord>>(
        '/services/',
        { params }
      );
      return response.data;
    },

    get: async (slug: string) => {
      const response = await apiClient.get<ServiceApiRecord>(
        `/services/${slug}/`
      );
      return response.data;
    },
  },

  opportunities: {
    list: async (params?: {
      category?: OpportunityApiRecord['category'];
      country?: string;
      level?: OpportunityApiRecord['level'];
      education?: OpportunityApiRecord['level'];
      nationality?: string;
      funding?: OpportunityApiRecord['compensation_status'];
      employment_type?: OpportunityApiRecord['employment_type'];
      work_mode?: OpportunityApiRecord['work_mode'];
      search?: string;
      page?: number;
      ordering?: string;
    }) => {
      const response = await apiClient.get<PaginatedResponse<OpportunityApiRecord>>(
        '/opportunities/',
        { params }
      );
      return response.data;
    },

    get: async (slug: string) => {
      const response = await apiClient.get<OpportunityApiRecord>(
        `/opportunities/${slug}/`
      );
      return response.data;
    },
  },

  countries: {
    list: async () => {
      const response = await apiClient.get<CountryApiRecord[]>('/countries/');
      return response.data;
    },
    users: async (params?: { page?: number }) => {
      const response = await apiClient.get<PaginatedResponse<UserApiRecord>>(
        '/auth/users/',
        { params }
      );
      return response.data;
    },
    updateUser: async (
      userId: string,
      data: Partial<Pick<UserApiRecord, 'first_name' | 'last_name' | 'phone_number' | 'role'>>
        & { is_active?: boolean }
    ) => {
      const response = await apiClient.patch<UserApiRecord>(
        `/auth/users/${userId}/`,
        data
      );
      return response.data;
    },
    auditEvents: async (params?: { page?: number }) => {
      const response = await apiClient.get<PaginatedResponse<SecurityAuditEventApiRecord>>(
        '/auth/security/audit/',
        { params }
      );
      return response.data;
    },
  },
};

export function getCurrentUserFromStorage(): UserApiRecord | null {
  return currentUser;
}

export function isAuthenticated(): boolean {
  return currentUser !== null;
}

export default apiClient;

export type ScholarshipMatchStatus =
  | 'ELIGIBLE'
  | 'NOT_ELIGIBLE'
  | 'NEEDS_VERIFICATION';

export interface ScholarshipMatchApiRecord {
  status: ScholarshipMatchStatus;
  reasons: string[];
  needs_verification: string[];
}

export interface PersonalizedScholarshipResult {
  scholarship: ScholarshipApiRecord;
  match: ScholarshipMatchApiRecord;
}

export interface PersonalizedScholarshipsResponse {
  count: number;
  results: PersonalizedScholarshipResult[];
}
