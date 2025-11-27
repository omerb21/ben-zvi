import type { ChangeEvent } from "react";
import type { ClientSummary } from "../api/crmApi";

type Props = {
  selectedClient: ClientSummary | null;
  isPacketSignLoading: boolean;
  isDeletingClientExports: boolean;
  packetTrimInput: string;
  packetUploadFile: File | null;
  pdfGenerationMessage: string | null;
  pdfGenerationIsError: boolean;
  packetSignLink: string | null;
  packetSignError: string | null;
  packetTrimStatus: string | null;
  packetTrimIsError: boolean;
  packetUploadStatus: string | null;
  packetUploadIsError: boolean;
  clientExportsStatus: string | null;
  clientExportsIsError: boolean;
  onGeneratePacketPdf: () => void;
  onPreviewPacketPdf: () => void;
  onCreatePacketSignLink: () => void;
  onPreviewSignedPacketPdf: () => void;
  onPacketTrimInputChange: (value: string) => void;
  onTrimPacketPages: () => void;
  onPacketUploadFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onUploadPacketPdf: () => void;
  onDeleteClientExports: () => void;
};

function JustificationFormsPanel({
  selectedClient,
  isPacketSignLoading,
  isDeletingClientExports,
  packetTrimInput,
  packetUploadFile,
  pdfGenerationMessage,
  pdfGenerationIsError,
  packetSignLink,
  packetSignError,
  packetTrimStatus,
  packetTrimIsError,
  packetUploadStatus,
  packetUploadIsError,
  clientExportsStatus,
  clientExportsIsError,
  onGeneratePacketPdf,
  onPreviewPacketPdf,
  onCreatePacketSignLink,
  onPreviewSignedPacketPdf,
  onPacketTrimInputChange,
  onTrimPacketPages,
  onPacketUploadFileChange,
  onUploadPacketPdf,
  onDeleteClientExports,
}: Props) {
  return (
    <section className="client-pdf-section">
      <h3 className="panel-subtitle">חבילת טפסי PDF ללקוח</h3>
      <div className="client-pdf-layout">
        <ul className="client-pdf-list">
          <li className="client-pdf-item">
            <div className="client-pdf-item-main">
              <span className="client-pdf-title">חבילת טפסים מאוחדת</span>
              <span className="client-pdf-meta">
                החבילה כוללת: מסמך הנמקה, טופס B1 וכל קיטי ההצטרפות שנוצרו ללקוח
              </span>
            </div>
            <div className="client-pdf-actions">
              <button
                type="button"
                className="client-pdf-button"
                onClick={onGeneratePacketPdf}
              >
                הפקת חבילת טפסים
              </button>
              <button
                type="button"
                className="client-pdf-button"
                onClick={onPreviewPacketPdf}
              >
                תצוגה בעמוד
              </button>
              <button
                type="button"
                className="client-pdf-button"
                onClick={onCreatePacketSignLink}
                disabled={isPacketSignLoading}
              >
                שלח ללקוח לחתימה
              </button>
              <button
                type="button"
                className="client-pdf-button"
                onClick={onPreviewSignedPacketPdf}
              >
                צפייה בחבילה החתומה
              </button>
              <div className="client-pdf-trim">
                <span>מחק עמודים (לפי מספר):</span>
                <input
                  type="text"
                  className="client-pdf-input"
                  value={packetTrimInput}
                  onChange={(event) => onPacketTrimInputChange(event.target.value)}
                  placeholder="לדוגמה: 2 5 7"
                />
                <button
                  type="button"
                  className="client-pdf-button"
                  onClick={onTrimPacketPages}
                >
                  מחק עמודים מהחבילה
                </button>
              </div>
              <div className="client-pdf-upload">
                <span>טעינת חבילה ערוכה (PDF):</span>
                <input
                  type="file"
                  accept="application/pdf"
                  className="client-pdf-input"
                  onChange={onPacketUploadFileChange}
                />
                <button
                  type="button"
                  className="client-pdf-button"
                  onClick={onUploadPacketPdf}
                  disabled={!packetUploadFile}
                >
                  שמירת חבילה ערוכה במערכת
                </button>
              </div>
              <div className="client-pdf-delete">
                <button
                  type="button"
                  className="client-pdf-button client-pdf-button-danger"
                  onClick={onDeleteClientExports}
                  disabled={isDeletingClientExports}
                >
                  מחיקת תיקיית קבצי הלקוח
                </button>
              </div>
            </div>
          </li>
        </ul>
      </div>
      {pdfGenerationMessage && (
        <div className={pdfGenerationIsError ? "status-text status-error" : "status-text"}>
          {pdfGenerationMessage}
        </div>
      )}
      {packetSignLink && (
        <div className="status-text">
          ניתן לשלוח ללקוח את הקישור הבא לחתימה:
          <br />
          <a href={packetSignLink} target="_blank" rel="noreferrer">
            {packetSignLink}
          </a>
        </div>
      )}
      {packetTrimStatus && (
        <div className={packetTrimIsError ? "status-text status-error" : "status-text"}>
          {packetTrimStatus}
        </div>
      )}
      {packetUploadStatus && (
        <div className={packetUploadIsError ? "status-text status-error" : "status-text"}>
          {packetUploadStatus}
        </div>
      )}
      {clientExportsStatus && (
        <div className={clientExportsIsError ? "status-text status-error" : "status-text"}>
          {clientExportsStatus}
        </div>
      )}
      {packetSignError && (
        <div className="status-text status-error">{packetSignError}</div>
      )}
    </section>
  );
}

export default JustificationFormsPanel;
