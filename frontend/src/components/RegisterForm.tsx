import { useState } from "react";
import { register, login, getMe, ApiError } from "../api/auth";
import type { UserRead } from "../api/auth";

interface Props {
  onSuccess: (token: string, user: UserRead) => void;
  onSwitchToLogin: () => void;
}

export function RegisterForm({ onSuccess, onSwitchToLogin }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register({ email, password, full_name: fullName.trim() || null });
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
        <h1 className="auth-heading">Регистрация</h1>
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
            <span>Имя (необязательно)</span>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
              placeholder="Иван Иванов"
            />
          </label>
          <label className="field">
            <span>Пароль</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              placeholder="минимум 8 символов"
            />
          </label>
          {error !== null && <p className="form-error">{error}</p>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Регистрация…" : "Создать аккаунт"}
          </button>
        </form>
        <p className="auth-switch">
          Уже есть аккаунт?{" "}
          <button type="button" className="link-btn" onClick={onSwitchToLogin}>
            Войти
          </button>
        </p>
      </div>
    </div>
  );
}
