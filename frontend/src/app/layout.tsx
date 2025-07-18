import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { UserProvider, User } from "@/contexts/UserContext";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "AI Test Manager",
  description: "Modern test management system with AI capabilities",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Static user for demo; replace with real auth/session logic as needed
  const user: User = {
    name: "Alex Johnson",
    email: "alex.johnson@company.com",
    avatar: undefined,
  };

  return (
    <html lang="en">
      <body className={`${inter.variable} antialiased`}>
        <UserProvider user={user}>
          {children}
        </UserProvider>
      </body>
    </html>
  );
}
