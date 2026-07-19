import { useMemo } from "react";
import { useDestinations } from "../api/config";
import { useInbox, useReplay } from "../api/inbox";
import { useQueryClient } from "@tanstack/react-query";
import { ApiError } from "../api/errors";
import { toast } from "sonner";
import { StatusBadge } from "@/components/ui/status-badge";
import { LivenessBadge } from "@/components/ui/liveness-badge";
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

export function Inbox() {
  const { isPending, isError, data } = useInbox();
  const { data: destinations } = useDestinations();
  const dstById = useMemo(
    () => new Map((destinations ?? []).map((d) => [d.id, d])),
    [destinations],
  );
  const replay = useReplay();
  const qc = useQueryClient();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  if (data.length === 0) return <h1>No dead-lettered deliveries</h1>;
  return (
    <Table>
      <TableCaption>Dead-lettered deliveries.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Status</TableHead>
          <TableHead>Destination</TableHead>
          <TableHead>Delivery</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((d) => {
          const dst = dstById.get(d.delivery.destination_id);
          return (
            <TableRow key={d.delivery.id + d.event.id}>
              <TableCell>
                <StatusBadge status={d.delivery.status} />
              </TableCell>
              <TableCell>
                {dst?.name}
                {dst?.active && <LivenessBadge active={dst.active} />}
              </TableCell>
              <TableCell>{d.delivery.id}</TableCell>
              <TableCell>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    replay.mutate(d.delivery.id, {
                      onSuccess: () => qc.invalidateQueries({ queryKey: ["inbox"] }),
                      onError: (err) => {
                        if (err instanceof ApiError && err.status === 409) {
                          toast.info(err.message);
                        } else {
                          toast.error(err.message);
                        }
                        qc.invalidateQueries({ queryKey: ["inbox"] });
                      },
                    })
                  }
                  disabled={replay.isPending && replay.variables === d.delivery.id}
                >
                  {replay.isPending && replay.variables === d.delivery.id ? "Replaying…" : "Replay"}
                </Button>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
