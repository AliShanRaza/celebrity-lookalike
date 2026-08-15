export interface CelebrityMatchItem {
  celebrity_id: string;
  name: string;
  gender: string;
  origin?: string;
  image_url: string;
  resemblance_score: number;
  bio?: string | null;
}

export interface LandmarkPoint {
  x: number;
  y: number;
}

export interface FacialLandmarks {
  eyebrows: LandmarkPoint[];
  left_eye: LandmarkPoint[];
  right_eye: LandmarkPoint[];
  nose: LandmarkPoint[];
  mouth: LandmarkPoint[];
  contour: LandmarkPoint[];
}

export interface BestPairMatches {
  male_match: CelebrityMatchItem | null;
  female_match: CelebrityMatchItem | null;
  pair_score: number;
}

export interface MatchResultResponse {
  request_id: string;
  model_version: string;
  score_version: string;
  detected_gender?: string | null;
  primary_target_gender?: string | null;
  primary_target_origin?: string | null;
  landmarks?: FacialLandmarks | null;
  best_pair?: BestPairMatches | null;
  male_matches: CelebrityMatchItem[];
  female_matches: CelebrityMatchItem[];
  overall_matches: CelebrityMatchItem[];
  processed_at: string;
}

export interface ApiErrorResponse {
  error: string;
  message: string;
}

export class ApiError extends Error {
  code: string;
  constructor(message: string, code: string = 'UNKNOWN_ERROR') {
    super(message);
    this.name = 'ApiError';
    this.code = code;
  }
}

export interface VersionInfo {
  app_version: string;
  build_sha: string;
  recognition_provider: string;
  model_version: string;
  index_version: string;
  score_version: string;
  embedding_dimension: number;
  total_celebrities?: number;
  bollywood_celebrities?: number;
  hollywood_celebrities?: number;
}

export function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== 'undefined' && window.location && window.location.hostname) {
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://localhost:8000';
}

export function getImageUrl(url: string | null | undefined): string {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url;
  }
  const baseUrl = getApiBaseUrl();
  if (url.startsWith('/api/')) {
    return `${baseUrl}${url}`;
  }
  return `${baseUrl}/api/v1/images/serve?path=${encodeURIComponent(url)}`;
}

export async function findCelebrityMatches(file: File, targetGender: string, targetOrigin: string): Promise<MatchResultResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('target_gender', targetGender);
  formData.append('target_origin', targetOrigin);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 25000);

  try {
    const baseUrl = getApiBaseUrl();
    const response = await fetch(`${baseUrl}/api/v1/matches`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorData: ApiErrorResponse;
      try {
        errorData = await response.json();
      } catch {
        throw new ApiError(`Server error (${response.status})`, 'HTTP_ERROR');
      }
      throw new ApiError(errorData.message || 'Face detection or matching failed', errorData.error || 'API_ERROR');
    }

    const data: MatchResultResponse = await response.json();
    return data;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new ApiError('Processing timed out after 25 seconds. Please try uploading a smaller image file.', 'TIMEOUT_ERROR');
    }
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err.message || 'Failed to connect to backend matching service', 'NETWORK_ERROR');
  }
}

export async function fetchVersionInfo(): Promise<VersionInfo> {
  try {
    const baseUrl = getApiBaseUrl();
    const res = await fetch(`${baseUrl}/api/v1/version`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    return {
      app_version: '0.1.0',
      build_sha: 'dev-local-c0ff33',
      recognition_provider: 'insightface',
      model_version: 'insightface_buffalo_l_arcface',
      index_version: 'pgvector_cosine_v1',
      score_version: 'sigmoid_calibrated_v1',
      embedding_dimension: 512,
      total_celebrities: 300,
      bollywood_celebrities: 100,
      hollywood_celebrities: 200,
    };
  }
}
