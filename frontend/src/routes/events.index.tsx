import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";
import { Events } from "../pages/Events";

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
