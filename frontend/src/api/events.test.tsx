import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type React from "react";
import { server } from "../mocks/server";
import { http, HttpResponse } from "msw";
import { renderHook, waitFor } from "@testing-library/react";
import { useEvents } from "./events";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

test("cursor pager", async () => {
  const requestedCursors: (string | null)[] = [];

  server.use(
    http.get("/api/events", ({ request }) => {
      const cursor = new URL(request.url).searchParams.get("cursor");
      requestedCursors.push(cursor);
      if (cursor === null) {
        return HttpResponse.json({
          items: [
            {
              id: "e03818d2-9850-4238-9907-76b90fdaaa31",
              source_id: "9e5c3f0b-5741-44fa-95c5-f8f7c818222e",
              idempotency_key: "key1",
              received_at: "",
              rollup: { total: 0 },
            },
            {
              id: "5fdf1a2f-dbcb-4022-a51b-0b33ea3b2bd5",
              source_id: "47f91256-5cf4-46ee-b78e-86f757977106",
              idempotency_key: "key2",
              received_at: "",
              rollup: { total: 0 },
            },
          ],
          next_cursor: "CURSOR_2",
        });
      }
      return HttpResponse.json({
        items: [
          {
            id: "032bf1e6-3fa3-4f1c-b8f3-f5786f8c0b1c",
            source_id: "353433af-178a-4489-bf6d-537da072db12",
            idempotency_key: "key3",
            received_at: "",
            rollup: { total: 0 },
          },
          {
            id: "38b2204c-22d9-411b-8f3d-6e92a8b71028",
            source_id: "6b6534e2-ae2d-45d0-a8c0-30f64a6fac6c",
            idempotency_key: "key4",
            received_at: "",
            rollup: { total: 0 },
          },
        ],
        next_cursor: null,
      });
    }),
  );

  const { result } = renderHook(() => useEvents(), { wrapper });

  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data?.pages[0]?.items[0]?.id).toEqual(
    "e03818d2-9850-4238-9907-76b90fdaaa31",
  );
  expect(result.current.data?.pages[0]?.items[1]?.id).toEqual(
    "5fdf1a2f-dbcb-4022-a51b-0b33ea3b2bd5",
  );
  expect(result.current.hasNextPage).toBe(true);

  result.current.fetchNextPage();
  await waitFor(() => expect(result.current.data?.pages).toHaveLength(2));

  expect(result.current.hasNextPage).toBe(false);

  expect(result.current.data?.pages[1]?.items[0]?.id).toEqual(
    "032bf1e6-3fa3-4f1c-b8f3-f5786f8c0b1c",
  );

  expect(requestedCursors).toEqual([null, "CURSOR_2"]);
});
