export interface ErrorDetail {
  kind?: string;
  message: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: ErrorDetail[];
}
