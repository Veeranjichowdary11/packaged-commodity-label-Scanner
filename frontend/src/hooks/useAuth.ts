'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

function getStoredUser() {
  if (typeof window === 'undefined') return null;
  try {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    if (token && userData) {
      return JSON.parse(userData);
    }
  } catch {
    // corrupted data — clear it
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
  return null;
}

export function useAuth(requireAuth: boolean = true) {
  const [user, setUser] = useState<any>(() => getStoredUser());
  const [checked, setChecked] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const storedUser = getStoredUser();
    if (storedUser) {
      setUser(storedUser);
    } else if (requireAuth) {
      router.replace('/login');
    }
    setChecked(true);
  }, [router, requireAuth]);

  return { user, checked };
}
