import { useState, type ChangeEvent, type FormEvent } from "react";
import {
  resetClientCredentials,
  updateClientToken,
  updateClientPin,
  disableClientAccess,
  type ClientCredentialsResetResult,
} from "../api/clientAccessApi";

const BZCLIENT_BASE_URL =
  import.meta.env.VITE_BZCLIENT_BASE_URL || "https://bzclient.onrender.com";

function CrmClientAccessPanel() {
  const [clientIdInput, setClientIdInput] = useState("");
  const [currentClient, setCurrentClient] = useState<ClientCredentialsResetResult | null>(
    null
  );
  const [manualToken, setManualToken] = useState("");
  const [manualPin, setManualPin] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  function buildClientUrl(): string | null {
    if (!currentClient?.clientToken) {
      return null;
    }
    const trimmedToken = currentClient.clientToken.trim();
    if (!trimmedToken) {
      return null;
    }
    const base = BZCLIENT_BASE_URL.replace(/\/$/, "");
    return `${base}/?token=${encodeURIComponent(trimmedToken)}`;
  }

  function parseClientId(): number | null {
    const trimmed = clientIdInput.trim();
    if (!trimmed) {
      setErrorMessage("יש להזין מספר לקוח");
      return null;
    }
    const value = Number.parseInt(trimmed, 10);
    if (Number.isNaN(value) || value <= 0) {
      setErrorMessage("מספר לקוח חייב להיות מספר גדול מ-0");
      return null;
    }
    return value;
  }

  function handleClientIdChange(event: ChangeEvent<HTMLInputElement>) {
    const onlyDigits = event.target.value.replace(/[^0-9]/g, "");
    setClientIdInput(onlyDigits);
  }

  async function handleResetCredentials(event: FormEvent) {
    event.preventDefault();
    setStatusMessage(null);
    setErrorMessage(null);

    const clientId = parseClientId();
    if (!clientId) {
      return;
    }

    setIsLoading(true);
    try {
      const result = await resetClientCredentials(clientId);
      setCurrentClient(result);
      setManualToken(result.clientToken || "");
      setManualPin(result.clientPin || "");
      setStatusMessage("נוצרו token + PIN חדשים ללקוח");
    } catch (error: any) {
      if (error?.response?.status === 404) {
        setErrorMessage("לקוח לא נמצא, בדוק את מספר הלקוח");
      } else {
        const detail = error?.response?.data?.detail || error?.message;
        setErrorMessage(detail || "שגיאה ביצירת token + PIN חדשים");
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function handleUpdateToken() {
    setStatusMessage(null);
    setErrorMessage(null);

    const clientId = parseClientId();
    if (!clientId) {
      return;
    }

    const trimmedToken = manualToken.trim();
    if (!trimmedToken) {
      setErrorMessage("לא ניתן לעדכן token ריק");
      return;
    }

    setIsLoading(true);
    try {
      const result = await updateClientToken(clientId, trimmedToken);
      setCurrentClient((prev) =>
        prev
          ? { ...prev, clientId: result.clientId, clientToken: result.clientToken || "" }
          : { clientId: result.clientId, clientToken: result.clientToken || "", clientPin: "" }
      );
      setStatusMessage("token עודכן בהצלחה");
    } catch (error: any) {
      if (error?.response?.status === 404) {
        setErrorMessage("לקוח לא נמצא, בדוק את מספר הלקוח");
      } else {
        const detail = error?.response?.data?.detail || error?.message;
        setErrorMessage(detail || "שגיאה בעדכון token");
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function handleUpdatePin() {
    setStatusMessage(null);
    setErrorMessage(null);

    const clientId = parseClientId();
    if (!clientId) {
      return;
    }

    const trimmedPin = manualPin.trim();
    if (!/^[0-9]{6}$/.test(trimmedPin)) {
      setErrorMessage("קוד PIN חייב להיות בן 6 ספרות (0-9)");
      return;
    }

    setIsLoading(true);
    try {
      await updateClientPin(clientId, trimmedPin);
      setCurrentClient((prev) =>
        prev
          ? { ...prev, clientPin: trimmedPin }
          : { clientId, clientToken: "", clientPin: trimmedPin }
      );
      setStatusMessage("קוד הגישה עודכן בהצלחה");
    } catch (error: any) {
      if (error?.response?.status === 404) {
        setErrorMessage("לקוח לא נמצא, בדוק את מספר הלקוח");
      } else if (error?.response?.status === 422) {
        setErrorMessage("קוד PIN לא תקין. ודא שהוא בן 6 ספרות");
      } else {
        const detail = error?.response?.data?.detail || error?.message;
        setErrorMessage(detail || "שגיאה בעדכון קוד הגישה");
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDisableAccess() {
    setStatusMessage(null);
    setErrorMessage(null);

    const clientId = parseClientId();
    if (!clientId) {
      return;
    }

    setIsLoading(true);
    try {
      await disableClientAccess(clientId);
      setCurrentClient((prev) =>
        prev
          ? { ...prev, clientToken: "", clientPin: "" }
          : { clientId, clientToken: "", clientPin: "" }
      );
      setManualToken("");
      setManualPin("");
      setStatusMessage("הגישה ללקוח בוטלה (token + PIN נוקו)");
    } catch (error: any) {
      if (error?.response?.status === 404) {
        setErrorMessage("לקוח לא נמצא, בדוק את מספר הלקוח");
      } else {
        const detail = error?.response?.data?.detail || error?.message;
        setErrorMessage(detail || "שגיאה בביטול הגישה ללקוח");
      }
    } finally {
      setIsLoading(false);
    }
  }

  const clientLink = buildClientUrl();

  return (
    <section className="crm-panel crm-client-access-panel">
      <h2 className="panel-title">ניהול גישת לקוח לאפליקציית לקוחות</h2>

      <form className="crm-client-access-form" onSubmit={handleResetCredentials}>
        <div className="crm-client-access-row">
          <div className="crm-client-access-field">
            <label className="crm-client-access-label" htmlFor="client-id-input">
              מספר לקוח
            </label>
            <input
              id="client-id-input"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              className="crm-client-access-input"
              value={clientIdInput}
              onChange={handleClientIdChange}
              disabled={isLoading}
            />
          </div>
        </div>

        <div className="crm-client-access-sections">
          <div className="crm-client-access-section">
            <h3 className="crm-client-access-section-title">יצירת token + PIN חדשים</h3>
            <p className="crm-client-access-help">
              פעולה זו יוצרת ללקוח token וקוד PIN חדשים ומחליפה ערכים קודמים.
            </p>
            <button
              type="submit"
              className="crm-client-access-button primary"
              disabled={isLoading}
            >
              {isLoading ? "מבצע פעולה..." : "צור token + PIN חדשים"}
            </button>
          </div>

          <div className="crm-client-access-section">
            <h3 className="crm-client-access-section-title">עדכון token ידני</h3>
            <div className="crm-client-access-field">
              <label className="crm-client-access-label" htmlFor="manual-token-input">
                token נוכחי
              </label>
              <input
                id="manual-token-input"
                type="text"
                className="crm-client-access-input"
                value={manualToken}
                onChange={(event) => setManualToken(event.target.value)}
                disabled={isLoading}
              />
            </div>
            <button
              type="button"
              className="crm-client-access-button"
              onClick={handleUpdateToken}
              disabled={isLoading}
            >
              עדכן token
            </button>
          </div>

          <div className="crm-client-access-section">
            <h3 className="crm-client-access-section-title">עדכון PIN ידני</h3>
            <div className="crm-client-access-field">
              <label className="crm-client-access-label" htmlFor="manual-pin-input">
                קוד גישה (PIN) בן 6 ספרות
              </label>
              <input
                id="manual-pin-input"
                type="password"
                className="crm-client-access-input"
                value={manualPin}
                onChange={(event) => setManualPin(event.target.value)}
                disabled={isLoading}
              />
              <div className="crm-client-access-hint">הקוד חייב להכיל בדיוק 6 ספרות (0–9).</div>
            </div>
            <button
              type="button"
              className="crm-client-access-button"
              onClick={handleUpdatePin}
              disabled={isLoading}
            >
              עדכן קוד גישה
            </button>
          </div>

          <div className="crm-client-access-section danger">
            <h3 className="crm-client-access-section-title">ביטול גישה ללקוח</h3>
            <p className="crm-client-access-help">
              פעולה זו מנקה את ה-token וה-PIN של הלקוח. לאחר מכן הלקוח לא יוכל להתחבר
              יותר באמצעות קישור או קוד גישה קיימים.
            </p>
            <button
              type="button"
              className="crm-client-access-button danger"
              onClick={handleDisableAccess}
              disabled={isLoading}
            >
              בטל גישה ללקוח
            </button>
          </div>
        </div>
      </form>

      <div className="crm-client-access-status-area">
        {statusMessage && (
          <div className="crm-client-access-status success">{statusMessage}</div>
        )}
        {errorMessage && (
          <div className="crm-client-access-status error">{errorMessage}</div>
        )}

        {currentClient && (
          <div className="crm-client-access-result">
            <div className="crm-client-access-result-row">
              <span className="crm-client-access-result-label">מספר לקוח:</span>
              <span>{currentClient.clientId}</span>
            </div>
            <div className="crm-client-access-result-row">
              <span className="crm-client-access-result-label">token נוכחי:</span>
              <span>{currentClient.clientToken || ""}</span>
            </div>
            <div className="crm-client-access-result-row">
              <span className="crm-client-access-result-label">PIN נוכחי:</span>
              <span>{currentClient.clientPin || ""}</span>
            </div>
            {clientLink && (
              <div className="crm-client-access-result-row">
                <span className="crm-client-access-result-label">קישור ללקוח:</span>
                <a
                  href={clientLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="crm-client-access-link"
                >
                  {clientLink}
                </a>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

export default CrmClientAccessPanel;
