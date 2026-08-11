import { GenerationProvider } from '../context/GenerationContext';
import { ThreeColumnLayout } from '../components/layout';
import { GenerationTabs, ResultCard } from '../components/features/generation';

export function MainApp() {
  return (
    <GenerationProvider>
      <ThreeColumnLayout
        middle={<GenerationTabs />}
        right={<ResultCard />}
      />
    </GenerationProvider>
  );
}
