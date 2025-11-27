import type { Reminder } from "../api/crmApi";

type Props = {
  reminders: Reminder[];
  onGoToClient: (reminder: Reminder) => void;
  onDismissReminder: (reminder: Reminder) => void;
  onClearReminder: (reminder: Reminder) => void;
};

function CrmRemindersPanel({
  reminders,
  onGoToClient,
  onDismissReminder,
  onClearReminder,
}: Props) {
  if (reminders.length === 0) {
    return null;
  }

  return (
    <section className="crm-panel crm-reminders-panel">
      <h3 className="panel-subtitle">תזכורות פתוחות</h3>
      <ul className="crm-reminders-list">
        {reminders.map((reminder) => (
          <li key={reminder.id} className="crm-reminder-item">
            <div
              className="crm-reminder-text"
              onClick={() => onGoToClient(reminder)}
            >
              {reminder.note}
            </div>
            <div className="crm-reminder-meta">
              <span>{reminder.clientName}</span>
              {reminder.reminderAt && <span>עד {reminder.reminderAt}</span>}
            </div>
            <div className="crm-reminder-actions">
              <button
                type="button"
                className="crm-reminder-action-button"
                onClick={() => onGoToClient(reminder)}
              >
                מעבר ללקוח
              </button>
              <button
                type="button"
                className="crm-reminder-action-button"
                onClick={() => onDismissReminder(reminder)}
              >
                סגירה
              </button>
              <button
                type="button"
                className="crm-reminder-action-button crm-reminder-action-secondary"
                onClick={() => onClearReminder(reminder)}
              >
                איפוס
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default CrmRemindersPanel;
