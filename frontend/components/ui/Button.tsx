"use client";

import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800 shadow-sm",
  secondary:
    "border border-ink-300 bg-white text-ink-800 hover:bg-ink-50 active:bg-ink-100",
  danger: "bg-red-600 text-white hover:bg-red-700 active:bg-red-800",
  ghost: "text-primary-700 hover:bg-primary-50",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

export default function Button({
  variant = "primary",
  loading = false,
  disabled,
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm
        font-medium transition focus:outline-none focus-visible:ring-2
        focus-visible:ring-primary-400 disabled:cursor-not-allowed disabled:opacity-50
        ${VARIANTS[variant]} ${className}`}
    >
      {loading && (
        <span
          aria-hidden
          className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      )}
      {children}
    </button>
  );
}
