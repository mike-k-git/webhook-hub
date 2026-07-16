import { createFileRoute } from "@tanstack/react-router";
import { useInbox, useReplay } from "../api/inbox";
import { useEffect, useMemo, useRef, useState } from "react";
import { useDestinations } from "../api/config";
import { Badge } from "../components/badge";
import { useQueryClient } from "@tanstack/react-query";
import { ApiError } from "../api/errors";

export const Route = createFileRoute("/inbox")({
  component: Inbox,
});

function Inbox() {
  const { isPending, isError, data } = useInbox();
  const { data: destinations } = useDestinations();
  const dstById = useMemo(
    () => new Map((destinations ?? []).map((d) => [d.id, d])),
    [destinations],
  );
  const timerRef = useRef<number | undefined>(undefined);

  const replay = useReplay();
  const qc = useQueryClient();
  const [notification, setNotification] = useState({ type: "", message: "" });
  const handleNotification = (type: string, message: string) => {
    clearTimeout(timerRef.current);
    setNotification({ type, message });
    timerRef.current = setTimeout(() => {
      setNotification({ type: "", message: "" });
    }, 2_000);
  };
  useEffect(() => () => clearTimeout(timerRef.current), []);

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  if (data.length === 0) return <h1>No dead-lettered deliveries</h1>;
  return (
    <div>
      {notification.type && (
        <div>
          {notification.type} {notification.message}
        </div>
      )}
      <ol className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {data.map((item) => {
          const dst = dstById.get(item.delivery.destination_id);
          return (
            <li
              key={item.delivery.id + item.event.id}
              className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-gray-50"
            >
              <Badge status={item.delivery.status} /> {dst?.name}
              {dst?.active ? <Badge status="active" /> : <Badge status="paused" />}
              {item.delivery.id}
              <button
                onClick={() =>
                  replay.mutate(item.delivery.id, {
                    onSuccess: () => qc.invalidateQueries({ queryKey: ["inbox"] }),
                    onError: (err) => {
                      if (err instanceof ApiError) {
                        if (err.status === 409) {
                          handleNotification("INFO", err.message);
                        } else {
                          handleNotification("ERROR", err.message);
                        }
                        qc.invalidateQueries({ queryKey: ["inbox"] });
                      }
                    },
                  })
                }
                disabled={replay.isPending && replay.variables === item.delivery.id}
                className="mt-3 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                {replay.isPending && replay.variables === item.delivery.id
                  ? "Replaying…"
                  : "Replay"}
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
