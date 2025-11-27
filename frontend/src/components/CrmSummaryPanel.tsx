import type { SummaryResponse } from "../api/crmApi";

type ViewMode = "main" | "dashboard" | "clientDetail";

type Props = {
  summary: SummaryResponse;
  effectiveMonth: string | null;
  viewMode: ViewMode;
  totalClients: number;
  totalAssetsValue: number;
  totalFundsValue: number;
  totalSourcesValue: number;
  onShiftMonth: (delta: number) => void;
  onMonthChange: (value: string) => void;
  onToggleDashboard: () => void;
};

function CrmSummaryPanel({
  summary,
  effectiveMonth,
  viewMode,
  totalClients,
  totalAssetsValue,
  totalFundsValue,
  totalSourcesValue,
  onShiftMonth,
  onMonthChange,
  onToggleDashboard,
}: Props) {
  return (
    <section className="crm-panel crm-summary-panel">
      <div className="crm-summary-header">
        <div className="crm-month-controls">
          <button
            type="button"
            className="crm-month-button"
            onClick={() => onShiftMonth(-1)}
          >
            חודש קודם
          </button>
          <div className="crm-month-input-wrapper">
            <div className="crm-summary-label">חודש הצגה</div>
            <input
              type="month"
              className="crm-month-input"
              value={effectiveMonth || ""}
              onChange={(e) => onMonthChange(e.target.value)}
            />
          </div>
          <button
            type="button"
            className="crm-month-button"
            onClick={() => onShiftMonth(1)}
          >
            חודש הבא
          </button>
        </div>
        <button
          type="button"
          className="crm-dashboard-toggle"
          onClick={onToggleDashboard}
        >
          {viewMode === "dashboard" ? "חזרה לרשימת לקוחות" : "דשבורד"}
        </button>
      </div>

      <div className="crm-summary-cards">
        <div className="crm-summary-card crm-summary-card-primary">
          <div className="crm-summary-card-label">סה"כ לקוחות</div>
          <div className="crm-summary-card-value">
            {totalClients.toLocaleString()}
          </div>
        </div>
        <div className="crm-summary-card crm-summary-card-success">
          <div className="crm-summary-card-label">סה"כ נכסים</div>
          <div className="crm-summary-card-value">
            {totalAssetsValue.toLocaleString()}
          </div>
        </div>
        <div className="crm-summary-card crm-summary-card-info">
          <div className="crm-summary-card-label">סה"כ קופות</div>
          <div className="crm-summary-card-value">
            {totalFundsValue.toLocaleString()}
          </div>
        </div>
        <div className="crm-summary-card crm-summary-card-warning">
          <div className="crm-summary-card-label">מקורות נתונים</div>
          <div className="crm-summary-card-value">
            {totalSourcesValue.toLocaleString()}
          </div>
        </div>
      </div>
    </section>
  );
}

export default CrmSummaryPanel;
