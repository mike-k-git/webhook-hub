import { Link, useSearch } from "@tanstack/react-router";
import { useEvents } from "../api/events";
import { StatusBadge } from "@/components/ui/status-badge";
import type { components } from "@/api/schema";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function Events() {
  const { source, status } = useSearch({ from: "/events/" });
  const { isPending, isError, data, fetchNextPage, hasNextPage, isFetchingNextPage } = useEvents(
    source,
    status,
  );

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <>
      <Table>
        <TableCaption>The latest received webhooks</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Event ID</TableHead>
            <TableHead>Received</TableHead>
            <TableHead>Statuses</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.pages
            .flatMap((p) => p.items)
            .map((e) => (
              <TableRow key={e.id}>
                <TableCell>
                  <Link to="/events/$id" params={{ id: e.id }}>
                    {e.id}
                  </Link>
                </TableCell>
                <TableCell>{new Date(e.received_at).toLocaleString()}</TableCell>
                <TableCell>
                  {e.rollup.total > 0 &&
                    (
                      Object.entries(e.rollup.counts_by_status) as [
                        components["schemas"]["DeliveryStatus"],
                        number,
                      ][]
                    ).map(([deliveryStatus, count]) => (
                      <StatusBadge key={deliveryStatus} status={deliveryStatus} count={count} />
                    ))}
                </TableCell>
              </TableRow>
            ))}
        </TableBody>
      </Table>
      {hasNextPage && (
        <Button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? "Loading..." : "Load more"}
        </Button>
      )}
    </>
  );
}
