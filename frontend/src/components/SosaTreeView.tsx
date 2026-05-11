import { useLayoutEffect, useRef, useState } from "react";
import type { SosaReport } from "../api/reports";

interface Props {
  report: SosaReport;
  highlightedSosaNumbers?: Set<number>;
}

interface ConnectorLine {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

const SEX_LABEL: Record<string, string> = {
  male: "Мужской",
  female: "Женский",
  unknown: "Неизвестно",
};

function formatFullName(
  surname: string | null,
  given_name: string,
  patronymic: string | null,
): string {
  return [surname, given_name, patronymic].filter(Boolean).join(" ");
}

export function SosaTreeView({ report, highlightedSosaNumbers }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cardRefs = useRef<Map<number, HTMLElement>>(new Map());
  const [lines, setLines] = useState<ConnectorLine[]>([]);

  const sortedGenerations = [...report.generations]
    .sort((a, b) => a.generation - b.generation)
    .map((gen) => ({
      ...gen,
      persons: [...gen.persons].sort((a, b) => a.sosa_number - b.sosa_number),
    }));

  useLayoutEffect(() => {
    function measure() {
      const currentContainer = containerRef.current;
      if (currentContainer === null) return;

      const containerRect = currentContainer.getBoundingClientRect();
      const newLines: ConnectorLine[] = [];

      for (const gen of report.generations) {
        for (const rp of gen.persons) {
          const childEl = cardRefs.current.get(rp.sosa_number);
          if (!childEl) continue;

          const childRect = childEl.getBoundingClientRect();
          const x1 = childRect.right - containerRect.left;
          const y1 = childRect.top + childRect.height / 2 - containerRect.top;

          for (const parentNum of [
            rp.sosa_number * 2,
            rp.sosa_number * 2 + 1,
          ]) {
            const parentEl = cardRefs.current.get(parentNum);
            if (!parentEl) continue;

            const parentRect = parentEl.getBoundingClientRect();
            newLines.push({
              x1,
              y1,
              x2: parentRect.left - containerRect.left,
              y2: parentRect.top + parentRect.height / 2 - containerRect.top,
            });
          }
        }
      }

      setLines(newLines);
    }

    measure();

    const currentContainer = containerRef.current;
    if (currentContainer === null) return;

    if (typeof ResizeObserver !== "undefined") {
      const ro = new ResizeObserver(measure);
      ro.observe(currentContainer);
      return () => ro.disconnect();
    }

    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [report]);

  if (sortedGenerations.length === 0) {
    return <p className="sosa-empty">Нет данных для визуализации.</p>;
  }

  return (
    <div className="sosa-tree">
      <div className="sosa-tree-scroll">
        <div ref={containerRef} className="sosa-tree-inner">
          <svg className="sosa-tree-svg" aria-hidden="true">
            {lines.map((line, i) => {
              const mx = (line.x1 + line.x2) / 2;
              return (
                <path
                  key={i}
                  d={`M ${line.x1} ${line.y1} C ${mx} ${line.y1} ${mx} ${line.y2} ${line.x2} ${line.y2}`}
                  className="sosa-tree-connector"
                />
              );
            })}
          </svg>
          <div className="sosa-tree-columns">
            {sortedGenerations.map((gen) => (
              <div key={gen.generation} className="sosa-tree-column">
                <p className="sosa-tree-column-title">
                  Поколение {gen.generation}
                </p>
                {gen.persons.map((rp) => {
                  const p = rp.person;
                  const name = formatFullName(
                    p.surname,
                    p.given_name,
                    p.patronymic,
                  );
                  const birthLine = [p.birth_date, p.birth_place]
                    .filter(Boolean)
                    .join(", ");
                  const deathLine = [p.death_date, p.death_place]
                    .filter(Boolean)
                    .join(", ");
                  const isHighlighted =
                    highlightedSosaNumbers !== undefined &&
                    highlightedSosaNumbers.has(rp.sosa_number);
                  return (
                    <div
                      key={rp.sosa_number}
                      className={`sosa-tree-node${isHighlighted ? " sosa-tree-node-highlighted" : ""}`}
                      ref={(el) => {
                        if (el) cardRefs.current.set(rp.sosa_number, el);
                        else cardRefs.current.delete(rp.sosa_number);
                      }}
                    >
                      <span className="sosa-tree-node-number">
                        {rp.sosa_number}
                      </span>
                      <span className="sosa-tree-node-name">{name}</span>
                      <span className="sosa-tree-node-meta">
                        {SEX_LABEL[p.sex] ?? p.sex}
                        {birthLine && <> · р. {birthLine}</>}
                      </span>
                      {deathLine && (
                        <span className="sosa-tree-node-meta">
                          ум. {deathLine}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
