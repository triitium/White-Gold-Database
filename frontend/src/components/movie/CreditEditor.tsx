import { useState } from "react";

import { api, ApiError } from "../../lib/api";
import type { EditableCredit, PersonOption } from "../../types";

export function CreditEditor({
  value,
  onChange,
}: {
  value: EditableCredit[];
  onChange: (value: EditableCredit[]) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PersonOption[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    const needle = query.trim();
    if (!needle) return;
    setSearching(true);
    setError(null);
    try {
      const people = await api<PersonOption[]>(
        `/catalog/people?q=${encodeURIComponent(needle)}`,
      );
      setResults(people);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "People search failed");
    } finally {
      setSearching(false);
    }
  }

  async function createPerson() {
    const name = query.trim();
    if (!name) return;
    setError(null);
    try {
      const person = await api<PersonOption>("/catalog/people", {
        method: "POST",
        csrf: true,
        body: JSON.stringify({ name }),
      });
      setResults((current) => [person, ...current]);
      addPerson(person);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not create person");
    }
  }

  function addPerson(person: PersonOption) {
    onChange([
      ...value,
      {
        key: crypto.randomUUID(),
        person_id: person.id,
        person_name: person.name,
        credit_type: "cast",
        job: "",
        character_name: "",
        billing_order: null,
      },
    ]);
    setQuery("");
    setResults([]);
  }

  function patch(key: string, changes: Partial<EditableCredit>) {
    onChange(
      value.map((credit) =>
        credit.key === key ? { ...credit, ...changes } : credit,
      ),
    );
  }

  return (
    <div className="field field--span-4">
      <span>Cast & crew</span>

      <div className="people-search-row">
        <input
          value={query}
          placeholder="Search or create person"
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              void search();
            }
          }}
        />
        <button
          type="button"
          className="button button--ghost"
          disabled={searching || !query.trim()}
          onClick={() => void search()}
        >
          {searching ? "Searching…" : "Search"}
        </button>
        <button
          type="button"
          className="button button--ghost"
          disabled={!query.trim()}
          onClick={() => void createPerson()}
        >
          Create person
        </button>
      </div>

      {error && <div className="alert alert--error">{error}</div>}

      {results.length > 0 && (
        <div className="person-results">
          {results.map((person) => (
            <button
              type="button"
              key={person.id}
              onClick={() => addPerson(person)}
            >
              <strong>{person.name}</strong>
              <span>
                {person.birth_date?.slice(0, 4) ?? "?"}
                {person.tmdb_id ? ` · TMDB ${person.tmdb_id}` : ""}
              </span>
            </button>
          ))}
        </div>
      )}

      <div className="credit-editor-list">
        {value.map((credit, index) => (
          <div className="credit-editor-row" key={credit.key}>
            <strong>{credit.person_name}</strong>

            <select
              value={credit.credit_type}
              onChange={(event) =>
                patch(credit.key, {
                  credit_type: event.target.value as "cast" | "crew",
                })
              }
            >
              <option value="cast">Cast</option>
              <option value="crew">Crew</option>
            </select>

            {credit.credit_type === "crew" ? (
              <input
                placeholder="Job, e.g. Director"
                value={credit.job}
                onChange={(event) =>
                  patch(credit.key, { job: event.target.value })
                }
              />
            ) : (
              <input
                placeholder="Character"
                value={credit.character_name}
                onChange={(event) =>
                  patch(credit.key, { character_name: event.target.value })
                }
              />
            )}

            <input
              className="credit-order"
              type="number"
              min="0"
              placeholder="#"
              value={credit.billing_order ?? ""}
              onChange={(event) =>
                patch(credit.key, {
                  billing_order:
                    event.target.value === ""
                      ? null
                      : Number(event.target.value),
                })
              }
            />

            <button
              type="button"
              className="text-button text-button--danger"
              onClick={() =>
                onChange(value.filter((item) => item.key !== credit.key))
              }
            >
              Remove
            </button>

            {credit.credit_type === "cast" &&
              credit.billing_order == null && (
                <button
                  type="button"
                  className="text-button"
                  onClick={() => patch(credit.key, { billing_order: index })}
                >
                  Set order {index}
                </button>
              )}
          </div>
        ))}
      </div>
    </div>
  );
}
