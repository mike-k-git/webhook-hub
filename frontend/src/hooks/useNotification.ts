import { useEffect, useRef, useState } from "react";

export type Notice = { type: "ERROR" | "INFO"; message: string };

export function useNotification() {
  const timerRef = useRef<number | undefined>(undefined);
  const [notification, setNotification] = useState<Notice | null>(null);
  const notify = (notice: Notice) => {
    clearTimeout(timerRef.current);
    setNotification(notice);
    timerRef.current = setTimeout(() => {
      setNotification(null);
    }, 2_000);
  };
  useEffect(() => () => clearTimeout(timerRef.current), []);

  return { notification, notify };
}
