import { PublicPageShell } from '@/components/layout/PublicPageShell';

const focusAreas = [
  {
    title: 'Scholarship discovery',
    description:
      'We help students explore scholarships, funding opportunities, and the requirements tied to each option.',
  },
  {
    title: 'Study destination guidance',
    description:
      'We present destination information, university options, and practical details that help students compare pathways.',
  },
  {
    title: 'Application support',
    description:
      'We share guidance around exams, preparation, documentation, and next steps for an informed application journey.',
  },
];

export default function AboutPage() {
  return (
    <PublicPageShell
      title="About Gofer Exam"
      description="Learn. Prepare. Apply. Achieve."
    >
      <article className="space-y-8 rounded-xl bg-white p-6 shadow-sm sm:p-8">
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold text-gray-900">Guidance for your study-abroad journey</h2>
          <p className="leading-7 text-gray-700">
            Gofer Exam provides educational information and consultancy support for students
            exploring international study. The website brings together scholarship discovery, study
            destination information, English exam preparation guidance, and application support.
          </p>
          <p className="leading-7 text-gray-700">
            Our goal is to make the pathway to international study clearer by connecting students
            with relevant information, practical preparation resources, and a better understanding of
            the decisions involved at each stage.
          </p>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {focusAreas.map(({ title, description }) => (
            <div key={title} className="rounded-xl border border-gray-200 bg-gray-50 p-5">
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-gray-700">{description}</p>
            </div>
          ))}
        </section>

        <section className="space-y-4 rounded-xl bg-amber-50 p-5 text-sm leading-7 text-amber-950">
          <p>
            Scholarship availability, admission decisions, and visa outcomes are determined by the
            relevant providers and authorities. Students should confirm current requirements and
            deadlines with official sources before applying.
          </p>
          <p>
            Gofer Exam is based in Addis Ababa, Ethiopia. For questions about the services or
            website, please use the contact options on our <a className="font-semibold underline" href="/contact">contact page</a>.
          </p>
        </section>
      </article>
    </PublicPageShell>
  );
}
