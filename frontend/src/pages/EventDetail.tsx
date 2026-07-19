import { useParams } from "@tanstack/react-router";
import { useEvent } from "../api/events";
import { useDestinations } from "../api/config";
import { useMemo } from "react";
import { useReplay } from "../api/inbox";
import { useQueryClient } from "@tanstack/react-query";
import { StatusBadge } from "@/components/ui/status-badge";
import { LivenessBadge } from "@/components/ui/liveness-badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table";

export function EventDetail() {
  const { id } = useParams({ from: "/events/$id" });
  const { data, isPending, isError } = useEvent(id);
  const { data: destinations } = useDestinations();
  const dstById = useMemo(
    () => new Map((destinations ?? []).map((d) => [d.id, d])),
    [destinations],
  );

  const replay = useReplay();
  const qc = useQueryClient();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div className="w-full max-w-2xl">
      <Card className="p-4 m-4">
        <CardHeader>
          <CardTitle>Payload</CardTitle>
          <CardDescription>Event Data</CardDescription>
        </CardHeader>
        <CardContent className="whitespace-pre">
          {JSON.stringify(data.payload, null, 2)}
        </CardContent>
      </Card>
      <Card className="p-4 m-4">
        <CardHeader>
          <CardTitle>Headers</CardTitle>
          <CardDescription>Event Headers</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableBody>
              {Object.entries(data.headers).map(([h, v]) => (
                <TableRow key={h.concat(v)}>
                  <TableCell>{h}</TableCell>
                  <TableCell>{v}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      {data.deliveries.map((d) => {
        const dst = dstById.get(d.destination_id);
        return (
          <Card className="p-4 m-4" key={d.id}>
            <CardHeader>
              <CardTitle>
                {dst?.name} {dst && <LivenessBadge active={dst.active} />}
              </CardTitle>
              <CardDescription>
                <StatusBadge status={d.status} count={d.attempt_count} />
                <span className="px-1">
                  {d.attempt_count == 1 ? "1 attempt" : `${d.attempt_count} attempts`}
                </span>
              </CardDescription>
              <CardAction>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    replay.mutate(d.id, {
                      onSuccess: () => qc.invalidateQueries({ queryKey: ["event", id] }),
                    })
                  }
                  disabled={
                    d.status !== "dead_letter" || (replay.isPending && replay.variables === d.id)
                  }
                >
                  {replay.isPending && replay.variables === d.id ? "Replaying…" : "Replay"}
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent>
              <ol>
                {d.attempts.map((a) => (
                  <li key={a.attempt_number}>
                    {a.attempt_number === 0
                      ? "System: dead-lettered without delivery (no attempt made)"
                      : `Attempt #${a.attempt_number} at ${new Date(a.attempted_at).toLocaleString()} for ${a.duration_ms} ms`}
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
