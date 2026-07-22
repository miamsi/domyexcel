// version 1
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Data Chatbot",
  description: "Natural Language BI Tool",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
