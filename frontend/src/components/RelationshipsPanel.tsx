import { useEffect, useState } from 'react';
import type { PersonRead } from '../api/persons';
import { listPersons } from '../api/persons';
import type { ParentRole, RelationshipRead } from '../api/relationships';
import { createRelationship, deleteRelationship, listRelationships } from '../api/relationships';
import { ApiError } from '../api/auth';
import { listRelationshipSourceLinks } from '../api/sources';
import { SkeletonCardList } from './Skeletons';

interface Props {
  token: string;
  personsVersion: number;
  onRelationshipsChanged?: () => void;
  sourceLinksVersion?: number;
}

const PARENT_ROLE_LABEL: Record<ParentRole, string> = {
  father: 'Отец',
  mother: 'Мать',
  unknown: 'Неизвестно',
};

function formatFullName(p: PersonRead): string {
  return [p.surname, p.given_name, p.patronymic].filter(Boolean).join(' ');
}

export function RelationshipsPanel({
  token,
  personsVersion,
  onRelationshipsChanged,
  sourceLinksVersion,
}: Props) {
  const [persons, setPersons] = useState<PersonRead[]>([]);
  const [relationships, setRelationships] = useState<RelationshipRead[]>([]);
  const [loadState, setLoadState] = useState<'loading' | 'ok' | 'error'>('loading');

  const [parentId, setParentId] = useState('');
  const [childId, setChildId] = useState('');
  const [parentRole, setParentRole] = useState<ParentRole>('unknown');
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [relSourceCounts, setRelSourceCounts] = useState<Map<string, number>>(new Map());

  useEffect(() => {
    void load();
  }, [personsVersion]);

  useEffect(() => {
    void loadSourceCounts();
  }, [sourceLinksVersion]);

  async function load() {
    setLoadState('loading');
    try {
      const [personsData, relsData] = await Promise.all([
        listPersons(token),
        listRelationships(token),
      ]);
      setPersons(personsData);
      setRelationships(relsData);
      setLoadState('ok');
    } catch {
      setLoadState('error');
    }
  }

  async function loadSourceCounts() {
    try {
      const links = await listRelationshipSourceLinks(token);
      const counts = new Map<string, number>();
      for (const link of links) {
        counts.set(link.relationship_id, (counts.get(link.relationship_id) ?? 0) + 1);
      }
      setRelSourceCounts(counts);
    } catch {
      // non-critical: badges simply won't show
    }
  }

  async function reloadRelationships() {
    try {
      const relsData = await listRelationships(token);
      setRelationships(relsData);
    } catch {
      // keep existing list on reload error
    }
  }

  function findPerson(id: string): PersonRead | undefined {
    return persons.find((p) => p.id === id);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);

    if (!parentId || !childId) {
      setFormError('Выберите родителя и ребёнка.');
      return;
    }

    if (parentId === childId) {
      setFormError('Родитель и ребёнок должны быть разными персонами.');
      return;
    }

    setSaving(true);
    try {
      await createRelationship(token, {
        parent_id: parentId,
        child_id: childId,
        parent_role: parentRole,
      });
      setParentId('');
      setChildId('');
      setParentRole('unknown');
      await reloadRelationships();
      onRelationshipsChanged?.();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Ошибка создания связи');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(rel: RelationshipRead) {
    const parentPerson = findPerson(rel.parent_id);
    const childPerson = findPerson(rel.child_id);
    const parentName = parentPerson ? formatFullName(parentPerson) : 'Персона не найдена';
    const childName = childPerson ? formatFullName(childPerson) : 'Персона не найдена';
    const confirmed = window.confirm(
      `Удалить связь? Это действие нельзя отменить.\n\n${parentName} → ${childName}`
    );
    if (!confirmed) return;
    try {
      await deleteRelationship(token, rel.id);
      await reloadRelationships();
      onRelationshipsChanged?.();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Ошибка удаления');
    }
  }

  const canShowForm = loadState === 'ok' && persons.length >= 2;
  const showEmptyPersonsHint = loadState === 'ok' && persons.length < 2;
  const showEmptyRels = loadState === 'ok' && persons.length >= 2 && relationships.length === 0;

  return (
    <section className="panel relationships-panel">
      <div className="relationships-header">
        <div>
          <h2>Связи</h2>
          <p className="relationships-subtitle">
            Указывайте связи родитель–ребёнок для построения поколений.
          </p>
        </div>
      </div>

      {loadState === 'loading' && <SkeletonCardList count={3} />}

      {loadState === 'error' && (
        <p className="relationship-error">
          Не удалось загрузить данные.{' '}
          <button
            type="button"
            className="link-btn"
            onClick={() => {
              void load();
            }}
          >
            Повторить
          </button>
        </p>
      )}

      {showEmptyPersonsHint && (
        <p className="relationship-empty">Для создания связи нужно минимум две персоны.</p>
      )}

      {canShowForm && (
        <div className="relationships-form-section">
          <form
            className="relationships-form"
            onSubmit={(e) => {
              void handleCreate(e);
            }}
          >
            <label className="field">
              <span>Родитель</span>
              <select
                value={parentId}
                onChange={(e) => {
                  setParentId(e.target.value);
                  setFormError(null);
                }}
                required
              >
                <option value="">- выбрать -</option>
                {persons.map((p) => (
                  <option key={p.id} value={p.id}>
                    {formatFullName(p)}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Ребёнок</span>
              <select
                value={childId}
                onChange={(e) => {
                  setChildId(e.target.value);
                  setFormError(null);
                }}
                required
              >
                <option value="">- выбрать -</option>
                {persons.map((p) => (
                  <option key={p.id} value={p.id}>
                    {formatFullName(p)}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Роль родителя</span>
              <select
                value={parentRole}
                onChange={(e) => setParentRole(e.target.value as ParentRole)}
              >
                <option value="father">Отец</option>
                <option value="mother">Мать</option>
                <option value="unknown">Неизвестно</option>
              </select>
            </label>

            {formError !== null && (
              <p className="form-error relationship-form-error">{formError}</p>
            )}

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? 'Сохранение…' : 'Добавить связь'}
              </button>
            </div>
          </form>
        </div>
      )}

      {showEmptyRels && (
        <p className="relationship-empty">Связей пока нет. Выберите родителя и ребёнка.</p>
      )}

      {loadState === 'ok' && relationships.length > 0 && (
        <ul className="relationships-list">
          {relationships.map((rel) => {
            const parentPerson = findPerson(rel.parent_id);
            const childPerson = findPerson(rel.child_id);
            const parentName = parentPerson ? formatFullName(parentPerson) : 'Персона не найдена';
            const childName = childPerson ? formatFullName(childPerson) : 'Персона не найдена';
            return (
              <li key={rel.id} className="relationship-card">
                <div className="relationship-card-main">
                  <span className="relationship-role">{PARENT_ROLE_LABEL[rel.parent_role]}</span>
                  <span className="relationship-path">
                    {parentName}
                    <span className="relationship-arrow" aria-hidden="true">
                      {' '}
                      →{' '}
                    </span>
                    {childName}
                  </span>
                  {(relSourceCounts.get(rel.id) ?? 0) > 0 && (
                    <span className="evidence-badge">Источники: {relSourceCounts.get(rel.id)}</span>
                  )}
                </div>
                <div className="relationship-actions">
                  <button
                    type="button"
                    className="btn-action btn-action-delete"
                    onClick={() => {
                      void handleDelete(rel);
                    }}
                    aria-label="Удалить связь"
                  >
                    Удалить
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
