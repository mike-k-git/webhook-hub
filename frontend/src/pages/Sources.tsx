import { useState } from "react";
import { useCreateSource, useSources } from "../api/config";
import { useNotification } from "../hooks/useNotification";
import { useQueryClient } from "@tanstack/react-query";
import { Toast } from "../components/Toast";

export function Sources() {
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
