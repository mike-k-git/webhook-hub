import { ModeToggle } from "@/components/mode-toggle";
import { useHealthCheck } from "../api/healthCheck";
import { Link, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { Toaster } from "@/components/ui/sonner";
import { Badge } from "@/components/ui/badge";

function HealthCheckBadge() {
  const { isPending, isError, data } = useHealthCheck();
  if (isPending) {
    return (
      <div className="min-w-12">
        <Badge variant="warning">Loading...</Badge>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-w-12">
        <Badge variant="danger">Error</Badge>
      </div>
    );
  }

  return (
    <div className="min-w-12">
      <Badge variant="success">{data.status}</Badge>
    </div>
  );
}

export function RootComponent() {
  return (
    <div className="w-full">
      <Toaster />
      <div className="p-2 flex gap-2 text-lg border-b">
        <ModeToggle />
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
      <div className="flex flex-col min-h-screen justify-start items-center">
        <Outlet />
      </div>
      <TanStackRouterDevtools position="bottom-right" />
    </div>
  );
}
