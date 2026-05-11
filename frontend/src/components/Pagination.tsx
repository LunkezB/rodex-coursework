interface Props {
  page: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  label?: string;
}

export function Pagination({ page, pageSize, totalItems, onPageChange, label }: Props) {
  const totalPages = Math.ceil(totalItems / pageSize);
  if (totalPages <= 1) return null;

  return (
    <div className="pagination" role="navigation" aria-label={label ?? "Пагинация"}>
      <button
        type="button"
        className="pagination-button"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        aria-label="Предыдущая страница"
      >
        Назад
      </button>
      <span className="pagination-status">
        Страница {page} из {totalPages}
      </span>
      <button
        type="button"
        className="pagination-button"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        aria-label="Следующая страница"
      >
        Вперёд
      </button>
    </div>
  );
}
