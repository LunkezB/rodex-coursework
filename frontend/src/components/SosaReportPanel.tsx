import { useEffect, useState } from 'react';
import { ApiError } from '../api/auth';
import type { PersonRead } from '../api/persons';
import { listPersons } from '../api/persons';
import type { SosaGeneration, SosaReport, SosaReportPerson } from '../api/reports';
import { downloadSosaCsv, getSosaReport } from '../api/reports';
import { SosaTreeView } from './SosaTreeView';
import { SkeletonCardList } from './Skeletons';

interface Props {
  token: string;
  personsVersion: number;
}

type ViewMode = 'list' | 'tree';

const SEX_LABEL: Record<string, string> = {
  male: 'Мужской',
  female: 'Женский',
  unknown: 'Неизвестно',
};

const MAX_DEPTH_OPTIONS = [3, 5, 8, 10];

function formatFullName(
  surname: string | null,
  given_name: string,
  patronymic: string | null
): string {
  return [surname, given_name, patronymic].filter(Boolean).join(' ');
}

function matchesReportSearch(rp: SosaReportPerson, gen: SosaGeneration, query: string): boolean {
  if (!query) return true;
  const q = query.toLowerCase();
  const p = rp.person;
  const sexLabel = SEX_LABEL[p.sex] ?? p.sex;
  const fields: (string | null | undefined)[] = [
    p.surname,
    p.given_name,
    p.patronymic,
    sexLabel,
    p.birth_date,
    p.birth_place,
    p.death_date,
    p.death_place,
    String(rp.sosa_number),
    String(gen.generation),
  ];
  return fields.some((f) => f != null && f.toLowerCase().includes(q));
}

function resetReport(
  setReport: (r: SosaReport | null) => void,
  setReportState: (s: 'idle' | 'loading' | 'ok' | 'error') => void,
  setReportError: (e: string | null) => void,
  setCsvError: (e: string | null) => void,
  setViewMode: (m: ViewMode) => void
) {
  setReport(null);
  setReportState('idle');
  setReportError(null);
  setCsvError(null);
  setViewMode('list');
}

export function SosaReportPanel({ token, personsVersion }: Props) {
  const [persons, setPersons] = useState<PersonRead[]>([]);
  const [personsLoadState, setPersonsLoadState] = useState<'loading' | 'ok' | 'error'>('loading');

  const [probandId, setProbandId] = useState('');
  const [maxDepth, setMaxDepth] = useState(5);

  const [report, setReport] = useState<SosaReport | null>(null);
  const [reportState, setReportState] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle');
  const [reportError, setReportError] = useState<string | null>(null);

  const [csvLoading, setCsvLoading] = useState(false);
  const [csvError, setCsvError] = useState<string | null>(null);

  const [viewMode, setViewMode] = useState<ViewMode>('list');

  const [reportSearchQuery, setReportSearchQuery] = useState('');
  const [generationFilter, setGenerationFilter] = useState('all');

  useEffect(() => {
    void loadPersons();
  }, [personsVersion]);

  async function loadPersons() {
    setPersonsLoadState('loading');
    try {
      const data = await listPersons(token);
      setPersons(data);
      setPersonsLoadState('ok');
    } catch {
      setPersonsLoadState('error');
    }
  }

  async function handleBuildReport(e: React.FormEvent) {
    e.preventDefault();
    if (!probandId) return;
    setReportState('loading');
    setReportError(null);
    setReport(null);
    try {
      const data = await getSosaReport(token, probandId, maxDepth);
      setReport(data);
      setReportState('ok');
    } catch (err) {
      setReportError(err instanceof ApiError ? err.message : 'Ошибка построения росписи');
      setReportState('error');
    }
  }

  async function handleDownloadCsv() {
    if (!probandId) return;
    setCsvLoading(true);
    setCsvError(null);
    try {
      await downloadSosaCsv(token, probandId, maxDepth);
    } catch (err) {
      setCsvError(err instanceof ApiError ? err.message : 'Ошибка скачивания CSV');
    } finally {
      setCsvLoading(false);
    }
  }

  function resetFilters() {
    setReportSearchQuery('');
    setGenerationFilter('all');
  }

  const trimmedQuery = reportSearchQuery.trim();

  const filteredGenerations =
    report === null
      ? []
      : report.generations
          .filter(
            (gen) => generationFilter === 'all' || String(gen.generation) === generationFilter
          )
          .map((gen) => ({
            ...gen,
            persons: gen.persons.filter((rp) => matchesReportSearch(rp, gen, trimmedQuery)),
          }))
          .filter((gen) => gen.persons.length > 0);

  const totalPersons =
    report === null ? 0 : report.generations.reduce((sum, gen) => sum + gen.persons.length, 0);

  const totalFiltered = filteredGenerations.reduce((sum, gen) => sum + gen.persons.length, 0);

  const filtersActive = trimmedQuery !== '' || generationFilter !== 'all';

  const highlightedSosaNumbers = new Set<number>(
    filteredGenerations.flatMap((gen) => gen.persons.map((rp) => rp.sosa_number))
  );

  const sortedGenerationOptions =
    report === null ? [] : [...report.generations].sort((a, b) => a.generation - b.generation);

  const showEmptyPersons = personsLoadState === 'ok' && persons.length === 0;
  const showControls = personsLoadState === 'ok' && persons.length > 0;
  const canBuildReport = probandId !== '' && reportState !== 'loading';
  const canDownloadCsv = probandId !== '' && !csvLoading;

  return (
    <section className="panel sosa-panel">
      <div className="sosa-header">
        <div>
          <h2>Роспись</h2>
          <p className="sosa-subtitle">Сформируйте поколенную роспись по выбранному пробанду.</p>
        </div>
      </div>

      {personsLoadState === 'loading' && <SkeletonCardList count={2} compact />}

      {personsLoadState === 'error' && (
        <p className="sosa-error">
          Не удалось загрузить данные.{' '}
          <button
            type="button"
            className="link-btn"
            onClick={() => {
              void loadPersons();
            }}
          >
            Повторить
          </button>
        </p>
      )}

      {showEmptyPersons && (
        <p className="sosa-empty">Добавьте хотя бы одну персону, чтобы построить роспись.</p>
      )}

      {showControls && (
        <div className="sosa-controls">
          <form
            className="sosa-form"
            onSubmit={(e) => {
              void handleBuildReport(e);
            }}
          >
            <label className="field">
              <span>Пробанд</span>
              <select
                value={probandId}
                onChange={(e) => {
                  setProbandId(e.target.value);
                  resetReport(setReport, setReportState, setReportError, setCsvError, setViewMode);
                  setReportSearchQuery('');
                  setGenerationFilter('all');
                }}
                required
              >
                <option value="">- выбрать -</option>
                {persons.map((p) => (
                  <option key={p.id} value={p.id}>
                    {formatFullName(p.surname, p.given_name, p.patronymic)}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Глубина</span>
              <select
                value={maxDepth}
                onChange={(e) => {
                  setMaxDepth(Number(e.target.value));
                  resetReport(setReport, setReportState, setReportError, setCsvError, setViewMode);
                  setReportSearchQuery('');
                  setGenerationFilter('all');
                }}
              >
                {MAX_DEPTH_OPTIONS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </label>

            <div className="sosa-form-actions">
              <button type="submit" className="btn-primary" disabled={!canBuildReport}>
                {reportState === 'loading' ? 'Построение…' : 'Построить роспись'}
              </button>
              <button
                type="button"
                className="btn-secondary"
                disabled={!canDownloadCsv}
                onClick={() => {
                  void handleDownloadCsv();
                }}
              >
                {csvLoading ? 'Подготовка CSV…' : 'Скачать CSV'}
              </button>
            </div>
          </form>

          {csvError !== null && <p className="sosa-error">{csvError}</p>}
          {reportState === 'error' && reportError !== null && (
            <p className="sosa-error">{reportError}</p>
          )}
        </div>
      )}

      {showControls && reportState === 'idle' && (
        <p className="sosa-empty">Выберите пробанда и постройте роспись.</p>
      )}

      {showControls && reportState === 'loading' && <SkeletonCardList count={3} compact />}

      {reportState === 'ok' && report !== null && (
        <>
          {report.warnings.length > 0 && (
            <div className="sosa-warning">
              <p className="sosa-warning-title">Предупреждения</p>
              <ul className="sosa-warning-list">
                {report.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="sosa-view-toggle">
            <button
              type="button"
              className={`sosa-view-toggle-btn${viewMode === 'list' ? ' active' : ''}`}
              onClick={() => setViewMode('list')}
            >
              Список
            </button>
            <button
              type="button"
              className={`sosa-view-toggle-btn${viewMode === 'tree' ? ' active' : ''}`}
              onClick={() => setViewMode('tree')}
            >
              Дерево
            </button>
          </div>

          <div className="sosa-report-toolbar">
            <input
              type="search"
              className="sosa-report-search"
              placeholder="Поиск по росписи..."
              value={reportSearchQuery}
              onChange={(e) => setReportSearchQuery(e.target.value)}
            />
            <select
              className="sosa-report-filter"
              value={generationFilter}
              onChange={(e) => setGenerationFilter(e.target.value)}
            >
              <option value="all">Все поколения</option>
              {sortedGenerationOptions.map((gen) => (
                <option key={gen.generation} value={String(gen.generation)}>
                  Поколение {gen.generation}
                </option>
              ))}
            </select>
            {filtersActive && (
              <button type="button" className="sosa-report-reset-btn" onClick={resetFilters}>
                Сбросить
              </button>
            )}
            <span className="sosa-report-count">
              Найдено: {totalFiltered} из {totalPersons}
            </span>
          </div>

          {viewMode === 'list' && (
            <div className="sosa-result">
              {filteredGenerations.length === 0 ? (
                <p className="sosa-report-filter-empty">По заданным фильтрам ничего не найдено.</p>
              ) : (
                filteredGenerations.map((gen) => (
                  <div key={gen.generation} className="sosa-generation">
                    <p className="sosa-generation-title">Поколение {gen.generation}</p>
                    <ul className="sosa-person-list">
                      {gen.persons.map((rp) => {
                        const p = rp.person;
                        const name = formatFullName(p.surname, p.given_name, p.patronymic);
                        const birthLine = [p.birth_date, p.birth_place].filter(Boolean).join(', ');
                        const deathLine = [p.death_date, p.death_place].filter(Boolean).join(', ');
                        return (
                          <li key={rp.sosa_number} className="sosa-person-card">
                            <span className="sosa-number">{rp.sosa_number}</span>
                            <div className="sosa-person-main">
                              <span className="sosa-person-name">{name}</span>
                              <span className="sosa-person-meta">
                                <span>{SEX_LABEL[p.sex] ?? p.sex}</span>
                                {birthLine && <span>р. {birthLine}</span>}
                                {deathLine && <span>ум. {deathLine}</span>}
                              </span>
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ))
              )}
            </div>
          )}

          {viewMode === 'tree' && (
            <>
              {filtersActive && highlightedSosaNumbers.size === 0 && (
                <p className="sosa-tree-filter-note">
                  В дереве нет совпадений по заданным фильтрам.
                </p>
              )}
              <SosaTreeView
                report={report}
                highlightedSosaNumbers={filtersActive ? highlightedSosaNumbers : undefined}
              />
            </>
          )}
        </>
      )}
    </section>
  );
}
