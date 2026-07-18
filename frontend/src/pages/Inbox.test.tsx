import { server } from "../mocks/server";
import { handlers } from "../mocks/handlers/deliveries";
import { http, HttpResponse } from "msw";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import { Inbox } from "./Inbox";
import { wrapper } from "../test/test-utils";

describe("replay flow", () => {
  it("invalidation", async () => {
    let first_call = true;
    server.use(
      http.get("/api/deliveries/dead_letter", () => {
        if (first_call) {
          first_call = false;
          return HttpResponse.json([
            {
              delivery: {
                id: "be3e2e8d-b1bc-476e-8d59-d590fc127c4f",
                destination_id: "a635f40f-eb7f-4f32-aed9-3373426c7556",
                status: "dead_letter",
                attempt_count: 8,
                next_attempt_at: null,
                created_at: "2026-07-17T13:17:45.734984Z",
                updated_at: "2026-07-17T13:19:29.440967Z",
                attempts: [
                  {
                    attempt_number: 1,
                    response_status: null,
                    response_body: null,
                    error: "[Errno -2] Name or service not known",
                    duration_ms: 94,
                    attempted_at: "2026-07-17T13:17:45.959362Z",
                  },
                  {
                    attempt_number: 2,
                    response_status: null,
                    response_body: null,
                    error: "[Errno -2] Name or service not known",
                    duration_ms: 8,
                    attempted_at: "2026-07-17T13:17:50.537879Z",
                  },
                  {
                    attempt_number: 3,
                    response_status: null,
                    response_body: null,
                    error: "[Errno -2] Name or service not known",
                    duration_ms: 9,
                    attempted_at: "2026-07-17T13:17:55.576764Z",
                  },
                  {
                    attempt_number: 4,
                    response_status: null,
                    response_body: null,
                    error: "[Errno -2] Name or service not known",
                    duration_ms: 5,
                    attempted_at: "2026-07-17T13:18:05.641448Z",
                  },
                  {
                    attempt_number: 5,
                    response_status: null,
                    response_body: null,
                    error: "[Errno -2] Name or service not known",
                    duration_ms: 8,
                    attempted_at: "2026-07-17T13:18:20.753433Z",
                  },
                  {
                    attempt_number: 6,
                    response_status: null,
                    response_body: null,
                    error: "[Errno -2] Name or service not known",
                    duration_ms: 9,
                    attempted_at: "2026-07-17T13:18:56.027156Z",
                  },
                  {
                    attempt_number: 7,
                    response_status: null,
                    response_body: null,
                    error: "[Errno -2] Name or service not known",
                    duration_ms: 9,
                    attempted_at: "2026-07-17T13:19:17.432997Z",
                  },
                  {
                    attempt_number: 8,
                    response_status: null,
                    response_body: null,
                    error: "[Errno -2] Name or service not known",
                    duration_ms: 7,
                    attempted_at: "2026-07-17T13:19:29.440967Z",
                  },
                ],
              },
              event: {
                id: "be5e23bf-6552-49c6-b3b6-5d122d491fd2",
                source_id: "374c2e11-0506-4c9d-b42a-1cf3e5ad7cfb",
                event_type: "test.event",
                idempotency_key: "cde762750020d94f3cdd24d98a3a04cfd82c998c8b7db36bceaad7da42126d28",
                received_at: "2026-07-17T13:17:45.734984Z",
              },
            },
          ]);
        } else {
          return HttpResponse.json([]);
        }
      }),
      ...handlers,
    );

    const user = userEvent.setup();

    render(<Inbox />, { wrapper });

    await screen.findByRole("button", { name: /replay/i });

    await user.click(screen.getByRole("button", { name: /replay/i }));

    await screen.findByText(/no dead-lettered deliveries/i);
  });

  it("409", async () => {
    server.use(
      http.post<{ id: string }>("/api/deliveries/:id/replay", () => {
        return HttpResponse.json({ detail: "delivering" }, { status: 409 });
      }),
      ...handlers,
    );

    const user = userEvent.setup();

    render(<Inbox />, { wrapper });

    await screen.findByRole("button", { name: /replay/i });

    await user.click(screen.getByRole("button", { name: /replay/i }));

    await screen.findByText(/delivering/i);
  });
});
