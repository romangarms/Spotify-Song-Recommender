interface GuideStepProps {
  number: number;
  title: string;
  description: string;
}

export function GuideStep({ number, title, description }: GuideStepProps) {
  return (
    <li className="flex gap-4">
      <span className="flex-shrink-0 w-8 h-8 rounded-full bg-spotify-green text-black font-bold flex items-center justify-center">
        {number}
      </span>
      <div>
        <p className="text-white font-medium">{title}</p>
        <p className="text-spotify-text text-sm">{description}</p>
      </div>
    </li>
  );
}
