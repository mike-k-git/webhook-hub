import { Link, Outlet, createRootRoute } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useHealthCheck } from "../api/healthCheck";

export const Route = createRootRoute({
  component: RootComponent,
});

const queryClient = new QueryClient();

function HealthCheckBadge() {
  const { isPending, isError, data } = useHealthCheck();
  if (isPending) {
    return (
      <span className="inline-flex items-center rounded-md bg-yellow-400/10 px-2 py-1 text-xs font-medium text-yellow-500 inset-ring inset-ring-yellow-400/20">
        Loading...
      </span>
    );
  }

  if (isError) {
    return (
      <span className="inline-flex items-center rounded-md bg-red-400/10 px-2 py-1 text-xs font-medium text-red-400 inset-ring inset-ring-red-400/20">
        Error
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-md bg-green-400/10 px-2 py-1 text-xs font-medium text-green-400 inset-ring inset-ring-green-500/20">
      {data.status}
    </span>
  );
}

function RootComponent() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="p-2 flex gap-2 text-lg border-b">
        <HealthCheckBadge />
        <Link
          to="/events"
          activeProps={{
            className: "font-bold",
          }}
        >
          Events
        </Link>{" "}
        <Link
          to="/inbox"
          activeProps={{
            className: "font-bold",
          }}
        >
          Inbox
        </Link>{" "}
        <Link
          to="/config"
          activeProps={{
            className: "font-bold",
          }}
        >
          Config
        </Link>
      </div>
      <Outlet />
      <TanStackRouterDevtools position="bottom-right" />
    </QueryClientProvider>
  );
}
