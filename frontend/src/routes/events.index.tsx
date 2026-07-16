import { createFileRoute, Link } from "@tanstack/react-router";
import { useEvents } from "../api/events";
import { z } from "zod";
import { Badge } from "../components/Badge";

const eventFilters = z.object({
  source: z.string().optional(),
  status: z
    .enum(["pending", "delivering", "succeeded", "failed", "dead_letter"])
    .optional()
    .catch(undefined),
});

export const Route = createFileRoute("/events/")({
  component: Events,
  validateSearch: eventFilters,
});

function Events() {
  const { source, status } = Route.useSearch();
  const { isPending, isError, data, fetchNextPage, hasNextPage, isFetchingNextPage } = useEvents(
    source,
    status,
  );

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div>
      <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {data.pages
          .flatMap((p) => p.items)
          .map((e) => (
            <li key={e.id} className="hover:bg-gray-50">
              <Link
                to="/events/$id"
                params={{ id: e.id }}
                className="flex items-center justify-between gap-4 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="truncate font-mono text-sm text-gray-900">{e.id}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(e.received_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex flex-wrap gap-1">
                  {e.rollup.total > 0 && (
                    <>
                      {Object.entries(e.rollup.counts_by_status).map(([deliveryStatus, count]) => (
                        <Badge key={deliveryStatus} status={deliveryStatus} count={count} />
                      ))}
                    </>
                  )}
                </div>
              </Link>
            </li>
          ))}
      </ul>
      {hasNextPage && (
        <button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
          className="mt-3 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
        >
          {isFetchingNextPage ? "Loading..." : "Load more"}
        </button>
      )}
    </div>
  );
}
