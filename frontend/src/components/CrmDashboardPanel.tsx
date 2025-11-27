import type { ChangeEvent, CSSProperties } from "react";
import type { SummaryResponse, MonthlyChangePoint } from "../api/crmApi";

type Props = {
  summary: SummaryResponse;
  crmAdminMessage: string | null;
  crmAdminError: string | null;
  crmImportMonth: string;
  crmImportFiles: File[];
  isCrmImporting: boolean;
  isCrmClearing: boolean;
  monthlyTrendPath: string;
  monthlyTrendPoints: { x: number; y: number }[];
  monthlyChange: MonthlyChangePoint[];
  onCrmMonthChange: (value: string) => void;
  onCrmFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onRunCrmImport: () => void;
  onClearCrmDataLocal: () => void;
};

function CrmDashboardPanel({
  summary,
  crmAdminMessage,
  crmAdminError,
  crmImportMonth,
  crmImportFiles,
  isCrmImporting,
  isCrmClearing,
  monthlyTrendPath,
  monthlyTrendPoints,
  monthlyChange,
  onCrmMonthChange,
  onCrmFileChange,
  onRunCrmImport,
  onClearCrmDataLocal,
}: Props) {
  return (
    <section className="crm-panel crm-dashboard-panel">
      <h2 className="panel-title">דשבורד תיק לקוחות</h2>
      {crmAdminMessage && <div className="admin-import-status">{crmAdminMessage}</div>}
      {crmAdminError && (
        <div className="admin-import-status admin-import-status-error">{crmAdminError}</div>
      )}
      <div className="crm-dashboard-grid">
        <div className="crm-dashboard-card crm-dashboard-import-card">
          <div className="crm-dashboard-card-header">
            <div className="crm-dashboard-card-title">ניהול קבצי CRM (Excel)</div>
          </div>
          <div className="crm-dashboard-card-body">
            <div className="admin-import-group crm-admin-import-group">
              <input
                type="month"
                className="admin-import-month"
                value={crmImportMonth}
                onChange={(event) => onCrmMonthChange(event.target.value)}
              />
              <input
                type="file"
                accept=".xls,.xlsx"
                multiple
                className="admin-import-file"
                onChange={onCrmFileChange}
              />
              <button
                type="button"
                className="admin-import-button"
                onClick={onRunCrmImport}
                disabled={
                  crmImportFiles.length === 0 ||
                  !crmImportMonth ||
                  isCrmImporting ||
                  isCrmClearing
                }
              >
                ייבוא CRM (Excel)
              </button>
              <button
                type="button"
                className="admin-import-button"
                onClick={onClearCrmDataLocal}
                disabled={isCrmImporting || isCrmClearing}
              >
                מחיקת נתוני CRM
              </button>
            </div>
          </div>
        </div>

        <div className="crm-dashboard-card">
          <div className="crm-dashboard-card-header">
            <div className="crm-dashboard-card-title">התפלגות לפי מקור</div>
          </div>
          <div className="crm-dashboard-card-body">
            {summary && Object.keys(summary.bySource || {}).length > 0 ? (
              Object.entries(summary.bySource || {}).map(([key, value]) => {
                const total = Object.values(summary.bySource || {}).reduce(
                  (acc, v) => acc + (v || 0),
                  0
                );
                const ratio = total > 0 ? (value || 0) / total : 0;
                const percent = Math.round(ratio * 100);
                return (
                  <div key={key || "unknown"} className="crm-dashboard-bar-row">
                    <div className="crm-dashboard-bar-label">{key || "לא זמין"}</div>
                    <div className="crm-dashboard-bar-value">
                      {value?.toLocaleString() || "0"} ₪ ({percent}%)
                    </div>
                    <div className="crm-dashboard-bar-track">
                      <div
                        className="crm-dashboard-bar-fill"
                        style={{
                          "--crm-bar-width": `${Math.max(5, percent)}%`,
                        } as CSSProperties}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="crm-dashboard-empty">אין נתונים להצגה</div>
            )}
          </div>
        </div>

        <div className="crm-dashboard-card">
          <div className="crm-dashboard-card-header">
            <div className="crm-dashboard-card-title">התפלגות לפי סוג מוצר</div>
          </div>
          <div className="crm-dashboard-card-body">
            {summary && Object.keys(summary.byFundType || {}).length > 0 ? (
              Object.entries(summary.byFundType || {}).map(([key, value]) => {
                const total = Object.values(summary.byFundType || {}).reduce(
                  (acc, v) => acc + (v || 0),
                  0
                );
                const ratio = total > 0 ? (value || 0) / total : 0;
                const percent = Math.round(ratio * 100);
                return (
                  <div key={key || "unknown"} className="crm-dashboard-bar-row">
                    <div className="crm-dashboard-bar-label">{key || "לא זמין"}</div>
                    <div className="crm-dashboard-bar-value">
                      {value?.toLocaleString() || "0"} ₪ ({percent}%)
                    </div>
                    <div className="crm-dashboard-bar-track">
                      <div
                        className="crm-dashboard-bar-fill crm-dashboard-bar-fill-type"
                        style={{
                          "--crm-bar-width": `${Math.max(5, percent)}%`,
                        } as CSSProperties}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="crm-dashboard-empty">אין נתונים להצגה</div>
            )}
          </div>
        </div>

        <div className="crm-dashboard-card">
          <div className="crm-dashboard-card-header">
            <div className="crm-dashboard-card-title">מגמת נכסים חודשית</div>
          </div>
          <div className="crm-dashboard-card-body">
            {monthlyTrendPoints.length >= 2 ? (
              <div className="crm-dashboard-trend">
                <svg
                  viewBox="0 0 100 100"
                  className="crm-dashboard-trend-svg"
                  preserveAspectRatio="none"
                >
                  <path d={monthlyTrendPath} className="crm-dashboard-trend-line" />
                  {monthlyTrendPoints.map((point, index) => (
                    <circle
                      key={`${point.x}-${point.y}-${index}`}
                      cx={point.x}
                      cy={point.y}
                      r={1.7}
                      className="crm-dashboard-trend-point"
                    />
                  ))}
                </svg>
                <ul className="crm-dashboard-trend-list">
                  {monthlyChange.map((item) => (
                    <li key={item.month}>
                      <span>{item.month}</span>
                      <span>{item.total.toLocaleString()} ₪</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="crm-dashboard-empty">אין מספיק היסטוריה להצגת גרף</div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

export default CrmDashboardPanel;
