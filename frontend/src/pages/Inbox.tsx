import { useMemo } from "react";
import { useDestinations } from "../api/config";
import { useInbox, useReplay } from "../api/inbox";
import { useQueryClient } from "@tanstack/react-query";
import { ApiError } from "../api/errors";
import { toast } from "sonner";
import { StatusBadge } from "@/components/ui/status-badge";
import { LivenessBadge } from "@/components/ui/liveness-badge";
import { Button } from "@/components/ui/button";

export function Inbox() {
  const { isPending, isError, data } = useInbox();
  const { data: destinations } = useDestinations();
  const dstById = useMemo(
    () => new Map((destinations ?? []).map((d) => [d.id, d])),
    [destinations],
  );
  const replay = useReplay();
  const qc = useQueryClient();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  if (data.length === 0) return <h1>No dead-lettered deliveries</h1>;
  return (
    <div>
      <ol className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {data.map((item) => {
          const dst = dstById.get(item.delivery.destination_id);
          return (
            <li
              key={item.delivery.id + item.event.id}
              className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-gray-50"
            >
              <StatusBadge status={item.delivery.status} />
              {dst?.name}
              {dst?.active && <LivenessBadge active={dst.active} />}
              {item.delivery.id}
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  replay.mutate(item.delivery.id, {
                    onSuccess: () => qc.invalidateQueries({ queryKey: ["inbox"] }),
                    onError: (err) => {
                      if (err instanceof ApiError && err.status === 409) {
                        toast.info(err.message);
                      } else {
                        toast.error(err.message);
                      }
                      qc.invalidateQueries({ queryKey: ["inbox"] });
                    },
                  })
                }
                disabled={replay.isPending && replay.variables === item.delivery.id}
                className="mt-3 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                {replay.isPending && replay.variables === item.delivery.id
                  ? "Replaying…"
                  : "Replay"}
              </Button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
