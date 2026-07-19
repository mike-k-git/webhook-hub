import { useMemo, useState } from "react";
import {
  useCreateRoute,
  useDeleteRoute,
  useDestinations,
  useRoutes,
  useSources,
} from "../api/config";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "@/components/ui/table";

export function RouteConfig() {
  const { isPending, isError, data } = useRoutes();
  const sources = useSources();
  const destinations = useDestinations();
  const [sourceId, setSourceId] = useState("");
  const [destinationId, setDestinationId] = useState("");
  const createRoute = useCreateRoute();
  const deleteRoute = useDeleteRoute();

  const dstById = useMemo(
    () => new Map((destinations.data ?? []).map((d) => [d.id, d])),
    [destinations.data],
  );
  const srcById = useMemo(
    () => new Map((sources.data ?? []).map((s) => [s.id, s])),
    [sources.data],
  );
  const qc = useQueryClient();

  if (isPending || sources.isPending || destinations.isPending) return <h1>Loading...</h1>;
  if (isError || sources.isError || destinations.isError) return <h1>Error</h1>;
  return (
    <div className="w-full max-w-xl">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          createRoute.mutate(
            { source_id: sourceId, destination_id: destinationId },
            {
              onSuccess: () => {
                qc.invalidateQueries({ queryKey: ["routes"] });
                setSourceId("");
                setDestinationId("");
              },
              onError: (err) => {
                setSourceId("");
                setDestinationId("");
                toast.error(err.message);
              },
            },
          );
        }}
      >
        <FieldGroup>
          <FieldSet>
            <FieldLegend>Routes</FieldLegend>
            <FieldDescription>
              A wiring rule connecting one source to one destination.
            </FieldDescription>
            <FieldGroup>
              <Field orientation="horizontal">
                <FieldLabel htmlFor="source-route">Source</FieldLabel>
                <Select value={sourceId} onValueChange={(v) => setSourceId(v)}>
                  <SelectTrigger id="source-route">
                    <SelectValue placeholder="Select a source" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      {(sources.data ?? []).map((s) => (
                        <SelectItem key={s.id} value={s.id}>
                          {s.name}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </Field>
            </FieldGroup>
            <FieldGroup>
              <Field orientation="horizontal">
                <FieldLabel htmlFor="source-destination">Destination</FieldLabel>
                <Select value={destinationId} onValueChange={(v) => setDestinationId(v)}>
                  <SelectTrigger id="source-destination">
                    <SelectValue placeholder="Select a destination" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      {(destinations.data ?? []).map((d) => (
                        <SelectItem key={d.id} value={d.id}>
                          {d.name}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </Field>
            </FieldGroup>
          </FieldSet>
          <Field>
            <Button type="submit">Create New Route</Button>
          </Field>
        </FieldGroup>
      </form>
      <Table className="mt-4">
        <TableHeader>
          <TableRow>
            <TableCell>Source</TableCell>
            <TableCell>Destination</TableCell>
            <TableCell className="text-right">Action</TableCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((r) => {
            const src = srcById.get(r.source_id);
            const dst = dstById.get(r.destination_id);
            return (
              <TableRow key={r.id}>
                <TableCell>{src?.name}</TableCell>
                <TableCell>{dst?.name}</TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => {
                      deleteRoute.mutate(
                        { id: r.id },
                        {
                          onSuccess: () => qc.invalidateQueries({ queryKey: ["routes"] }),
                          onError: (err) => {
                            toast.error(err.message);
                          },
                        },
                      );
                    }}
                    disabled={deleteRoute.isPending && deleteRoute.variables.id == r.id}
                  >
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
