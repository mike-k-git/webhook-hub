import { useState } from "react";
import { useCreateDestination, useDestinations, useToggleDestination } from "../api/config";
import { useNotification } from "../hooks/useNotification";
import { useQueryClient } from "@tanstack/react-query";
import { Toast } from "../components/Toast";
import { Badge } from "../components/Badge";
import { ApiError } from "../api/errors";

export function Destinations() {
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
