import { useState } from "react";
import { useCreateDestination, useDestinations, useToggleDestination } from "../api/config";
import { useQueryClient } from "@tanstack/react-query";
import { ApiError } from "../api/errors";
import { toast } from "sonner";
import {
  Field,
  FieldContent,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { LivenessBadge } from "@/components/ui/liveness-badge";

export function Destinations() {
  const { isPending, isError, data } = useDestinations();
  const createDestination = useCreateDestination();
  const toggleDestination = useToggleDestination();

  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [secret, setSecret] = useState("");
  const [active, setActive] = useState<boolean>(true);

  const qc = useQueryClient();

  if (isPending) return <h1>Loading...</h1>;
  if (isError) return <h1>Error</h1>;
  return (
    <div className="w-full max-w-xl">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          createDestination.mutate(
            { name, url, signing_secret: secret || undefined, active },
            {
              onSuccess: () => {
                qc.invalidateQueries({ queryKey: ["destinations"] });
                setName("");
                setUrl("");
                setSecret("");
                setActive(true);
              },
              onError: (err) => {
                setName("");
                setUrl("");
                setSecret("");
                setActive(true);
                toast.error(err.message);
              },
            },
          );
        }}
      >
        <FieldGroup>
          <FieldSet>
            <FieldLegend>Destinations</FieldLegend>
            <FieldDescription>A configured endpoint we send webhooks to.</FieldDescription>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="destination-name">Destination Name</FieldLabel>
                <Input
                  id="destination-name"
                  type="text"
                  value={name}
                  placeholder="New destination"
                  required
                  onChange={(e) => setName(e.currentTarget.value)}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="destination-url">URL</FieldLabel>
                <Input
                  id="destination-url"
                  type="text"
                  value={url}
                  placeholder="URL"
                  required
                  onChange={(e) => setUrl(e.currentTarget.value)}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="destination-secret">Destination Secret</FieldLabel>
                <Input
                  id="destination-secret"
                  type="text"
                  value={secret}
                  onChange={(e) => setSecret(e.currentTarget.value)}
                />
              </Field>
              <Field orientation="horizontal">
                <Checkbox
                  id="destination-active"
                  checked={active}
                  onCheckedChange={(checked) => {
                    setActive(!!checked);
                  }}
                />
                <FieldContent>
                  <FieldLabel htmlFor="destination-active">Active</FieldLabel>
                </FieldContent>
              </Field>
            </FieldGroup>
          </FieldSet>
          <Field>
            <Button type="submit">Create New Destination</Button>
          </Field>
        </FieldGroup>
      </form>
      <ol>
        {data.map((d) => (
          <li key={d.id}>
            {d.id} {d.url} {<LivenessBadge active={d.active} />}{" "}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                toggleDestination.mutate(
                  { id: d.id, active: !d.active },
                  {
                    onSuccess: () => qc.invalidateQueries({ queryKey: ["destinations"] }),
                    onError: (err) => {
                      if (err instanceof ApiError && err.status === 409) {
                        toast.info(err.message);
                      } else {
                        toast.error(err.message);
                      }
                    },
                  },
                );
              }}
              disabled={toggleDestination.isPending && toggleDestination.variables.id == d.id}
            >
              {d.active ? "Disable" : "Enable"}
            </Button>
          </li>
        ))}
      </ol>
    </div>
  );
}
