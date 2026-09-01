type Option = {
  id: string;
  name: string;
};

type Props = {
  label: string;
  options: Option[];
  value: string[];
  onChange: (value: string[]) => void;
  help?: string;
};

export function ReferenceMultiSelect({
  label,
  options,
  value,
  onChange,
  help,
}: Props) {
  return (
    <label className="field">
      <span>{label}</span>
      <select
        className="multi-select"
        multiple
        value={value}
        onChange={(event) =>
          onChange(
            Array.from(event.currentTarget.selectedOptions).map(
              (option) => option.value,
            ),
          )
        }
      >
        {options.map((option) => (
          <option value={option.id} key={option.id}>
            {option.name}
          </option>
        ))}
      </select>
      {help && <small className="field-help">{help}</small>}
    </label>
  );
}
