import { useState } from 'react';
import { LogOut } from 'lucide-react';
import type { UserRead } from '../api/auth';
import { PersonsPanel } from './PersonsPanel';
import { RelationshipsPanel } from './RelationshipsPanel';
import { SourcesPanel } from './SourcesPanel';
import { SosaReportPanel } from './SosaReportPanel';

interface Props {
  user: UserRead;
  token: string;
  onLogout: () => void;
}

export function Dashboard({ user, token, onLogout }: Props) {
  const [personsVersion, setPersonsVersion] = useState(0);
  const [relationshipsVersion, setRelationshipsVersion] = useState(0);
  const [sourceLinksVersion, setSourceLinksVersion] = useState(0);

  return (
    <main className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">Rodex · Родословная роспись</p>
          <h1>{user.full_name ? `Добро пожаловать, ${user.full_name}!` : 'Добро пожаловать!'}</h1>
          <p className="lead">Приятного вам дня!</p>
        </div>
        <button type="button" className="btn-logout" onClick={onLogout}>
          <LogOut size={16} aria-hidden="true" />
          Выйти
        </button>
      </section>

      <section className="panel dashboard-panel">
        <h2>Текущий пользователь</h2>
        <dl className="user-info">
          <div className="user-info-row">
            <dt>Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div className="user-info-row">
            <dt>Имя</dt>
            <dd>{user.full_name ?? '-'}</dd>
          </div>
          <div className="user-info-row">
            <dt>User ID</dt>
            <dd className="user-id">{user.id}</dd>
          </div>
          <div className="user-info-row">
            <dt>Статус</dt>
            <dd className={user.is_active ? 'status-active' : 'status-inactive'}>
              {user.is_active ? 'Активен' : 'Неактивен'}
            </dd>
          </div>
        </dl>
      </section>

      <PersonsPanel
        token={token}
        onPersonsChanged={() => setPersonsVersion((v) => v + 1)}
        sourceLinksVersion={sourceLinksVersion}
      />
      <RelationshipsPanel
        token={token}
        personsVersion={personsVersion}
        onRelationshipsChanged={() => setRelationshipsVersion((v) => v + 1)}
        sourceLinksVersion={sourceLinksVersion}
      />
      <SourcesPanel
        token={token}
        personsVersion={personsVersion}
        relationshipsVersion={relationshipsVersion}
        onSourceLinksChanged={() => setSourceLinksVersion((v) => v + 1)}
      />
      <SosaReportPanel token={token} personsVersion={personsVersion} />

      <details className="about-panel">
        <summary className="about-summary">О приложении</summary>
        <div className="about-body">
          <p className="about-text">
            Rodex предназначен для ввода сведений о персонах, родственных связях и источниках, а
            также для построения родословной росписи по системе Соса–Страдоница.
          </p>
          <ul className="about-feature-list">
            <li className="about-feature">Персоны и биографические сведения</li>
            <li className="about-feature">Связи родитель–ребёнок</li>
            <li className="about-feature">Архивные источники и привязки</li>
            <li className="about-feature">Поколенная роспись</li>
            <li className="about-feature">Визуальное дерево предков</li>
            <li className="about-feature">Экспорт CSV</li>
          </ul>
          <p className="about-note">
            Данные пользователя изолированы и доступны только после входа.
          </p>
        </div>
      </details>
    </main>
  );
}
