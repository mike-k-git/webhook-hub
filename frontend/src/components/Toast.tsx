import type { Notice } from "../hooks/useNotification";

export function Toast({ notification }: { notification: Notice | null }) {
  if (!notification) return null;
  return (
    <div>
      {notification.type} {notification.message}
    </div>
  );
}
