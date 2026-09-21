"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ISSUE_LABELS,
  reportsApi,
  uploadsApi,
  ApiError,
  type IssueType,
} from "@/lib/api";
import MapView from "@/components/map/MapView";
import Button from "@/components/ui/Button";

const ISSUE_OPTIONS = Object.entries(ISSUE_LABELS) as [IssueType, string][];

type FileKind = "image" | "video";

function kindOf(mime: string): FileKind {
  return mime.startsWith("video/") ? "video" : "image";
}

export default function ReportForm() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [objectKey, setObjectKey] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const [issueType, setIssueType] = useState<IssueType | "">("");
  const [description, setDescription] = useState("");
  const [landmark, setLandmark] = useState("");
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [locating, setLocating] = useState(false);
  const [consentLocation, setConsentLocation] = useState(false);
  const [consentTraining, setConsentTraining] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function resetFile() {
    setFile(null);
    setObjectKey(null);
    setError(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
  }

  async function handleFileSelected(next: File | null) {
    setError(null);
    if (!next) {
      resetFile();
      return;
    }
    if (!/^(image|video)\//.test(next.type)) {
      setError("Please choose a JPG, PNG, WebP, MP4 or MOV file.");
      return;
    }
    if (next.size > 25 * 1024 * 1024) {
      setError("File is larger than 25 MB.");
      return;
    }
    setFile(next);
    setObjectKey(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(next));

    setUploading(true);
    try {
      const sign = await uploadsApi.sign(next.name, next.type, next.size);
      await uploadsApi.upload(sign, next);
      setObjectKey(sign.object_key);
    } catch (e) {
      setError(
        e instanceof ApiError
          ? `Upload failed: ${e.message}`
          : "Upload failed. Please try again.",
      );
    } finally {
      setUploading(false);
    }
  }

  function useMyLocation() {
    if (!("geolocation" in navigator)) {
      setError("Geolocation is not available. Tap the map to drop a pin instead.");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocating(false);
      },
      () => {
        setError("Could not get your location. Tap the map to drop a pin instead.");
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!issueType) return setError("Select an issue type.");
    if (!file || !objectKey) return setError("Upload a photo or video first.");
    if (!coords) return setError("Set the location — use your GPS or tap the map to drop a pin.");
    if (!consentLocation) return setError("Location consent is required to submit a report.");

    setSubmitting(true);
    try {
      const created = await reportsApi.create({
        issue_type: issueType,
        description: description.trim() || undefined,
        latitude: coords.lat,
        longitude: coords.lng,
        location_source: landmark.trim() ? "landmark" : "manual_pin",
        landmark: landmark.trim() || undefined,
        consent_location: consentLocation,
        consent_training: consentTraining,
        media: [{ object_key: objectKey, mime_type: file.type, kind: kindOf(file.type) }],
      });
      router.push(`/reports/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Submission failed. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Media */}
      <div>
        <span className="label">Photo or video</span>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime"
          className="hidden"
          onChange={(e) => handleFileSelected(e.target.files?.[0] ?? null)}
        />
        {file ? (
          <div className="card overflow-hidden">
            {kindOf(file.type) === "video" ? (
              <video src={previewUrl ?? undefined} controls className="max-h-72 w-full bg-ink-950" />
            ) : (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={previewUrl ?? undefined} alt="Selected media" className="max-h-72 w-full object-cover" />
            )}
            <div className="flex items-center justify-between gap-3 px-4 py-2 text-sm">
              <span className="truncate text-ink-600">
                {file.name}
                {uploading ? " — uploading…" : objectKey ? " — uploaded" : ""}
              </span>
              <Button type="button" variant="secondary" onClick={resetFile} disabled={uploading}>
                Change
              </Button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="flex w-full flex-col items-center gap-2 rounded-xl border-2 border-dashed border-ink-300 bg-ink-50 px-6 py-10 text-ink-500 transition hover:border-primary-400 hover:text-primary-600"
          >
            <svg viewBox="0 0 24 24" className="h-8 w-8" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden>
              <path d="M12 16V4m0 0L8 8m4-4l4 4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-sm font-medium">Tap to add a road photo or short video</span>
            <span className="text-xs">JPG, PNG, WebP, MP4 or MOV · up to 25 MB</span>
          </button>
        )}
        {uploading && (
          <p className="mt-1 text-xs text-ink-500">Uploading securely…</p>
        )}
      </div>

      {/* Issue type */}
      <div>
        <label htmlFor="issue_type" className="label">Issue type</label>
        <select
          id="issue_type"
          value={issueType}
          onChange={(e) => setIssueType(e.target.value as IssueType | "")}
          className="input"
        >
          <option value="">Select the main issue…</option>
          {ISSUE_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>

      {/* Location */}
      <div>
        <span className="label">Location</span>
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Button type="button" variant="secondary" onClick={useMyLocation} loading={locating}>
            Use my location
          </Button>
          <span className="text-sm text-ink-500">
            {coords
              ? `Pinned at ${coords.lat.toFixed(5)}, ${coords.lng.toFixed(5)}`
              : "or tap the map to drop a pin"}
          </span>
        </div>
        <MapView
          center={coords ? [coords.lng, coords.lat] : [73.02, 19.05]}
          zoom={coords ? 15 : 11}
          className="h-72 w-full overflow-hidden rounded-xl border border-ink-200"
          markers={coords ? [{ id: "pin", lat: coords.lat, lng: coords.lng }] : []}
          onMapClick={(lat, lng) => setCoords({ lat, lng })}
        />
        <input
          value={landmark}
          onChange={(e) => setLandmark(e.target.value)}
          className="input mt-2"
          placeholder="Nearest landmark (optional)"
          maxLength={200}
        />
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="label">Details</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          maxLength={4000}
          className="input"
          placeholder="Anything that helps the team understand the issue…"
        />
      </div>

      {/* Consent */}
      <div className="space-y-2 rounded-xl border border-ink-200 bg-ink-50 p-4">
        <label className="flex items-start gap-2 text-sm text-ink-700">
          <input
            type="checkbox"
            checked={consentLocation}
            onChange={(e) => setConsentLocation(e.target.checked)}
            className="mt-0.5"
          />
          <span>I consent to UrbanLens storing this report&apos;s location. <span className="text-red-600">*</span></span>
        </label>
        <label className="flex items-start gap-2 text-sm text-ink-700">
          <input
            type="checkbox"
            checked={consentTraining}
            onChange={(e) => setConsentTraining(e.target.checked)}
            className="mt-0.5"
          />
          <span>Allow my media to help train the detection model (optional).</span>
        </label>
      </div>

      {error && <p className="field-error">{error}</p>}

      <div className="flex items-center gap-3">
        <Button type="submit" loading={submitting || uploading} disabled={!objectKey || !!uploading}>
          {submitting ? "Submitting…" : "Submit report"}
        </Button>
        <Button type="button" variant="ghost" onClick={() => router.back()}>Cancel</Button>
      </div>
    </form>
  );
}
