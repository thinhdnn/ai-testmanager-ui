"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="text-center space-y-5">
        {/* 404 Icon */}
        <div className="relative">
          <div className="absolute -inset-1 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 opacity-75 blur"></div>
          <div className="relative bg-white dark:bg-gray-800 rounded-lg p-8">
            <div className="text-9xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-pink-600">
              404
            </div>
          </div>
        </div>

        {/* Error Message */}
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mt-8">
          Page Not Found
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-lg">
          Sorry, we couldn't find the page you're looking for. The page might have been removed or the link might be broken.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
          <Button
            variant="default"
            size="lg"
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
            asChild
          >
            <Link href="/">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              Back to Home
            </Link>
          </Button>
          <Button
            variant="outline"
            size="lg"
            onClick={() => window.history.back()}
            className="border-gray-300 dark:border-gray-700"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Go Back
          </Button>
        </div>

        {/* Additional Help */}
        <div className="mt-12 text-sm text-gray-500 dark:text-gray-400">
          Need help? Contact{" "}
          <a href="mailto:support@example.com" className="text-purple-600 hover:text-purple-500 dark:text-purple-400">
            support@example.com
          </a>
        </div>
      </div>
    </div>
  )
} 