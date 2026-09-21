import { STATUS_LABELS, STATUS_STYLES } from "@/lib/api";

export default function StatusBadge({
  status,
  className = "",
}: {
  status: string;
  className?: string;
}) {
  const label = STATUS_LABELS[status] ?? status;
  const style = STATUS_STYLES[status] ?? "bg-ink-100 text-ink-700";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style} ${className}`}
    >
      {label}
    </span>
  );
}
