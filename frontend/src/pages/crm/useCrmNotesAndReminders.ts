import { useEffect, useState, type FormEvent, type Dispatch, type SetStateAction } from "react";
import type { ClientSummary, ClientNote, Reminder } from "../../api/crmApi";
import { fetchReminders } from "../../api/crmApi";
import {
  dismissNoteAction,
  clearNoteReminderAction,
  deleteNoteAction,
  submitNoteAction,
  dismissReminderAction,
  clearReminderGlobalAction,
} from "./crmNotesAndReminders";

export type UseCrmNotesAndRemindersArgs = {
  selectedClient: ClientSummary | null;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function useCrmNotesAndReminders({
  selectedClient,
  setError,
}: UseCrmNotesAndRemindersArgs) {
  const [notes, setNotes] = useState<ClientNote[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [newNoteText, setNewNoteText] = useState("");
  const [newNoteReminder, setNewNoteReminder] = useState("");

  useEffect(() => {
    let active = true;
    const refreshReminders = async () => {
      try {
        const nextReminders = await fetchReminders();
        if (active) {
          setReminders(nextReminders);
        }
      } catch {
        // Background refresh failures should not interrupt CRM work.
      }
    };

    const intervalId = window.setInterval(() => {
      void refreshReminders();
    }, 15000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, []);

  const handleDismissNote = (noteId: number) => {
    dismissNoteAction({
      selectedClient,
      noteId,
      setNotes,
      setError,
    });
  };

  const handleClearNoteReminder = (noteId: number) => {
    clearNoteReminderAction({
      selectedClient,
      noteId,
      setNotes,
      setError,
    });
  };

  const handleDeleteNote = (noteId: number) => {
    deleteNoteAction({
      selectedClient,
      noteId,
      setNotes,
      setError,
    });
  };

  const handleSubmitNote = (event: FormEvent) => {
    event.preventDefault();
    submitNoteAction({
      selectedClient,
      newNoteText,
      newNoteReminder,
      setNotes,
      setNewNoteText,
      setNewNoteReminder,
      setError,
    });
  };

  const handleDismissReminder = (reminder: Reminder) => {
    dismissReminderAction({
      reminder,
      setReminders,
      setError,
    });
  };

  const handleClearReminderFromGlobal = (reminder: Reminder) => {
    clearReminderGlobalAction({
      reminder,
      setReminders,
      setError,
    });
  };

  return {
    notes,
    reminders,
    newNoteText,
    newNoteReminder,
    setNotes,
    setReminders,
    setNewNoteText,
    setNewNoteReminder,
    handleDismissNote,
    handleClearNoteReminder,
    handleDeleteNote,
    handleSubmitNote,
    handleDismissReminder,
    handleClearReminderFromGlobal,
  };
}
