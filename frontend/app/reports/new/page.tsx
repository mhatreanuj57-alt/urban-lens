"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Loading } from "@/components/ui/States";
import Button from "@/components/ui/Button";
import ReportForm from "@/components/forms/ReportForm";

export default function NewReportPage() {
  const { user, loading } = useAuth();

  return (
    <div className="container-page max-w-2xl py-10">
      <h1 className="text-2xl font-bold text-ink-900">Report an issue</h1>
      <p className="mt-1 text-sm text-ink-500">
        Add a photo or short video, set the location, and submit. AI will suggest what
        it sees for you to review.
      </p>

      <div className="mt-6">
        {loading ? (
          <Loading label="Checking your session…" />
        ) : !user ? (
          <div className="card px-6 py-10 text-center">
            <h2 className="text-lg font-semibold text-ink-800">Sign in to report</h2>
            <p className="mx-auto mt-1 max-w-sm text-sm text-ink-500">
              You need an account so you can track the status and export a complaint later.
            </p>
            <div className="mt-4 flex justify-center gap-2">
              <Link href="/login"><Button>Sign in</Button></Link>
              <Link href="/register"><Button variant="secondary">Create account</Button></Link>
            </div>
          </div>
        ) : (
          <ReportForm />
        )}
      </div>
    </div>
  );
}
