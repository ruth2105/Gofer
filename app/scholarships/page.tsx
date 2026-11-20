'use client';

import { FormEvent, useState, useEffect, useSyncExternalStore } from 'react';
import Link from 'next/link';
import { Navigation } from '@/components/layout/Navigation';
import { Footer } from '@/components/layout/Footer';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Search, Award, Calendar, MapPin, ExternalLink } from 'lucide-react';
import { getScholarshipPage } from '@/lib/api/scholarships';
import { formatDate, calculateDaysUntil } from '@/lib/utils';
import { Scholarship } from '@/types';
import { FeedbackState } from '@/components/ui/FeedbackState';
import { getApiErrorMessage } from '@/lib/api/errors';

const subscribeToNothing = () => () => {};
const getClientSnapshot = () => true;
const getServerSnapshot = () => false;

export default function ScholarshipsPage() {
  const [scholarships, setScholarships] = useState<Scholarship[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [hasPreviousPage, setHasPreviousPage] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [loadErrorMessage, setLoadErrorMessage] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [countryFilter, setCountryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [levelFilter, setLevelFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [appliedFilters, setAppliedFilters] = useState({
    search: '',
    country: '',
    type: '',
    level: '',
    ordering: 'application_deadline',
  });
  const mounted = useSyncExternalStore(
    subscribeToNothing,
    getClientSnapshot,
    getServerSnapshot
  );

  useEffect(() => {
    let active = true;
    getScholarshipPage({
      page,
      search: appliedFilters.search || undefined,
      country: appliedFilters.country || undefined,
      type: appliedFilters.type || undefined,
      level: appliedFilters.level || undefined,
      ordering: appliedFilters.ordering || undefined,
    })
      .then((response) => {
        if (active) {
          setScholarships(response.results);
          setTotalCount(response.count);
          setHasNextPage(Boolean(response.next));
          setHasPreviousPage(Boolean(response.previous));
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setLoadError(true);
          setLoadErrorMessage(getApiErrorMessage(error, 'Scholarships could not be loaded.'));
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [appliedFilters, page, retryCount]);

  const submitFilters = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPage(1);
    setLoading(true);
    setLoadError(false);
    setLoadErrorMessage('');
    setAppliedFilters({
      search: searchQuery.trim(),
      country: countryFilter.trim(),
      type: typeFilter === 'all' ? '' : typeFilter,
      level: levelFilter === 'all' ? '' : levelFilter,
      ordering: appliedFilters.ordering || 'application_deadline',
    });
  };

  const clearFilters = () => {
    setSearchQuery('');
    setCountryFilter('');
    setTypeFilter('all');
    setLevelFilter('all');
    setPage(1);
    setLoading(true);
    setLoadError(false);
    setLoadErrorMessage('');
    setAppliedFilters({
      search: '',
      country: '',
      type: '',
      level: '',
      ordering: 'application_deadline',
    });
  };

  const changePage = (nextPage: number) => {
    setPage(nextPage);
    setLoading(true);
    setLoadError(false);
    setLoadErrorMessage('');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main id="main-content" tabIndex={-1}>
      
      {/* Header */}
      <section className="bg-primary-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <Award className="mx-auto mb-4 text-brand-gold" size={48} />
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Scholarship Database
            </h1>
            <p className="text-xl text-gray-200 max-w-2xl mx-auto">
              Discover scholarships from around the world to fund your education
            </p>
          </div>
        </div>
      </section>

      {/* Filters */}
      <section className="bg-white shadow-md sticky top-16 z-30" aria-label="Scholarship search filters">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <form onSubmit={submitFilters} className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <Input
                  type="text"
                  label="Search scholarships"
                  placeholder="Search scholarships..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Input
              label="Country"
              type="search"
              placeholder="Any country"
              value={countryFilter}
              onChange={(e) => setCountryFilter(e.target.value)}
            />
            <Select
              label="Scholarship type"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              options={[
                { value: 'all', label: 'All Types' },
                { value: 'FULL', label: 'Full Scholarship' },
                { value: 'PARTIAL', label: 'Partial Scholarship' },
                { value: 'MERIT', label: 'Merit-Based Scholarship' },
                { value: 'NEED', label: 'Need-Based Scholarship' },
                { value: 'RESEARCH', label: 'Research Scholarship' },
                { value: 'ATHLETIC', label: 'Athletic Scholarship' },
              ]}
            />
            <Select
              label="Study level"
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              options={[
                { value: 'all', label: 'All Levels' },
                { value: 'UNDERGRADUATE', label: 'Undergraduate' },
                { value: 'GRADUATE', label: 'Graduate' },
                { value: 'POSTGRADUATE', label: 'Postgraduate' },
                { value: 'DOCTORATE', label: 'PhD' },
                { value: 'ALL', label: 'All Levels' },
              ]}
            />
            <Select
              label="Sort by deadline"
              value={appliedFilters.ordering}
              onChange={(event) => {
                setAppliedFilters((current) => ({
                  ...current,
                  ordering: event.target.value,
                }));
                setPage(1);
                setLoading(true);
                setLoadError(false);
                setLoadErrorMessage('');
              }}
              options={[
                { value: 'application_deadline', label: 'Soonest deadline' },
                { value: '-application_deadline', label: 'Latest deadline' },
              ]}
            />
            <div className="flex items-end gap-2 md:col-span-4">
              <Button type="submit">Apply filters</Button>
              <Button type="button" variant="outline" onClick={clearFilters}>Clear</Button>
            </div>
          </form>
          <div className="mt-4 text-sm text-gray-600" aria-live="polite">
            {loading ? 'Loading scholarships…' : `Showing ${scholarships.length} of ${totalCount} scholarships`}
          </div>
        </div>
      </section>

      {/* Scholarships Grid */}
      <section className="flex-1 py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {loadError ? (
            <div className="text-center py-12" role="alert">
              <h3 className="text-xl font-semibold text-gray-700 mb-2">Scholarships could not be loaded</h3>
              <p className="text-gray-600 mb-4">{loadErrorMessage}</p>
              <Button
                variant="primary"
                onClick={() => {
                  setLoading(true);
                  setLoadError(false);
                  setLoadErrorMessage('');
                  setRetryCount((count) => count + 1);
                }}
              >
                Try Again
              </Button>
            </div>
          ) : loading ? (
            <p className="text-center py-12 text-gray-600" role="status">Loading scholarships…</p>
          ) : totalCount === 0 ? (
            <FeedbackState
              variant="empty"
              title={[appliedFilters.search, appliedFilters.country, appliedFilters.type, appliedFilters.level].some(Boolean) ? 'No scholarships found' : 'No scholarships are published yet'}
              description={[appliedFilters.search, appliedFilters.country, appliedFilters.type, appliedFilters.level].some(Boolean)
                ? 'No published scholarships match these filters. Adjust your search or clear the filters.'
                : 'The catalogue is connected, but there are no current records to display. Check back later.'}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {scholarships.map((scholarship) => {
                const daysLeft = mounted ? calculateDaysUntil(scholarship.deadline) : 0;
                const isUrgent = daysLeft > 0 && daysLeft <= 30;
                
                return (
                  <Card key={scholarship.id} hover className="h-full flex flex-col">
                    <CardHeader>
                      <div className="flex items-start justify-between mb-3">
                        <Badge variant={scholarship.type === 'Full' ? 'success' : 'info'}>
                          {scholarship.type} Scholarship
                        </Badge>
                        {scholarship.featured && (
                          <Badge variant="warning" className="ml-2">
                            ⭐ Featured
                          </Badge>
                        )}
                      </div>
                      <CardTitle className="text-lg">{scholarship.title}</CardTitle>
                      <CardDescription>{scholarship.provider}</CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1">
                      <div className="space-y-3">
                        <div className="flex items-center text-sm text-gray-600">
                          <MapPin size={16} className="mr-2 text-primary-600 flex-shrink-0" />
                          {scholarship.country}
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-gray-700">Coverage:</p>
                          <p className="text-sm text-gray-600">{scholarship.amount}</p>
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-gray-700">Level:</p>
                          <p className="text-sm text-gray-600">{scholarship.level}</p>
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-gray-700">Deadline:</p>
                          <div className="flex items-center">
                            <Calendar size={14} className="mr-1 text-gray-500" />
                            <p className="text-sm text-gray-600">
                              {formatDate(scholarship.deadline)}
                            </p>
                          </div>
                          {mounted && daysLeft > 0 && (
                            <Badge variant={isUrgent ? 'danger' : 'warning'} className="mt-1">
                              {daysLeft} days left
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardContent>
                    <CardFooter className="flex gap-2">
                      <Link href={`/scholarships/${scholarship.id}`} className="flex-1">
                        <Button variant="primary" className="w-full" size="sm">
                          View Details
                        </Button>
                      </Link>
                      <a 
                        href={scholarship.applicationLink} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex-shrink-0"
                      >
                        <Button variant="outline" size="sm">
                          <ExternalLink size={16} />
                        </Button>
                      </a>
                    </CardFooter>
                  </Card>
                );
              })}
            </div>
          )}
          {!loadError && !loading && totalCount > 0 && (
            <nav className="mt-8 flex items-center justify-between" aria-label="Scholarship pages">
              <Button
                variant="outline"
                disabled={!hasPreviousPage}
                onClick={() => changePage(Math.max(1, page - 1))}
              >
                Previous
              </Button>
              <span className="text-sm text-gray-600">Page {page}</span>
              <Button
                variant="outline"
                disabled={!hasNextPage}
                onClick={() => changePage(page + 1)}
              >
                Next
              </Button>
            </nav>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-900 text-white py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">
            Need Help with Scholarship Applications?
          </h2>
          <p className="text-lg text-gray-200 mb-6">
            Gofer Exam may offer application guidance. Confirm the current consultation scope and fees before engaging a service.
          </p>
          <Link href="/contact">
            <Button variant="secondary" size="lg">
              Contact Us About a Consultation
            </Button>
          </Link>
        </div>
      </section>

      </main>
      <Footer />
    </div>
  );
}
