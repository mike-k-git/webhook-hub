import { useMemo, useState } from "react";
import {
  useCreateRoute,
  useDeleteRoute,
  useDestinations,
  useRoutes,
  useSources,
} from "../api/config";
import { useNotification } from "../hooks/useNotification";
import { useQueryClient } from "@tanstack/react-query";
import { Toast } from "../components/Toast";

export function RouteConfig() {
  const { isPending, isError, data } = useRoutes();
  const sources = useSources();
  const destinations = useDestinations();
  const { notification, notify } = useNotification();
  const [sourceId, setSourceId] = useState("");
  const [destinationId, setDestinationId] = useState("");
  const createRoute = useCreateRoute();
  const deleteRoute = useDeleteRoute();

  const dstById = useMemo(
    () => new Map((destinations.data ?? []).map((d) => [d.id, d])),
    [destinations.data],
  );
  const srcById = useMemo(
    () => new Map((sources.data ?? []).map((s) => [s.id, s])),
    [sources.data],
  );
  const qc = useQueryClient();

  if (isPending || sources.isPending || destinations.isPending) return <h1>Loading...</h1>;
  if (isError || sources.isError || destinations.isError) return <h1>Error</h1>;
  return (
    <div>
      <Toast notification={notification} />
      <h2>Routes:</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          createRoute.mutate(
            { source_id: sourceId, destination_id: destinationId },
            {
              onSuccess: () => {
                qc.invalidateQueries({ queryKey: ["routes"] });
                setSourceId("");
                setDestinationId("");
              },
              onError: (err) => {
                notify({ type: "ERROR", message: err.message });
              },
            },
          );
        }}
      >
        <div>
          <label>
            Source:
            <select value={sourceId} onChange={(e) => setSourceId(e.currentTarget.value)}>
              <option value="" disabled>
                Select a source
              </option>
              {(sources.data ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div>
          <label>
            Destination:
            <select value={destinationId} onChange={(e) => setDestinationId(e.currentTarget.value)}>
              <option value="" disabled>
                Select a destination
              </option>
              {(destinations.data ?? []).map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <button type="submit" disabled={!sourceId || !destinationId}>
          Create Route
        </button>
      </form>
      <ol>
        {data.map((r) => {
          const src = srcById.get(r.source_id);
          const dst = dstById.get(r.destination_id);
          return (
            <li key={r.id}>
              {src?.name || ""}
              {" -> "}
              {dst?.name || ""}
              <button
                onClick={() => {
                  deleteRoute.mutate(
                    { id: r.id },
                    {
                      onSuccess: () => qc.invalidateQueries({ queryKey: ["routes"] }),
                      onError: (err) => {
                        notify({ type: "ERROR", message: err.message });
                      },
                    },
                  );
                }}
                disabled={deleteRoute.isPending && deleteRoute.variables.id == r.id}
              >
                Delete
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
