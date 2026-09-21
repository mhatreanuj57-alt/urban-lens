"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";
import Button from "@/components/ui/Button";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [consentTraining, setConsentTraining] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    setBusy(true);
    try {
      await register({
        email: email.trim(),
        password,
        display_name: displayName.trim() || undefined,
        consent_training: consentTraining,
      });
      router.push("/reports/new");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed. Please try again.");
      setBusy(false);
    }
  }

  return (
    <div className="container-page flex max-w-md flex-col py-12">
      <div className="card px-6 py-8 sm:px-8">
        <h1 className="text-xl font-bold text-ink-900">Create your account</h1>
        <p className="mb-6 mt-1 text-sm text-ink-500">Report issues and track their status.</p>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label htmlFor="display_name" className="label">Display name</label>
            <input
              id="display_name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="input"
              placeholder="Optional"
              maxLength={100}
            />
          </div>
          <div>
            <label htmlFor="email" className="label">Email</label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label htmlFor="password" className="label">Password</label>
            <input
              id="password"
              type="password"
              required
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="At least 8 characters"
            />
          </div>
          <label className="flex items-start gap-2 text-sm text-ink-700">
            <input
              type="checkbox"
              checked={consentTraining}
              onChange={(e) => setConsentTraining(e.target.checked)}
              className="mt-0.5"
            />
            <span>Allow my media to help train the detection model (optional).</span>
          </label>
          {error && <p className="field-error">{error}</p>}
          <Button type="submit" className="w-full" loading={busy}>Create account</Button>
          <p className="text-center text-sm text-ink-500">
            Already registered?{" "}
            <Link href="/login" className="font-medium text-primary-700 hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
