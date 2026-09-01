import type { LanguageOption } from "../../types";

type Value = {
  language_id: string;
  is_original: boolean;
};

type Props = {
  options: LanguageOption[];
  value: Value[];
  onChange: (value: Value[]) => void;
};

export function LanguageSelector({ options, value, onChange }: Props) {
  const selected = new Map(value.map((item) => [item.language_id, item]));

  function toggle(id: string, enabled: boolean) {
    if (enabled) {
      onChange([...value, { language_id: id, is_original: false }]);
    } else {
      onChange(value.filter((item) => item.language_id !== id));
    }
  }

  function setOriginal(id: string, original: boolean) {
    onChange(
      value.map((item) =>
        item.language_id === id
          ? { ...item, is_original: original }
          : item,
      ),
    );
  }

  return (
    <div className="field">
      <span>Languages</span>
      <div className="language-selector">
        {options.map((language) => {
          const item = selected.get(language.id);
          return (
            <div className="language-row" key={language.id}>
              <label className="toggle-row">
                <input
                  type="checkbox"
                  checked={Boolean(item)}
                  onChange={(event) => toggle(language.id, event.target.checked)}
                />
                <span>
                  {language.name} <small>({language.iso_code})</small>
                </span>
              </label>

              {item && (
                <label className="toggle-row language-original">
                  <input
                    type="checkbox"
                    checked={item.is_original}
                    onChange={(event) =>
                      setOriginal(language.id, event.target.checked)
                    }
                  />
                  <span>original</span>
                </label>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
