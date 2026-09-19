import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "UrbanLens AI",
  description: "Civic intelligence platform for Navi Mumbai",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
