import * as React from "react"
import { cn } from "@/lib/utils"

export interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  // Handle ESC key press
  React.useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && open) {
        onOpenChange(false)
      }
    }

    if (open) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden' // Prevent background scroll
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [open, onOpenChange])

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Enhanced backdrop with blur effect */}
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ease-out" 
            onClick={() => onOpenChange(false)}
          />
          {/* Enhanced dialog content with animation - fixed width and layout */}
          <div className="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-[90vw] z-10 transform transition-all duration-300 ease-out animate-in fade-in zoom-in-95 m-4">
            {children}
          </div>
        </div>
      )}
    </>
  )
}

export interface DialogContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function DialogContent({ children, className, ...props }: DialogContentProps) {
  return (
    <div className={cn("p-6", className)} {...props}>
      {children}
    </div>
  )
}

export interface DialogHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function DialogHeader({ children, className, ...props }: DialogHeaderProps) {
  return (
    <div className={cn("flex flex-col space-y-2 text-center sm:text-left pb-4 border-b border-gray-100 dark:border-gray-800", className)} {...props}>
      {children}
    </div>
  )
}

export interface DialogTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode
}

export function DialogTitle({ children, className, ...props }: DialogTitleProps) {
  return (
    <h3 className={cn("text-xl font-semibold leading-none tracking-tight text-gray-900 dark:text-gray-100", className)} {...props}>
      {children}
    </h3>
  )
}

export interface DialogDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode
}

export function DialogDescription({ children, className, ...props }: DialogDescriptionProps) {
  return (
    <p className={cn("text-sm text-gray-600 dark:text-gray-400", className)} {...props}>
      {children}
    </p>
  )
}

export interface DialogFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function DialogFooter({ children, className, ...props }: DialogFooterProps) {
  return (
    <div className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 pt-4 border-t border-gray-100 dark:border-gray-800 gap-3", className)} {...props}>
      {children}
    </div>
  )
} 