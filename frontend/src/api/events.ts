import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { client } from "./client";
import type { components } from "./schema";

export function useEvent(event_id: string) {
  return useQuery({
    queryKey: ["event", event_id],
    queryFn: async () => {
      const { data, error } = await client.GET("/events/{event_id}", {
        params: { path: { event_id } },
      });
      if (error) throw error;
      return data;
    },
  });
}

export function useEvents(
  source?: string,
  status?: components["schemas"]["DeliveryStatus"],
  limit: number = 50,
) {
  return useInfiniteQuery({
    queryKey: ["events", source, status],
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam }) => {
      const { data, error } = await client.GET("/events", {
        params: { query: { source, status, limit, cursor: pageParam } },
      });
      if (error) throw error;
      return data;
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    refetchInterval: 5_000,
  });
}
