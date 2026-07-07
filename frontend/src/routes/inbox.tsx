import { createFileRoute } from "@tanstack/react-router";
import { useInbox } from "../api/inbox";

export const Route = createFileRoute("/inbox")({
  component: Inbox,
});

function Inbox() {
  const { isPending, isError, data } = useInbox();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div>
      <ol>
        {data.map((item) => (
          <li key={item.delivery.id + item.event.id}>{item.delivery.id}</li>
        ))}
      </ol>
    </div>
  );
}
