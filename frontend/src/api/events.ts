import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { client } from "./client";
import type { components } from "./schema";
import { ApiError } from "./errors";

export function useEvent(event_id: string) {
  return useQuery({
    queryKey: ["event", event_id],
    queryFn: async () => {
      const { data, error, response } = await client.GET("/events/{event_id}", {
        params: { path: { event_id } },
      });
      if (error)
        throw new ApiError(
          response.status,
          typeof error.detail === "string" ? error.detail : "event details load failed",
        );
      return data;
    },
    refetchInterval: 5_000,
  });
}

export function useEvents(
  source?: string,
  status?: components["schemas"]["DeliveryStatus"],
  limit: number = 50,
) {
  return useInfiniteQuery({
    queryKey: ["events", source, status, limit],
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam }) => {
      const { data, error, response } = await client.GET("/events", {
        params: { query: { source, status, limit, cursor: pageParam } },
      });
      if (error)
        throw new ApiError(
          response.status,
          typeof error.detail === "string" ? error.detail : "events load failed",
        );
      return data;
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    refetchInterval: 5_000,
  });
}
