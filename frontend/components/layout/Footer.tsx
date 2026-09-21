import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-ink-200 bg-white">
      <div className="container-page flex flex-col items-start justify-between gap-4 py-8 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-semibold text-ink-800">UrbanLens AI</p>
          <p className="mt-1 max-w-md text-xs leading-relaxed text-ink-500">
            A civic-intelligence demo for Navi Mumbai. Decision support only —
            never a replacement for an official inspection or an emergency warning system.
          </p>
        </div>
        <nav className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-ink-500">
          <Link href="/reports/new" className="hover:text-ink-800">Report an issue</Link>
          <Link href="/incidents" className="hover:text-ink-800">Incidents map</Link>
          <a
            href="https://www.openstreetmap.org/copyright"
            target="_blank"
            rel="noreferrer"
            className="hover:text-ink-800"
          >
            © OpenStreetMap contributors
          </a>
        </nav>
      </div>
    </footer>
  );
}
