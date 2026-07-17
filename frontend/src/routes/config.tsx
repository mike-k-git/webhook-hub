import { createFileRoute } from "@tanstack/react-router";
import {
  useCreateDestination,
  useCreateRoute,
  useCreateSource,
  useDeleteRoute,
  useDestinations,
  useRoutes,
  useSources,
  useToggleDestination,
} from "../api/config";
import React, { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNotification } from "../hooks/useNotification";
import { Toast } from "../components/Toast";
import { Badge } from "../components/Badge";
import { ApiError } from "../api/errors";

export const Route = createFileRoute("/config")({
  component: Config,
});

function Sources() {
  const { isPending, isError, data } = useSources();
  const createSource = useCreateSource();
  const { notification, notify } = useNotification();
  const [name, setName] = useState("");
  const [secret, setSecret] = useState("");
  const qc = useQueryClient();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div>
      <Toast notification={notification} />
      <h2>Sources:</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          createSource.mutate(
            { name: name, signing_secret: secret },
            {
              onSuccess: () => {
                qc.invalidateQueries({ queryKey: ["sources"] });
                setName("");
                setSecret("");
              },
              onError: (err) => {
                notify({ type: "ERROR", message: err.message });
              },
            },
          );
        }}
      >
        <div>
          <label>Name:</label>
          <input type="text" value={name} onChange={(e) => setName(e.currentTarget.value)} />
        </div>
        <div>
          <label>Secret:</label>
          <input type="text" value={secret} onChange={(e) => setSecret(e.currentTarget.value)} />
        </div>
        <button type="submit">Submit</button>
      </form>
      <ol>
        {data.map((s) => (
          <li key={s.id}>
            {s.id} {s.name}
          </li>
        ))}
      </ol>
    </div>
  );
}

function Destinations() {
  const { isPending, isError, data } = useDestinations();
  const { notification, notify } = useNotification();
  const createDestination = useCreateDestination();
  const toggleDestination = useToggleDestination();

  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [secret, setSecret] = useState("");
  const [active, setActive] = useState(true);

  const qc = useQueryClient();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div>
      <Toast notification={notification} />
      <h2>Destinations:</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          createDestination.mutate(
            { name, url, signing_secret: secret || undefined, active },
            {
              onSuccess: () => {
                qc.invalidateQueries({ queryKey: ["destinations"] });
                setName("");
                setUrl("");
                setSecret("");
                setActive(true);
              },
              onError: (err) => {
                notify({ type: "ERROR", message: err.message });
              },
            },
          );
        }}
      >
        <div>
          <label>Name:</label>
          <input type="text" value={name} onChange={(e) => setName(e.currentTarget.value)} />
        </div>
        <div>
          <label>URL:</label>
          <input type="text" value={url} onChange={(e) => setUrl(e.currentTarget.value)} />
        </div>
        <div>
          <label>Secret:</label>
          <input type="text" value={secret} onChange={(e) => setSecret(e.currentTarget.value)} />
        </div>
        <div>
          <input
            type="checkbox"
            id="active"
            name="active"
            checked={active}
            onChange={(e) => setActive(e.currentTarget.checked)}
          />
          <label htmlFor="active">Active</label>
        </div>
        <button type="submit">Submit</button>
      </form>
      <ol>
        {data.map((d) => (
          <li key={d.id}>
            {d.id} {d.url} {d.active ? <Badge status="active" /> : <Badge status="paused" />}{" "}
            <button
              onClick={() => {
                toggleDestination.mutate(
                  { id: d.id, active: !d.active },
                  {
                    onSuccess: () => qc.invalidateQueries({ queryKey: ["destinations"] }),
                    onError: (err) => {
                      if (err instanceof ApiError && err.status === 409) {
                        notify({ type: "INFO", message: err.message });
                      } else {
                        notify({ type: "ERROR", message: err.message });
                      }
                    },
                  },
                );
              }}
              disabled={toggleDestination.isPending && toggleDestination.variables.id == d.id}
            >
              {d.active ? "Disable" : "Enable"}
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}

function Routes() {
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

function Config() {
  return (
    <React.Fragment>
      <Sources />
      <Destinations />
      <Routes />
    </React.Fragment>
  );
}
