import { useEffect, useState } from "react";

import { api } from "../lib/api";
import type {
  CountryOption,
  GenreOption,
  LanguageOption,
  StudioOption,
} from "../types";

export function useCatalog() {
  const [genres, setGenres] = useState<GenreOption[]>([]);
  const [countries, setCountries] = useState<CountryOption[]>([]);
  const [languages, setLanguages] = useState<LanguageOption[]>([]);
  const [studios, setStudios] = useState<StudioOption[]>([]);
  const [loading, setLoading] = useState(true);

  async function reload() {
    setLoading(true);
    try {
      const [g, c, l, s] = await Promise.all([
        api<GenreOption[]>("/catalog/genres"),
        api<CountryOption[]>("/catalog/countries"),
        api<LanguageOption[]>("/catalog/languages"),
        api<StudioOption[]>("/catalog/studios"),
      ]);
      setGenres(g);
      setCountries(c);
      setLanguages(l);
      setStudios(s);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void reload();
  }, []);

  return {
    genres,
    countries,
    languages,
    studios,
    loading,
    reload,
  };
}
