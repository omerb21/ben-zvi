import type { ClientSummary, ClientNote, Reminder } from "../../api/crmApi";
import {
  dismissClientNote,
  clearNoteReminder,
  deleteClientNote,
  createClientNote,
} from "../../api/crmApi";
import type { Dispatch, SetStateAction } from "react";

export type DismissNoteArgs = {
  selectedClient: ClientSummary | null;
  noteId: number;
  setNotes: Dispatch<SetStateAction<ClientNote[]>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function dismissNoteAction({
  selectedClient,
  noteId,
  setNotes,
  setError,
}: DismissNoteArgs) {
  if (!selectedClient) {
    return;
  }

  dismissClientNote(selectedClient.id, noteId)
    .then((updated) => {
      setNotes((prev) =>
        prev.map((note) => (note.id === updated.id ? updated : note))
      );
      setError(null);
    })
    .catch(() => {
      setError("שגיאה בסגירת תזכורת");
    });
}

export type ClearNoteReminderArgs = {
  selectedClient: ClientSummary | null;
  noteId: number;
  setNotes: Dispatch<SetStateAction<ClientNote[]>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function clearNoteReminderAction({
  selectedClient,
  noteId,
  setNotes,
  setError,
}: ClearNoteReminderArgs) {
  if (!selectedClient) {
    return;
  }

  clearNoteReminder(selectedClient.id, noteId)
    .then((updated) => {
      setNotes((prev) =>
        prev.map((note) => (note.id === updated.id ? updated : note))
      );
      setError(null);
    })
    .catch(() => {
      setError("שגיאה באיפוס תזכורת");
    });
}

export type DeleteNoteArgs = {
  selectedClient: ClientSummary | null;
  noteId: number;
  setNotes: Dispatch<SetStateAction<ClientNote[]>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function deleteNoteAction({
  selectedClient,
  noteId,
  setNotes,
  setError,
}: DeleteNoteArgs) {
  if (!selectedClient) {
    return;
  }

  deleteClientNote(selectedClient.id, noteId)
    .then(() => {
      setNotes((prev) => prev.filter((note) => note.id !== noteId));
      setError(null);
    })
    .catch(() => {
      setError("שגיאה במחיקת הערה");
    });
}

export type SubmitNoteArgs = {
  selectedClient: ClientSummary | null;
  newNoteText: string;
  newNoteReminder: string;
  setNotes: Dispatch<SetStateAction<ClientNote[]>>;
  setNewNoteText: Dispatch<SetStateAction<string>>;
  setNewNoteReminder: Dispatch<SetStateAction<string>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function submitNoteAction({
  selectedClient,
  newNoteText,
  newNoteReminder,
  setNotes,
  setNewNoteText,
  setNewNoteReminder,
  setError,
}: SubmitNoteArgs) {
  if (!selectedClient || !newNoteText.trim()) {
    return;
  }

  createClientNote(selectedClient.id, {
    note: newNoteText.trim(),
    reminderAt: newNoteReminder || undefined,
  })
    .then((created) => {
      setNotes((prev) => [created, ...prev]);
      setNewNoteText("");
      setNewNoteReminder("");
    })
    .catch(() => {
      setError("שגיאה ביצירת הערה חדשה");
    });
}

export type DismissReminderArgs = {
  reminder: Reminder;
  setReminders: Dispatch<SetStateAction<Reminder[]>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function dismissReminderAction({
  reminder,
  setReminders,
  setError,
}: DismissReminderArgs) {
  dismissClientNote(reminder.clientId, reminder.id)
    .then(() => {
      setReminders((prev) => prev.filter((r) => r.id !== reminder.id));
      setError(null);
    })
    .catch(() => {
      setError("שגיאה בסגירת תזכורת");
    });
}

export type ClearReminderGlobalArgs = {
  reminder: Reminder;
  setReminders: Dispatch<SetStateAction<Reminder[]>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function clearReminderGlobalAction({
  reminder,
  setReminders,
  setError,
}: ClearReminderGlobalArgs) {
  clearNoteReminder(reminder.clientId, reminder.id)
    .then(() => {
      setReminders((prev) => prev.filter((r) => r.id !== reminder.id));
      setError(null);
    })
    .catch(() => {
      setError("שגיאה באיפוס תזכורת");
    });
}
