import { createFileRoute } from "@tanstack/react-router";
import { useDestinations, useRoutes, useSources } from "../api/config";
import React from "react";

export const Route = createFileRoute("/config")({
  component: Config,
});

function Sources() {
  const { isPending, isError, data } = useSources();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div>
      <h2>Sources:</h2>
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

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div>
      <h2>Destinations:</h2>
      <ol>
        {data.map((d) => (
          <li key={d.id}>{d.id}</li>
        ))}
      </ol>
    </div>
  );
}

function Routes() {
  const { isPending, isError, data } = useRoutes();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div>
      <h2>Routes:</h2>
      <ol>
        {data.map((r) => (
          <li key={r.id}>{r.id}</li>
        ))}
      </ol>
    </div>
  );
}

function Config() {
  return (
    <React.Fragment>
      <Routes />
      <Sources />
      <Destinations />
    </React.Fragment>
  );
}
