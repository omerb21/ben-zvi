import { useMemo, useState } from "react";
import MainLayout from "./layout/MainLayout";
import CrmPage from "./pages/crm/CrmPageRoot.tsx";
import JustificationPage from "./pages/justification/JustificationPageRoot";

export type AppView = "crm" | "justification";

const REQUIRED_PASSWORD = "benzvi5090";

type LoginProps = {
  onSuccess: () => void;
};

function LoginGate({ onSuccess }: LoginProps) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 420,
          background: "#ffffff",
          borderRadius: 12,
          padding: 24,
          boxShadow: "0 10px 30px rgba(0,0,0,0.12)",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 16 }}>כניסה למערכת</h2>
        <label style={{ display: "block", marginBottom: 8 }}>סיסמה</label>
        <input
          type="password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            setError(null);
          }}
          style={{
            width: "100%",
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid #d1d5db",
            fontSize: 16,
          }}
        />
        {error ? (
          <div style={{ marginTop: 10, color: "#b91c1c" }}>{error}</div>
        ) : null}
        <button
          type="button"
          onClick={() => {
            if (password !== REQUIRED_PASSWORD) {
              setError("סיסמה שגויה");
              return;
            }
            localStorage.setItem("app_password", password);
            onSuccess();
          }}
          style={{
            marginTop: 16,
            width: "100%",
            padding: "10px 12px",
            borderRadius: 8,
            border: 0,
            background: "#111827",
            color: "white",
            fontSize: 16,
            cursor: "pointer",
          }}
        >
          כניסה
        </button>
      </div>
    </div>
  );
}

function App() {
  const initialAuth = useMemo(() => {
    return localStorage.getItem("app_password") === REQUIRED_PASSWORD;
  }, []);

  const [isAuthed, setIsAuthed] = useState<boolean>(initialAuth);
  const [view, setView] = useState<AppView>("crm");
  const [savingProductsReloadKey, setSavingProductsReloadKey] = useState(0);
  const [justificationInitialClientId, setJustificationInitialClientId] =
    useState<number | null>(null);

  if (!isAuthed) {
    return <LoginGate onSuccess={() => setIsAuthed(true)} />;
  }

  return (
    <MainLayout currentView={view} onChangeView={setView}>
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
