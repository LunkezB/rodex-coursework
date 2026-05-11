import { useEffect, useState } from 'react';
import type { PersonRead, PersonCreate, PersonUpdate, Sex } from '../api/persons';
import { listPersons, createPerson, updatePerson, deletePerson } from '../api/persons';
import { ApiError } from '../api/auth';
import type { SourceRead } from '../api/sources';
import { listPersonSourceLinks, listSources } from '../api/sources';
import { Pagination } from './Pagination';
import { SkeletonCardList, SkeletonToolbar } from './Skeletons';

type SexFilter = 'all' | 'male' | 'female' | 'unknown';
type DateFilter =
  | 'all'
  | 'has_birth_date'
  | 'missing_birth_date'
  | 'has_death_date'
  | 'missing_death_date';

interface Props {
  token: string;
  onPersonsChanged?: () => void;
  sourceLinksVersion?: number;
}

interface FormData {
  surname: string;
  given_name: string;
  patronymic: string;
  name_variants: string;
  sex: string;
  birth_date: string;
  birth_place: string;
  death_date: string;
  death_place: string;
  notes: string;
}

const EMPTY_FORM: FormData = {
  surname: '',
  given_name: '',
  patronymic: '',
  name_variants: '',
  sex: 'unknown',
  birth_date: '',
  birth_place: '',
  death_date: '',
  death_place: '',
  notes: '',
};

const SEX_LABEL: Record<Sex, string> = {
  male: 'Мужской',
  female: 'Женский',
  unknown: 'Неизвестно',
};

function personToForm(p: PersonRead): FormData {
  return {
    surname: p.surname ?? '',
    given_name: p.given_name,
    patronymic: p.patronymic ?? '',
    name_variants: p.name_variants ?? '',
    sex: p.sex,
    birth_date: p.birth_date ?? '',
    birth_place: p.birth_place ?? '',
    death_date: p.death_date ?? '',
    death_place: p.death_place ?? '',
    notes: p.notes ?? '',
  };
}

function formToPayload(f: FormData): PersonCreate {
  return {
    surname: f.surname.trim() || null,
    given_name: f.given_name.trim(),
    patronymic: f.patronymic.trim() || null,
    name_variants: f.name_variants.trim() || null,
    sex: f.sex as Sex,
    birth_date: f.birth_date.trim() || null,
    birth_place: f.birth_place.trim() || null,
    death_date: f.death_date.trim() || null,
    death_place: f.death_place.trim() || null,
    notes: f.notes.trim() || null,
  };
}

function formatFullName(p: PersonRead): string {
  return [p.surname, p.given_name, p.patronymic].filter(Boolean).join(' ');
}

function formatBirthLine(p: PersonRead): string | null {
  if (!p.birth_date && !p.birth_place) return null;
  return [p.birth_date, p.birth_place].filter(Boolean).join(', ');
}

function formatDeathLine(p: PersonRead): string | null {
  if (!p.death_date && !p.death_place) return null;
  return [p.death_date, p.death_place].filter(Boolean).join(', ');
}

function matchesSearch(p: PersonRead, query: string, sourceText?: string): boolean {
  if (!query) return true;
  const q = query.toLowerCase();
  const fields: (string | null | undefined)[] = [
    p.surname,
    p.given_name,
    p.patronymic,
    p.name_variants,
    p.birth_date,
    p.birth_place,
    p.death_date,
    p.death_place,
    p.notes,
  ];
  if (fields.some((f) => f != null && f.toLowerCase().includes(q))) return true;
  if (sourceText !== undefined && sourceText.toLowerCase().includes(q)) return true;
  return false;
}

function matchesSex(p: PersonRead, filter: SexFilter): boolean {
  if (filter === 'all') return true;
  return p.sex === filter;
}

function matchesDate(p: PersonRead, filter: DateFilter): boolean {
  switch (filter) {
    case 'all':
      return true;
    case 'has_birth_date':
      return p.birth_date != null && p.birth_date !== '';
    case 'missing_birth_date':
      return p.birth_date == null || p.birth_date === '';
    case 'has_death_date':
      return p.death_date != null && p.death_date !== '';
    case 'missing_death_date':
      return p.death_date == null || p.death_date === '';
  }
}

export function PersonsPanel({ token, onPersonsChanged, sourceLinksVersion }: Props) {
  const [persons, setPersons] = useState<PersonRead[]>([]);
  const [loadState, setLoadState] = useState<'loading' | 'ok' | 'error'>('loading');
  const [formMode, setFormMode] = useState<'none' | 'create' | 'edit'>('none');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [sexFilter, setSexFilter] = useState<SexFilter>('all');
  const [dateFilter, setDateFilter] = useState<DateFilter>('all');

  const [personSourceCounts, setPersonSourceCounts] = useState<Map<string, number>>(new Map());
  const [personSourceTexts, setPersonSourceTexts] = useState<Map<string, string>>(new Map());

  const [personPage, setPersonPage] = useState(1);
  const PERSON_PAGE_SIZE = 10;

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    void loadSourceCounts();
  }, [sourceLinksVersion]);

  async function load() {
    setLoadState('loading');
    try {
      const data = await listPersons(token);
      setPersons(data);
      setLoadState('ok');
    } catch {
      setLoadState('error');
    }
  }

  async function loadSourceCounts() {
    try {
      const [links, sources] = await Promise.all([
        listPersonSourceLinks(token),
        listSources(token),
      ]);
      const sourcesById = new Map<string, SourceRead>(sources.map((s) => [s.id, s]));
      const counts = new Map<string, number>();
      const texts = new Map<string, string>();
      for (const link of links) {
        counts.set(link.person_id, (counts.get(link.person_id) ?? 0) + 1);
        const src = sourcesById.get(link.source_id);
        if (src) {
          const chunk = [
            src.title,
            src.archive_reference,
            src.url,
            src.reliability_comment,
            src.notes,
          ]
            .filter(Boolean)
            .join(' ');
          const prev = texts.get(link.person_id);
          texts.set(link.person_id, prev !== undefined ? `${prev} ${chunk}` : chunk);
        }
      }
      setPersonSourceCounts(counts);
      setPersonSourceTexts(texts);
    } catch {
      // ignore non-critical errors
    }
  }

  function openCreate() {
    setFormData(EMPTY_FORM);
    setFormMode('create');
    setEditingId(null);
    setFormError(null);
  }

  function openEdit(p: PersonRead) {
    setFormData(personToForm(p));
    setFormMode('edit');
    setEditingId(p.id);
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

  function resetFilters() {
    setSearchQuery('');
    setSexFilter('all');
    setDateFilter('all');
    setPersonPage(1);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!formData.given_name.trim()) return;
    setSaving(true);
    setFormError(null);
    try {
      if (formMode === 'create') {
        const created = await createPerson(token, formToPayload(formData));
        setPersons((prev) => [...prev, created]);
        onPersonsChanged?.();
      } else if (formMode === 'edit' && editingId !== null) {
        const payload: PersonUpdate = formToPayload(formData);
        const updated = await updatePerson(token, editingId, payload);
        setPersons((prev) => prev.map((p) => (p.id === editingId ? updated : p)));
        onPersonsChanged?.();
      }
      setFormMode('none');
      setEditingId(null);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(p: PersonRead) {
    if (!window.confirm('Удалить персону? Это действие нельзя отменить.')) return;
    try {
      await deletePerson(token, p.id);
      setPersons((prev) => prev.filter((x) => x.id !== p.id));
      if (editingId === p.id) {
        setFormMode('none');
        setEditingId(null);
      }
      onPersonsChanged?.();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Ошибка удаления');
    }
  }

  const trimmedQuery = searchQuery.trim();
  const filteredPersons = persons.filter(
    (p) =>
      matchesSearch(p, trimmedQuery, personSourceTexts.get(p.id)) &&
      matchesSex(p, sexFilter) &&
      matchesDate(p, dateFilter)
  );
  const filtersActive = trimmedQuery !== '' || sexFilter !== 'all' || dateFilter !== 'all';

  const totalPages = Math.ceil(filteredPersons.length / PERSON_PAGE_SIZE);
  const safePage = totalPages > 0 ? Math.min(personPage, totalPages) : 1;
  const pagedPersons = filteredPersons.slice(
    (safePage - 1) * PERSON_PAGE_SIZE,
    safePage * PERSON_PAGE_SIZE
  );

  const formTitle = formMode === 'create' ? 'Новая персона' : 'Редактировать персону';

  return (
    <section className="panel persons-panel">
      <div className="persons-header">
        <div>
          <h2>Персоны</h2>
          <p className="persons-subtitle">Добавляйте персон и основные биографические сведения.</p>
        </div>
        {formMode === 'none' && (
          <button type="button" className="btn-add" onClick={openCreate}>
            + Добавить
          </button>
        )}
      </div>

      {loadState === 'ok' && persons.length > 0 && (
        <div className="persons-toolbar">
          <input
            type="search"
            className="persons-search"
            placeholder="Поиск по ФИО, месту, дате, заметкам, источникам..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPersonPage(1);
            }}
          />
          <select
            className="persons-filter"
            value={sexFilter}
            onChange={(e) => {
              setSexFilter(e.target.value as SexFilter);
              setPersonPage(1);
            }}
          >
            <option value="all">Все</option>
            <option value="male">Мужской</option>
            <option value="female">Женский</option>
            <option value="unknown">Неизвестно</option>
          </select>
          <select
            className="persons-filter"
            value={dateFilter}
            onChange={(e) => {
              setDateFilter(e.target.value as DateFilter);
              setPersonPage(1);
            }}
          >
            <option value="all">Все даты</option>
            <option value="has_birth_date">Есть дата рождения</option>
            <option value="missing_birth_date">Нет даты рождения</option>
            <option value="has_death_date">Есть дата смерти</option>
            <option value="missing_death_date">Нет даты смерти</option>
          </select>
          {filtersActive && (
            <button type="button" className="persons-reset-btn" onClick={resetFilters}>
              Сбросить
            </button>
          )}
        </div>
      )}

      {formMode !== 'none' && (
        <div className="persons-form-section">
          <p className="persons-form-title">{formTitle}</p>
          <form
            onSubmit={(e) => {
              void handleSave(e);
            }}
            className="persons-form-grid"
          >
            <label className="field">
              <span>Фамилия</span>
              <input
                type="text"
                value={formData.surname}
                onChange={(e) => setField('surname', e.target.value)}
                placeholder="Иванов"
              />
            </label>
            <label className="field">
              <span>Имя *</span>
              <input
                type="text"
                value={formData.given_name}
                onChange={(e) => setField('given_name', e.target.value)}
                required
                placeholder="Иван"
              />
            </label>
            <label className="field">
              <span>Отчество</span>
              <input
                type="text"
                value={formData.patronymic}
                onChange={(e) => setField('patronymic', e.target.value)}
                placeholder="Иванович"
              />
            </label>
            <label className="field">
              <span>Пол</span>
              <select value={formData.sex} onChange={(e) => setField('sex', e.target.value)}>
                <option value="unknown">Неизвестно</option>
                <option value="male">Мужской</option>
                <option value="female">Женский</option>
              </select>
            </label>
            <label className="field field-full">
              <span>Варианты имени</span>
              <input
                type="text"
                value={formData.name_variants}
                onChange={(e) => setField('name_variants', e.target.value)}
                placeholder="Ваня, Vanya"
              />
            </label>
            <label className="field">
              <span>Дата рождения</span>
              <input
                type="date"
                value={formData.birth_date}
                onChange={(e) => setField('birth_date', e.target.value)}
              />
            </label>
            <label className="field">
              <span>Место рождения</span>
              <input
                type="text"
                value={formData.birth_place}
                onChange={(e) => setField('birth_place', e.target.value)}
                placeholder="Москва"
              />
            </label>
            <label className="field">
              <span>Дата смерти</span>
              <input
                type="date"
                value={formData.death_date}
                onChange={(e) => setField('death_date', e.target.value)}
              />
            </label>
            <label className="field">
              <span>Место смерти</span>
              <input
                type="text"
                value={formData.death_place}
                onChange={(e) => setField('death_place', e.target.value)}
                placeholder="Санкт-Петербург"
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

      {loadState === 'loading' && (
        <>
          <SkeletonToolbar />
          <SkeletonCardList count={3} />
        </>
      )}
      {loadState === 'error' && (
        <p className="persons-error">
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
      {loadState === 'ok' && persons.length === 0 && formMode === 'none' && (
        <p className="persons-empty">Пока нет персон. Добавьте первого человека в родословную.</p>
      )}
      {loadState === 'ok' && persons.length > 0 && (
        <>
          <p className="persons-count">
            Найдено: {filteredPersons.length} из {persons.length}
          </p>
          {filteredPersons.length === 0 ? (
            <p className="persons-filter-empty">По заданным фильтрам ничего не найдено.</p>
          ) : (
            <>
              <ul className="persons-list">
                {pagedPersons.map((p) => (
                  <li
                    key={p.id}
                    className={`person-card${editingId === p.id ? ' person-card-editing' : ''}`}
                  >
                    <div className="person-card-main">
                      <span className="person-name">{formatFullName(p)}</span>
                      <span className="person-meta">
                        <span>{SEX_LABEL[p.sex]}</span>
                        {formatBirthLine(p) !== null && <span>р. {formatBirthLine(p)}</span>}
                        {formatDeathLine(p) !== null && <span>ум. {formatDeathLine(p)}</span>}
                        {(personSourceCounts.get(p.id) ?? 0) > 0 && (
                          <span className="evidence-badge">
                            Источники: {personSourceCounts.get(p.id)}
                          </span>
                        )}
                      </span>
                      {p.notes !== null && <p className="person-notes">{p.notes}</p>}
                    </div>
                    <div className="person-actions">
                      <button
                        type="button"
                        className="btn-action btn-action-edit"
                        onClick={() => openEdit(p)}
                        disabled={formMode !== 'none' && editingId !== p.id}
                        aria-label="Редактировать"
                      >
                        Редактировать
                      </button>
                      <button
                        type="button"
                        className="btn-action btn-action-delete"
                        onClick={() => {
                          void handleDelete(p);
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
                page={safePage}
                pageSize={PERSON_PAGE_SIZE}
                totalItems={filteredPersons.length}
                onPageChange={setPersonPage}
                label="Страницы персон"
              />
            </>
          )}
        </>
      )}
    </section>
  );
}
