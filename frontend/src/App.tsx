import { useEffect, useState } from 'react';
import { getMe } from './api/auth';
import type { UserRead } from './api/auth';
import { LoginForm } from './components/LoginForm';
import { RegisterForm } from './components/RegisterForm';
import { Dashboard } from './components/Dashboard';
import { SkeletonAuthCard } from './components/Skeletons';

type Page = 'login' | 'register' | 'dashboard';

function useOnlineStatus() {
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    const up = () => setOnline(true);
    const down = () => setOnline(false);
    window.addEventListener('online', up);
    window.addEventListener('offline', down);
    return () => {
      window.removeEventListener('online', up);
      window.removeEventListener('offline', down);
    };
  }, []);
  return online;
}

function OfflineBanner() {
  const online = useOnlineStatus();
  if (online) return null;
  return (
    <div className="offline-banner" role="alert">
      Нет подключения к сети - данные недоступны
    </div>
  );
}

const TOKEN_KEY = 'rodex_token';

export function App() {
  const [page, setPage] = useState<Page>('login');
  const [user, setUser] = useState<UserRead | null>(null);
  const [token, setToken] = useState('');
  const [initialising, setInitialising] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    if (!storedToken) {
      setInitialising(false);
      return;
    }
    getMe(storedToken)
      .then((u) => {
        setToken(storedToken);
        setUser(u);
        setPage('dashboard');
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
      })
      .finally(() => {
        setInitialising(false);
      });
  }, []);

  function handleLoginSuccess(t: string, u: UserRead) {
    localStorage.setItem(TOKEN_KEY, t);
    setToken(t);
    setUser(u);
    setPage('dashboard');
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken('');
    setUser(null);
    setPage('login');
  }

  if (initialising) {
    return (
      <>
        <OfflineBanner />
        <div className="auth-page">
          <SkeletonAuthCard />
        </div>
      </>
    );
  }

  if (page === 'dashboard' && user !== null) {
    return (
      <>
        <OfflineBanner />
        <Dashboard user={user} token={token} onLogout={handleLogout} />
      </>
    );
  }

  if (page === 'register') {
    return (
      <>
        <OfflineBanner />
        <RegisterForm onSuccess={handleLoginSuccess} onSwitchToLogin={() => setPage('login')} />
      </>
    );
  }

  return (
    <>
      <OfflineBanner />
      <LoginForm onSuccess={handleLoginSuccess} onSwitchToRegister={() => setPage('register')} />
    </>
  );
}
