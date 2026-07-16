import { useMutation, useQuery } from "@tanstack/react-query";
import { client } from "./client";
import { ApiError } from "./errors";

export function useInbox() {
  return useQuery({
    queryKey: ["inbox"],
    queryFn: async () => {
      const { data, error } = await client.GET("/deliveries/dead_letter", {});
      if (error) throw error;
      return data;
    },
    refetchInterval: 5_000,
  });
}

export function useReplay() {
  return useMutation({
    mutationFn: async (delivery_id: string) => {
      const { data, error, response } = await client.POST("/deliveries/{delivery_id}/replay", {
        params: { path: { delivery_id } },
      });
      if (error)
        throw new ApiError(
          response.status,
          typeof error.detail === "string" ? error.detail : "replay error",
        );
      return data;
    },
  });
}
