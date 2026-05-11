import { useState } from "react";
import { login, getMe, ApiError } from "../api/auth";
import type { UserRead } from "../api/auth";

interface Props {
  onSuccess: (token: string, user: UserRead) => void;
  onSwitchToRegister: () => void;
}

export function LoginForm({ onSuccess, onSwitchToRegister }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const token = await login({ email, password });
      const user = await getMe(token);
      onSuccess(token, user);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось подключиться к серверу",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <p className="auth-eyebrow">Rodex</p>
        <h1 className="auth-heading">Вход</h1>
        <form
          onSubmit={(e) => {
            void handleSubmit(e);
          }}
          className="auth-form"
        >
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="you@example.com"
            />
          </label>
          <label className="field">
            <span>Пароль</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              placeholder="••••••••"
            />
          </label>
          {error !== null && <p className="form-error">{error}</p>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Вход…" : "Войти"}
          </button>
        </form>
        <p className="auth-switch">
          Нет аккаунта?{" "}
          <button
            type="button"
            className="link-btn"
            onClick={onSwitchToRegister}
          >
            Зарегистрироваться
          </button>
        </p>
      </div>
    </div>
  );
}
