import { useEffect, useState } from 'react';
import { ApiError } from '../api/auth';
import type { PersonRead } from '../api/persons';
import { listPersons } from '../api/persons';
import { Pagination } from './Pagination';
import { SkeletonCardList } from './Skeletons';
import type { RelationshipRead } from '../api/relationships';
import { listRelationships } from '../api/relationships';
import type {
  PersonSourceRead,
  RelationshipSourceRead,
  SourceCreate,
  SourceRead,
  SourceUpdate,
} from '../api/sources';
import {
  createSource,
  deleteSource,
  linkSourceToPerson,
  linkSourceToRelationship,
  listPersonSourceLinks,
  listRelationshipSourceLinks,
  listSources,
  unlinkSourceFromPerson,
  unlinkSourceFromRelationship,
  updateSource,
} from '../api/sources';

interface Props {
  token: string;
  personsVersion: number;
  relationshipsVersion: number;
  onSourceLinksChanged?: () => void;
}

interface FormData {
  title: string;
  archive_reference: string;
  url: string;
  reliability_comment: string;
  notes: string;
}

const EMPTY_FORM: FormData = {
  title: '',
  archive_reference: '',
  url: '',
  reliability_comment: '',
  notes: '',
};

function sourceToForm(s: SourceRead): FormData {
  return {
    title: s.title,
    archive_reference: s.archive_reference ?? '',
    url: s.url ?? '',
    reliability_comment: s.reliability_comment ?? '',
    notes: s.notes ?? '',
  };
}

function formToPayload(f: FormData): SourceCreate {
  return {
    title: f.title.trim(),
    archive_reference: f.archive_reference.trim() || null,
    url: f.url.trim() || null,
    reliability_comment: f.reliability_comment.trim() || null,
    notes: f.notes.trim() || null,
  };
}

function formatFullName(p: PersonRead): string {
  return [p.surname, p.given_name, p.patronymic].filter(Boolean).join(' ');
}

export function SourcesPanel({
  token,
  personsVersion,
  relationshipsVersion,
  onSourceLinksChanged,
}: Props) {
  const [sources, setSources] = useState<SourceRead[]>([]);
  const [loadState, setLoadState] = useState<'loading' | 'ok' | 'error'>('loading');

  const [persons, setPersons] = useState<PersonRead[]>([]);
  const [relationships, setRelationships] = useState<RelationshipRead[]>([]);

  const [formMode, setFormMode] = useState<'none' | 'create' | 'edit'>('none');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [linkSourceId, setLinkSourceId] = useState('');
  const [linkTargetType, setLinkTargetType] = useState<'person' | 'relationship'>('person');
  const [linkTargetId, setLinkTargetId] = useState('');
  const [linking, setLinking] = useState(false);
  const [linkError, setLinkError] = useState<string | null>(null);
  const [linkSuccess, setLinkSuccess] = useState(false);

  const [personLinks, setPersonLinks] = useState<PersonSourceRead[]>([]);
  const [relLinks, setRelLinks] = useState<RelationshipSourceRead[]>([]);
  const [linksLoadState, setLinksLoadState] = useState<'loading' | 'ok' | 'error'>('loading');
  const [unlinkError, setUnlinkError] = useState<string | null>(null);

  const [sourcesPage, setSourcesPage] = useState(1);
  const SOURCES_PAGE_SIZE = 8;

  useEffect(() => {
    void loadSources();
  }, []);

  useEffect(() => {
    void loadSourceLinks();
  }, []);

  useEffect(() => {
    void loadPersonsAndRelationships();
  }, [personsVersion, relationshipsVersion]);

  async function loadSources() {
    setLoadState('loading');
    try {
      const data = await listSources(token);
      setSources(data);
      setLoadState('ok');
    } catch {
      setLoadState('error');
    }
  }

  async function loadPersonsAndRelationships() {
    try {
      const [personsData, relsData] = await Promise.all([
        listPersons(token),
        listRelationships(token),
      ]);
      setPersons(personsData);
      setRelationships(relsData);
    } catch {
      // non-critical: linking selects will be empty
    }
  }

  async function loadSourceLinks() {
    setLinksLoadState('loading');
    try {
      const [pLinks, rLinks] = await Promise.all([
        listPersonSourceLinks(token),
        listRelationshipSourceLinks(token),
      ]);
      setPersonLinks(pLinks);
      setRelLinks(rLinks);
      setLinksLoadState('ok');
    } catch {
      setLinksLoadState('error');
    }
  }

  function openCreate() {
    setFormData(EMPTY_FORM);
    setFormMode('create');
    setEditingId(null);
    setFormError(null);
  }

  function openEdit(s: SourceRead) {
    setFormData(sourceToForm(s));
    setFormMode('edit');
    setEditingId(s.id);
    setFormError(null);
  }

  function cancelForm() {
    setFormMode('none');
    setEditingId(null);
    setFormError(null);
  }

  function setField(key: keyof FormData, value: string) {
    setFormData((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!formData.title.trim()) return;
    setSaving(true);
    setFormError(null);
    try {
      if (formMode === 'create') {
        const created = await createSource(token, formToPayload(formData));
        setSources((prev) => [...prev, created]);
      } else if (formMode === 'edit' && editingId !== null) {
        const payload: SourceUpdate = formToPayload(formData);
        const updated = await updateSource(token, editingId, payload);
        setSources((prev) => prev.map((s) => (s.id === editingId ? updated : s)));
        onSourceLinksChanged?.();
      }
      setFormMode('none');
      setEditingId(null);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(s: SourceRead) {
    if (!window.confirm('Удалить источник? Это действие нельзя отменить.')) return;
    try {
      await deleteSource(token, s.id);
      setSources((prev) => prev.filter((x) => x.id !== s.id));
      void loadSourceLinks();
      onSourceLinksChanged?.();
      if (editingId === s.id) {
        setFormMode('none');
        setEditingId(null);
      }
      if (linkSourceId === s.id) {
        setLinkSourceId('');
        setLinkError(null);
        setLinkSuccess(false);
      }
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Ошибка удаления');
    }
  }

  async function handleLink(e: React.FormEvent) {
    e.preventDefault();
    setLinkError(null);
    setLinkSuccess(false);

    if (!linkSourceId) {
      setLinkError('Выберите источник.');
      return;
    }
    if (!linkTargetId) {
      setLinkError('Выберите объект для привязки.');
      return;
    }

    setLinking(true);
    try {
      if (linkTargetType === 'person') {
        await linkSourceToPerson(token, linkSourceId, linkTargetId);
      } else {
        await linkSourceToRelationship(token, linkSourceId, linkTargetId);
      }
      await loadSourceLinks();
      onSourceLinksChanged?.();
      setLinkSuccess(true);
      setLinkTargetId('');
    } catch (err) {
      setLinkError(err instanceof ApiError ? err.message : 'Ошибка привязки');
    } finally {
      setLinking(false);
    }
  }

  async function handleUnlinkPerson(link: PersonSourceRead) {
    if (!window.confirm('Отвязать источник? Это действие нельзя отменить.')) return;
    setUnlinkError(null);
    try {
      await unlinkSourceFromPerson(token, link.source_id, link.person_id);
      await loadSourceLinks();
      onSourceLinksChanged?.();
    } catch (err) {
      setUnlinkError(err instanceof ApiError ? err.message : 'Ошибка отвязки');
    }
  }

  async function handleUnlinkRelationship(link: RelationshipSourceRead) {
    if (!window.confirm('Отвязать источник? Это действие нельзя отменить.')) return;
    setUnlinkError(null);
    try {
      await unlinkSourceFromRelationship(token, link.source_id, link.relationship_id);
      await loadSourceLinks();
      onSourceLinksChanged?.();
    } catch (err) {
      setUnlinkError(err instanceof ApiError ? err.message : 'Ошибка отвязки');
    }
  }

  function findPerson(id: string): PersonRead | undefined {
    return persons.find((p) => p.id === id);
  }

  function formatRelationshipLabel(rel: RelationshipRead): string {
    const parent = findPerson(rel.parent_id);
    const child = findPerson(rel.child_id);
    const parentName = parent ? formatFullName(parent) : 'Персона не найдена';
    const childName = child ? formatFullName(child) : 'Персона не найдена';
    return `${parentName} → ${childName}`;
  }

  const sourcesTotalPages = Math.ceil(sources.length / SOURCES_PAGE_SIZE);
  const safeSourcesPage = sourcesTotalPages > 0 ? Math.min(sourcesPage, sourcesTotalPages) : 1;
  const pagedSources = sources.slice(
    (safeSourcesPage - 1) * SOURCES_PAGE_SIZE,
    safeSourcesPage * SOURCES_PAGE_SIZE
  );

  const formTitle = formMode === 'create' ? 'Новый источник' : 'Редактировать источник';

  return (
    <section className="panel sources-panel">
      <div className="sources-header">
        <div>
          <h2>Источники</h2>
          <p className="sources-subtitle">
            Фиксируйте архивные документы, ссылки и комментарии к достоверности сведений.
          </p>
        </div>
        {formMode === 'none' && (
          <button type="button" className="btn-add" onClick={openCreate}>
            + Добавить источник
          </button>
        )}
      </div>

      {formMode !== 'none' && (
        <div className="sources-form-section">
          <p className="sources-form-title">{formTitle}</p>
          <form
            className="sources-form-grid"
            onSubmit={(e) => {
              void handleSave(e);
            }}
          >
            <label className="field">
              <span>Название *</span>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setField('title', e.target.value)}
                required
                placeholder="Метрическая книга..."
              />
            </label>
            <label className="field">
              <span>Архивный шифр</span>
              <input
                type="text"
                value={formData.archive_reference}
                onChange={(e) => setField('archive_reference', e.target.value)}
                placeholder="РГАДА, ф.1, оп.1, д.1"
              />
            </label>
            <label className="field field-full">
              <span>URL</span>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => setField('url', e.target.value)}
                placeholder="https://..."
              />
            </label>
            <label className="field field-full">
              <span>Комментарий к достоверности</span>
              <textarea
                value={formData.reliability_comment}
                onChange={(e) => setField('reliability_comment', e.target.value)}
                rows={2}
                placeholder="Степень достоверности источника..."
              />
            </label>
            <label className="field field-full">
              <span>Заметки</span>
              <textarea
                value={formData.notes}
                onChange={(e) => setField('notes', e.target.value)}
                rows={3}
                placeholder="Дополнительные сведения"
              />
            </label>
            {formError !== null && <p className="form-error field-full">{formError}</p>}
            <div className="form-actions field-full">
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? 'Сохранение…' : 'Сохранить'}
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={cancelForm}
                disabled={saving}
              >
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      {loadState === 'loading' && <SkeletonCardList count={3} />}
      {loadState === 'error' && (
        <p className="source-error">
          Не удалось загрузить данные.{' '}
          <button
            type="button"
            className="link-btn"
            onClick={() => {
              void loadSources();
            }}
          >
            Повторить
          </button>
        </p>
      )}
      {loadState === 'ok' && sources.length === 0 && formMode === 'none' && (
        <p className="source-empty">Источников пока нет. Добавьте первый архивный источник.</p>
      )}

      {loadState === 'ok' && sources.length > 0 && (
        <>
          <ul className="sources-list">
            {pagedSources.map((s) => (
              <li
                key={s.id}
                className={`source-card${editingId === s.id ? ' source-card-editing' : ''}`}
              >
                <div className="source-card-main">
                  <span className="source-title">{s.title}</span>
                  <div className="source-meta">
                    {s.archive_reference && <span>{s.archive_reference}</span>}
                    {s.url && (
                      <a href={s.url} target="_blank" rel="noreferrer" className="source-url">
                        {s.url}
                      </a>
                    )}
                    {s.reliability_comment && <span>{s.reliability_comment}</span>}
                  </div>
                  {s.notes !== null && s.notes !== '' && <p className="source-notes">{s.notes}</p>}
                </div>
                <div className="source-actions">
                  <button
                    type="button"
                    className="btn-action btn-action-edit"
                    onClick={() => openEdit(s)}
                    disabled={formMode !== 'none' && editingId !== s.id}
                    aria-label="Редактировать"
                  >
                    Редактировать
                  </button>
                  <button
                    type="button"
                    className="btn-action btn-action-delete"
                    onClick={() => {
                      void handleDelete(s);
                    }}
                    aria-label="Удалить"
                  >
                    Удалить
                  </button>
                </div>
              </li>
            ))}
          </ul>
          <Pagination
            page={safeSourcesPage}
            pageSize={SOURCES_PAGE_SIZE}
            totalItems={sources.length}
            onPageChange={setSourcesPage}
            label="Страницы источников"
          />
        </>
      )}

      {loadState === 'ok' && sources.length > 0 && (
        <div className="source-links">
          <p className="source-links-title">Текущие привязки</p>
          {linksLoadState === 'loading' && <SkeletonCardList count={2} compact />}
          {linksLoadState === 'error' && (
            <p className="source-links-error">Не удалось загрузить привязки источников.</p>
          )}
          {linksLoadState === 'ok' && unlinkError !== null && (
            <p className="source-links-error">{unlinkError}</p>
          )}
          {linksLoadState === 'ok' &&
            (personLinks.length === 0 && relLinks.length === 0 ? (
              <p className="source-links-empty">
                Привязок пока нет. Выберите источник и объект, чтобы связать доказательство с
                данными.
              </p>
            ) : (
              <ul className="source-links-list">
                {personLinks.map((link) => {
                  const source = sources.find((s) => s.id === link.source_id);
                  const person = findPerson(link.person_id);
                  return (
                    <li key={link.id} className="source-link-card">
                      <div className="source-link-card-main">
                        <span className="source-link-kind">Персона</span>
                        <span className="source-link-target">
                          {source?.title ?? '-'}
                          {' → '}
                          {person ? formatFullName(person) : 'Персона не найдена'}
                        </span>
                        {link.comment !== null && (
                          <span className="source-link-comment">{link.comment}</span>
                        )}
                      </div>
                      <div className="source-link-actions">
                        <button
                          type="button"
                          className="btn-action btn-action-delete"
                          onClick={() => {
                            void handleUnlinkPerson(link);
                          }}
                          aria-label="Отвязать"
                        >
                          Отвязать
                        </button>
                      </div>
                    </li>
                  );
                })}
                {relLinks.map((link) => {
                  const source = sources.find((s) => s.id === link.source_id);
                  const rel = relationships.find((r) => r.id === link.relationship_id);
                  const relLabel = rel ? formatRelationshipLabel(rel) : 'Связь не найдена';
                  return (
                    <li key={link.id} className="source-link-card">
                      <div className="source-link-card-main">
                        <span className="source-link-kind">Связь</span>
                        <span className="source-link-target">
                          {source?.title ?? '-'}
                          {' → '}
                          {relLabel}
                        </span>
                        {link.comment !== null && (
                          <span className="source-link-comment">{link.comment}</span>
                        )}
                      </div>
                      <div className="source-link-actions">
                        <button
                          type="button"
                          className="btn-action btn-action-delete"
                          onClick={() => {
                            void handleUnlinkRelationship(link);
                          }}
                          aria-label="Отвязать"
                        >
                          Отвязать
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ))}
        </div>
      )}

      {loadState === 'ok' && sources.length > 0 && (
        <div className="source-linking">
          <p className="source-linking-title">Привязки</p>
          <form
            className="source-linking-form"
            onSubmit={(e) => {
              void handleLink(e);
            }}
          >
            <label className="field">
              <span>Источник</span>
              <select
                value={linkSourceId}
                onChange={(e) => {
                  setLinkSourceId(e.target.value);
                  setLinkError(null);
                  setLinkSuccess(false);
                }}
              >
                <option value="">- выбрать -</option>
                {sources.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.title}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Тип</span>
              <select
                value={linkTargetType}
                onChange={(e) => {
                  setLinkTargetType(e.target.value as 'person' | 'relationship');
                  setLinkTargetId('');
                  setLinkError(null);
                  setLinkSuccess(false);
                }}
              >
                <option value="person">Персона</option>
                <option value="relationship">Связь</option>
              </select>
            </label>

            <label className="field">
              <span>{linkTargetType === 'person' ? 'Персона' : 'Связь'}</span>
              <select
                value={linkTargetId}
                onChange={(e) => {
                  setLinkTargetId(e.target.value);
                  setLinkError(null);
                  setLinkSuccess(false);
                }}
              >
                <option value="">- выбрать -</option>
                {linkTargetType === 'person'
                  ? persons.map((p) => (
                      <option key={p.id} value={p.id}>
                        {formatFullName(p)}
                      </option>
                    ))
                  : relationships.map((rel) => (
                      <option key={rel.id} value={rel.id}>
                        {formatRelationshipLabel(rel)}
                      </option>
                    ))}
              </select>
            </label>

            <div className="form-actions source-linking-actions">
              <button type="submit" className="btn-primary" disabled={linking}>
                {linking ? 'Привязка…' : 'Привязать'}
              </button>
            </div>

            {linkError !== null && (
              <p className="source-error source-linking-message">{linkError}</p>
            )}
            {linkSuccess && (
              <p className="source-success source-linking-message">Источник привязан.</p>
            )}
          </form>
        </div>
      )}
    </section>
  );
}
