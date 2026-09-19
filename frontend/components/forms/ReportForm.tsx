import { useState } from "react";
import { reportsApi } from "@/lib/api";

const ISSUE_TYPES = [
  { value: "pothole", label: "Pothole" },
  { value: "garbage", label: "Garbage" },
  { value: "damaged_streetlight", label: "Damaged Streetlight" },
  { value: "waterlogging", label: "Waterlogging" },
  { value: "illegal_dumping", label: "Illegal Dumping" },
];

export default function ReportForm() {
  const [issueType, setIssueType] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!issueType) {
      setMessage("Please select an issue type");
      return;
    }
    setSubmitting(true);
    setMessage("");
    try {
      await reportsApi.create({ issue_type: issueType, description });
      setMessage("Report submitted successfully!");
      setIssueType("");
      setDescription("");
    } catch {
      setMessage("Failed to submit report. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
      <div>
        <label className="block text-sm font-medium mb-1">Issue Type</label>
        <select
          value={issueType}
          onChange={(e) => setIssueType(e.target.value)}
          className="w-full border rounded px-3 py-2"
        >
          <option value="">Select an issue</option>
          {ISSUE_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full border rounded px-3 py-2"
          rows={3}
          placeholder="Optional details..."
        />
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        {submitting ? "Submitting..." : "Submit Report"}
      </button>
      {message && <p className="text-sm text-gray-600">{message}</p>}
    </form>
  );
}
