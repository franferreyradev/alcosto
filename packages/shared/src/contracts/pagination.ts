export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  next_cursor: string | null;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}
