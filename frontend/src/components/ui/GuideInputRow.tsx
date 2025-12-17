import { Input } from './Input';

interface GuideInputRowProps {
  value: string;
  onChange: (value: string) => void;
  onPaste: () => void;
  placeholder: string;
}

export function GuideInputRow({ value, onChange, onPaste, placeholder }: GuideInputRowProps) {
  return (
    <div className="flex gap-2 items-stretch">
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="text-lg flex-1"
      />
      <button
        type="button"
        onClick={onPaste}
        className="px-4 bg-spotify-light-gray text-white border border-gray-600 hover:border-spotify-green rounded-lg transition-colors"
        title="Paste from clipboard"
      >
        Paste
      </button>
    </div>
  );
}
