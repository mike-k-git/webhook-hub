import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/events/$id")({
  component: RouteComponent,
});

function RouteComponent() {
  const { id } = Route.useParams();
  return <div>Event {id}</div>;
}
