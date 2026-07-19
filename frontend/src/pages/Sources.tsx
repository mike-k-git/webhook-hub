import { useState } from "react";
import { useCreateSource, useSources } from "../api/config";
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
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "@/components/ui/table";

export function Sources() {
  const { isPending, isError, data } = useSources();
  const createSource = useCreateSource();
  const [name, setName] = useState("");
  const [secret, setSecret] = useState("");
  const qc = useQueryClient();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div className="w-full max-w-xl">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          createSource.mutate(
            { name, signing_secret: secret },
            {
              onSuccess: () => {
                qc.invalidateQueries({ queryKey: ["sources"] });
                setName("");
                setSecret("");
              },
              onError: (err) => {
                setName("");
                setSecret("");
                toast.error(err.message);
              },
            },
          );
        }}
      >
        <FieldGroup>
          <FieldSet>
            <FieldLegend>Sources</FieldLegend>
            <FieldDescription>A configured system that sends webhooks to us.</FieldDescription>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="source-name">Source Name</FieldLabel>
                <Input
                  id="source-name"
                  type="text"
                  value={name}
                  placeholder="GitHub"
                  required
                  onChange={(e) => setName(e.currentTarget.value)}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="source-secret">Source Secret</FieldLabel>
                <Input
                  id="source-secret"
                  type="text"
                  value={secret}
                  required
                  onChange={(e) => setSecret(e.currentTarget.value)}
                />
              </Field>
            </FieldGroup>
          </FieldSet>
          <Field>
            <Button type="submit">Create New Source</Button>
          </Field>
        </FieldGroup>
      </form>
      <Table>
        <TableHeader>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>ID</TableCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((s) => (
            <TableRow key={s.id}>
              <TableCell className="font-bold">{s.name}</TableCell>
              <TableCell className="font-mono text-primary/50">{s.id}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
