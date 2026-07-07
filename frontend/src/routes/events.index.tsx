import { createFileRoute } from "@tanstack/react-router";
import { useEvents } from "../api/events";

export const Route = createFileRoute("/events/")({
  component: Events,
});

function Events() {
  const { isPending, isError, data } = useEvents();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div>
      <ol>
        {data.items.map((e) => (
          <li key={e.id}>{e.id}</li>
        ))}
      </ol>
    </div>
  );
}
