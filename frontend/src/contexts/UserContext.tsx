"use client"

import { createContext, useContext, ReactNode } from 'react';

export interface User {
  name: string;
  email: string;
  avatar?: string;
}

const UserContext = createContext<User | null>(null);

interface UserProviderProps {
  children: ReactNode;
  user: User;
}

export function UserProvider({ children, user }: UserProviderProps) {
  return (
    <UserContext.Provider value={user}>
      {children}
    </UserContext.Provider>
  );
}

export const useUser = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}; 