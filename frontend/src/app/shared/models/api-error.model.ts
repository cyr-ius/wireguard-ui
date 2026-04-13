export interface ErrorDetail {
  field?: string;
  message: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: ErrorDetail[];
}
