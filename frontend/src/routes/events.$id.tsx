import { createFileRoute } from "@tanstack/react-router";
import { useEvent } from "../api/events";
import { useDestinations } from "../api/config";
import { useMemo } from "react";
import { Badge } from "../components/Badge";
import { useReplay } from "../api/inbox";
import { useQueryClient } from "@tanstack/react-query";

export const Route = createFileRoute("/events/$id")({
  component: EventDetail,
});

function EventDetail() {
  const { id } = Route.useParams();
  const { data, isPending, isError } = useEvent(id);
  const { data: destinations } = useDestinations();
  const dstById = useMemo(
    () => new Map((destinations ?? []).map((d) => [d.id, d])),
    [destinations],
  );

  const replay = useReplay();
  const qc = useQueryClient();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div>
      <div className="m-4">
        <p className="text-2xl">Payload</p>
        <p className="whitespace-pre">{JSON.stringify(data.payload, null, 2)}</p>
      </div>
      <div className="m-4">
        <p className="text-2xl">Headers</p>
        {Object.entries(data.headers).map(([h, v]) => (
          <p key={h.concat(v)}>
            <span>{h}</span>: <span className="font-semibold">{v}</span>
          </p>
        ))}
      </div>
      <div className="m-4">
        <p className="text-2xl">Deliveries</p>
        {data.deliveries.map((d) => {
          const dst = dstById.get(d.destination_id);
          return (
            <div key={d.id}>
              <Badge status={d.status} />
              <span className="px-1">
                {d.attempt_count == 1 ? "1 attempt" : `${d.attempt_count} attempts`}
              </span>
              <ol>
                {d.attempts.map((a) => (
                  <li key={a.attempt_number}>
                    {a.attempt_number === 0
                      ? "System: dead-lettered without delivery (no attempt made)"
                      : `Attempt #${a.attempt_number} at ${new Date(a.attempted_at).toLocaleString()} for ${a.duration_ms} ms`}
                  </li>
                ))}
              </ol>
              {dst && (
                <span>
                  {dst.name} {dst.active ? <Badge status="active" /> : <Badge status="paused" />}
                </span>
              )}
              <button
                onClick={() =>
                  replay.mutate(d.id, {
                    onSuccess: () => qc.invalidateQueries({ queryKey: ["event", id] }),
                  })
                }
                disabled={
                  d.status !== "dead_letter" || (replay.isPending && replay.variables === d.id)
                }
                className="mt-3 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                {replay.isPending && replay.variables === d.id ? "Replaying…" : "Replay"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
