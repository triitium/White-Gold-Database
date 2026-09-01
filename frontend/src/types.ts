export type User = {
  id: string;
  username: string;
  email: string;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Page<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
  has_previous: boolean;
  has_next: boolean;
};

export type MovieListItem = {
  id: string;
  title: string;
  original_title: string | null;
  release_year: number | null;
  runtime_minutes: number | null;
  poster_url: string | null;
  poster_path: string | null;
  genres: string[];
  imdb_rating: number | null;
  rt_critics_rating: number | null;
  rt_audience_rating: number | null;
  metacritic_critics_rating: number | null;
  metacritic_audience_rating: number | null;
  community_rating: number | null;
  rating_count: number;
};

export type GenreRead = {
  id: string;
  name: string;
};

export type CountryRead = {
  id: string;
  name: string;
  iso2: string | null;
  iso3: string | null;
};

export type LanguageRead = {
  id: string;
  name: string;
  iso_code: string;
  is_original: boolean;
};

export type StudioRead = {
  id: string;
  name: string;
};

export type PersonCreditRead = {
  credit_id: string;
  person_id: string;
  name: string;
  credit_type: "cast" | "crew";
  job: string | null;
  character_name: string | null;
  billing_order: number | null;
};

export type ExternalRatingRead = {
  source: string;
  rating_type: string;
  value: number;
  scale: number;
  vote_count: number | null;
  source_url: string | null;
};

export type MovieLinkRead = {
  id: string;
  source: string;
  url: string;
  label: string | null;
};

export type MovieRead = {
  id: string;
  title: string;
  original_title: string | null;
  release_year: number | null;
  release_date: string | null;
  runtime_minutes: number | null;
  overview: string | null;
  editorial_note: string | null;
  poster_url: string | null;
  poster_path: string | null;
  tmdb_id: number | null;
  imdb_id: string | null;
  genres: GenreRead[];
  countries: CountryRead[];
  languages: LanguageRead[];
  studios: StudioRead[];
  credits: PersonCreditRead[];
  links: MovieLinkRead[];
  external_ratings: ExternalRatingRead[];
  community_rating: number | null;
  rating_count: number;
  created_at: string;
  updated_at: string;
};

export type UserMovieState = {
  user_id: string;
  movie_id: string;
  rating: number | null;
  watched: boolean;
  favorite: boolean;
  created_at: string;
  updated_at: string;
};

export type Review = {
  id: string;
  movie_id: string;
  user: {
    id: string;
    username: string;
  };
  title: string | null;
  body: string;
  contains_spoilers: boolean;
  rating: number | null;
  created_at: string;
  updated_at: string;
};

export type TmdbSearchItem = {
  tmdb_id: number;
  title: string;
  original_title: string | null;
  release_date: string | null;
  release_year: number | null;
  overview: string | null;
  poster_url: string | null;
};

export type TmdbSearchResponse = {
  page: number;
  total_pages: number;
  total_results: number;
  results: TmdbSearchItem[];
};

export type MovieCreatePayload = {
  title: string;
  original_title?: string | null;
  release_year?: number | null;
  release_date?: string | null;
  runtime_minutes?: number | null;
  overview?: string | null;
  editorial_note?: string | null;
  poster_url?: string | null;
  poster_path?: string | null;
  tmdb_id?: number | null;
  imdb_id?: string | null;
  genre_ids?: string[];
  country_ids?: string[];
  languages?: { language_id: string; is_original: boolean }[];
  studio_ids?: string[];
  person_credits?: {
    person_id: string;
    credit_type: "cast" | "crew";
    job?: string | null;
    character_name?: string | null;
    billing_order?: number | null;
    tmdb_credit_id?: string | null;
  }[];
  links?: {
    source: string;
    url: string;
    label?: string | null;
  }[];
};


export type DeletedMovie = {
  id: string;
  title: string;
  original_title: string | null;
  release_year: number | null;
  poster_url: string | null;
  poster_path: string | null;
  deleted_at: string;
  deleted_by_username: string | null;
};

export type AuditLogItem = {
  id: string;
  actor: {
    id: string;
    username: string;
  } | null;
  action: string;
  entity_type: string;
  entity_id: string;
  before_data: Record<string, unknown> | null;
  after_data: Record<string, unknown> | null;
  created_at: string;
};

export type GenreOption = {
  id: string;
  name: string;
  tmdb_id: number | null;
};

export type CountryOption = {
  id: string;
  name: string;
  iso2: string | null;
  iso3: string | null;
};

export type LanguageOption = {
  id: string;
  name: string;
  iso_code: string;
};

export type StudioOption = {
  id: string;
  name: string;
  tmdb_id: number | null;
};

export type PersonOption = {
  id: string;
  name: string;
  birth_date: string | null;
  death_date: string | null;
  biography: string | null;
  profile_url: string | null;
  profile_path: string | null;
  tmdb_id: number | null;
  imdb_id: string | null;
};

export type EditableCredit = {
  key: string;
  person_id: string;
  person_name: string;
  credit_type: "cast" | "crew";
  job: string;
  character_name: string;
  billing_order: number | null;
  tmdb_credit_id?: string | null;
};
