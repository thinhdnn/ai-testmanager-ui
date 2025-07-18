# AI Test Manager - Layout Documentation

## Overview

This project implements a modern three-section web interface layout with clean design aesthetics, following the specifications provided. The layout consists of:

1. **Sidebar Menu** (left)
2. **Main Content Area** (center) 
3. **User Profile** (top right)

## Design System

### Colors
- **Background**: `#fdfdfd` (Primary background)
- **Sidebar**: `#f2f2f2` (Sidebar background)
- **Main Content**: `#fcfcfc` (Content area background)
- **Text Primary**: `#121212` (Main text color)
- **Text Secondary**: `#8a8a8a` (Muted text)
- **Border**: `#dcdcdc` (Light borders)
- **Hover**: `#eaeaea` (Hover states)

### Typography
- **Primary Font**: Inter (Google Fonts)
- **Fallback**: SF Pro Display, system fonts

### Border Radius
- **Small**: 10px
- **Medium**: 12px
- **Large**: 20px
- **Buttons**: 32px

## Components

### 1. Sidebar (`/components/sidebar.tsx`)

**Features:**
- Fixed position on the left
- Width: 240px (expanded), 64px (collapsed)
- Full height
- Collapsible with toggle button
- Menu items: Dashboard, Projects, Releases, Users, Settings
- Hover effects with background color change
- Tooltips when collapsed

**Props:**
- `isCollapsed?: boolean` - Control collapsed state
- `onToggle?: () => void` - Toggle function
- `className?: string` - Additional CSS classes

### 2. Main Content (`/components/main-content.tsx`)

**Features:**
- Flexible layout taking remaining space
- Background: `#fcfcfc`
- Padding: 24px
- Border radius: 12px
- Scrollable content area

**Props:**
- `children: React.ReactNode` - Content to display
- `title?: string` - Optional page title
- `className?: string` - Additional CSS classes

### 3. User Profile (`/components/user-profile.tsx`)

**Features:**
- Circular avatar with initials fallback
- User name and email display
- Dropdown menu with Profile/Settings/Sign out
- Positioned in top right corner

**Props:**
```typescript
user?: {
  name: string
  email: string
  avatar?: string
}
```

### 4. App Layout (`/components/app-layout.tsx`)

**Main Layout Component:**
- Combines all three sections
- Manages sidebar collapse state
- Responsive design
- Mobile-friendly

**Props:**
```typescript
{
  children: React.ReactNode
  title?: string
  user?: {
    name: string
    email: string
    avatar?: string
  }
}
```

## Usage Example

```tsx
import { AppLayout } from "@/components/app-layout"
import { DashboardContent } from "@/components/dashboard-content"

export default function Dashboard() {
  const user = {
    name: "Alex Johnson",
    email: "alex.johnson@company.com"
  }

  return (
    <AppLayout title="Dashboard" user={user}>
      <DashboardContent />
    </AppLayout>
  )
}
```

## Responsive Design

- **Desktop**: Full layout with expanded sidebar
- **Tablet**: Sidebar can be collapsed to save space
- **Mobile**: Sidebar collapses to icon-only mode
- **Touch**: Optimized for touch interactions

## Navigation

The sidebar includes these main navigation items:

1. **Dashboard** - Overview and analytics
2. **Projects** - Project management
3. **Releases** - Release tracking
4. **Users** - User management
5. **Settings** - System configuration

## Technologies Used

- **Next.js 15** - React framework
- **Tailwind CSS 4** - Styling
- **ShadCN UI** - Component library
- **Lucide React** - Icons
- **Radix UI** - Accessibility primitives

## File Structure

```
src/
├── components/
│   ├── ui/                    # ShadCN UI components
│   │   ├── avatar.tsx
│   │   ├── dropdown-menu.tsx
│   │   └── separator.tsx
│   ├── app-layout.tsx         # Main layout component
│   ├── sidebar.tsx            # Sidebar navigation
│   ├── main-content.tsx       # Content area wrapper
│   ├── user-profile.tsx       # User profile dropdown
│   └── dashboard-content.tsx  # Sample dashboard content
├── lib/
│   └── utils.ts               # Utility functions
└── app/
    ├── globals.css            # Global styles
    ├── layout.tsx             # Root layout
    └── page.tsx               # Home page
```

## Customization

The layout is highly customizable through:

1. **CSS Custom Properties** - Modify colors and spacing
2. **Tailwind Classes** - Override specific styles
3. **Component Props** - Control behavior and appearance
4. **ShadCN Theming** - Consistent design tokens

## Performance

- **Optimized Components** - Minimal re-renders
- **Responsive Images** - Proper avatar handling
- **Smooth Animations** - CSS transitions for interactions
- **Accessibility** - ARIA labels and keyboard navigation

## Getting Started

1. Install dependencies: `npm install`
2. Start development server: `npm run dev`
3. Open http://localhost:3000
4. Customize as needed for your application

The layout provides a solid foundation for building modern web applications with a clean, professional interface. 