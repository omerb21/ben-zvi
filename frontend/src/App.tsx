import { useState } from "react";
import MainLayout from "./layout/MainLayout";
import CrmPage from "./pages/CrmPage";
import JustificationPage from "./pages/JustificationPage";

export type AppView = "crm" | "justification";

function App() {
  const [view, setView] = useState<AppView>("crm");
  const [savingProductsReloadKey, setSavingProductsReloadKey] = useState(0);
  const [justificationInitialClientId, setJustificationInitialClientId] =
    useState<number | null>(null);

  return (
    <MainLayout
      currentView={view}
      onChangeView={setView}
    >
      {view === "crm" ? (
        <CrmPage
          onOpenJustification={(clientId: number) => {
            setJustificationInitialClientId(clientId);
            setView("justification");
          }}
        />
      ) : (
        <JustificationPage
          savingProductsReloadKey={savingProductsReloadKey}
          initialClientId={justificationInitialClientId}
          onGemelNetImportCompleted={() =>
            setSavingProductsReloadKey((prev) => prev + 1)
          }
        />
      )}
    </MainLayout>
  );
}

export default App;
