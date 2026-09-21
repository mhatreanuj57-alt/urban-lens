import Link from "next/link";
import Button from "@/components/ui/Button";

const STEPS = [
  {
    title: "Snap it",
    body: "Upload a photo or short video of a road issue — a pin or GPS sets the location.",
  },
  {
    title: "AI structures it",
    body: "Detection suggests the issue type and confidence; you review before it becomes a report.",
  },
  {
    title: "Track & escalate",
    body: "Duplicates are clustered, priority is explained, and you export an editable complaint.",
  },
];

export default function Home() {
  return (
    <div>
      <section className="border-b border-ink-200 bg-white">
        <div className="container-page flex flex-col items-start gap-6 py-16 md:py-24">
          <span className="rounded-full bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700">
            Civic intelligence for Navi Mumbai
          </span>
          <h1 className="max-w-2xl text-4xl font-bold leading-tight text-ink-900 md:text-5xl">
            Turn a road photo into a report the city can act on.
          </h1>
          <p className="max-w-xl text-lg text-ink-600">
            Residents submit issues with a photo; AI structures them, maps recurring
            problems, and helps the operations team prioritise what to fix first.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/reports/new"><Button className="px-6 py-2.5 text-base">Report an issue</Button></Link>
            <Link href="/incidents">
              <Button variant="secondary" className="px-6 py-2.5 text-base">Explore the map</Button>
            </Link>
          </div>
        </div>
      </section>

      <section className="container-page py-16">
        <div className="grid gap-6 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <div key={s.title} className="card p-6">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600 text-sm font-bold text-white">
                {i + 1}
              </span>
              <h2 className="mt-4 text-lg font-semibold text-ink-900">{s.title}</h2>
              <p className="mt-1 text-sm text-ink-600">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-ink-200 bg-white">
        <div className="container-page flex flex-col items-center gap-4 py-14 text-center">
          <h2 className="text-2xl font-bold text-ink-900">See what needs attention near you</h2>
          <p className="max-w-md text-sm text-ink-600">
            UrbanLens is decision support — every report is reviewed by a person before it
            becomes an official action.
          </p>
          <Link href="/incidents"><Button>Open the incidents map</Button></Link>
        </div>
      </section>
    </div>
  );
}
