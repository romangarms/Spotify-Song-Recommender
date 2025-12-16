interface Tab {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
}

export function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="flex bg-spotify-light-gray rounded-full p-1">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`flex-1 py-2 px-4 rounded-full text-sm font-medium transition-colors ${
            activeTab === tab.id
              ? 'bg-spotify-green text-white'
              : 'text-spotify-text hover:text-white'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
