"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import Button from "@/components/ui/Button";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/reports/new", label: "Report Issue" },
  { href: "/reports", label: "My Reports" },
  { href: "/incidents", label: "Incidents Map" },
];

export default function Header() {
  const { user, logout, loading, isModerator } = useAuth();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const links = isModerator ? [...NAV, { href: "/admin", label: "Admin" }] : NAV;

  return (
    <header className="sticky top-0 z-40 border-b border-ink-200 bg-white/90 backdrop-blur">
      <div className="container-page flex h-14 items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2 font-semibold text-ink-900">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary-600 text-white">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v3m0 14v3M2 12h3m14 0h3" strokeLinecap="round" />
            </svg>
          </span>
          <span>UrbanLens</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                pathname === l.href
                  ? "bg-primary-50 text-primary-700"
                  : "text-ink-600 hover:bg-ink-100 hover:text-ink-900"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          {loading ? (
            <span className="h-8 w-20 animate-pulse rounded-lg bg-ink-100" />
          ) : user ? (
            <>
              <span className="max-w-[180px] truncate text-sm text-ink-600">
                {user.display_name || user.email}
                <span className="ml-1 rounded bg-ink-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-ink-600">
                  {user.role}
                </span>
              </span>
              <Button variant="secondary" onClick={logout}>Sign out</Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="secondary">Sign in</Button>
              </Link>
              <Link href="/register">
                <Button>Get started</Button>
              </Link>
            </>
          )}
        </div>

        <button
          className="rounded-lg p-2 text-ink-700 hover:bg-ink-100 md:hidden"
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            {open ? (
              <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
            ) : (
              <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />
            )}
          </svg>
        </button>
      </div>

      {open && (
        <nav className="border-t border-ink-200 bg-white px-4 py-3 md:hidden">
          <div className="flex flex-col gap-1">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className={`rounded-lg px-3 py-2 text-sm font-medium ${
                  pathname === l.href
                    ? "bg-primary-50 text-primary-700"
                    : "text-ink-700 hover:bg-ink-100"
                }`}
              >
                {l.label}
              </Link>
            ))}
            <div className="mt-2 flex items-center gap-2 border-t border-ink-200 pt-3">
              {user ? (
                <>
                  <span className="flex-1 truncate text-sm text-ink-600">
                    {user.display_name || user.email}
                  </span>
                  <Button variant="secondary" onClick={() => { logout(); setOpen(false); }}>
                    Sign out
                  </Button>
                </>
              ) : (
                <>
                  <Link href="/login" className="flex-1" onClick={() => setOpen(false)}>
                    <Button variant="secondary" className="w-full">Sign in</Button>
                  </Link>
                  <Link href="/register" className="flex-1" onClick={() => setOpen(false)}>
                    <Button className="w-full">Get started</Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </nav>
      )}
    </header>
  );
}
