import { useMutation, useQuery } from "@tanstack/react-query";
import { client } from "./client";

export function useInbox() {
  return useQuery({
    queryKey: ["inbox"],
    queryFn: async () => {
      const { data, error } = await client.GET("/deliveries/dead_letter", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useReplay(delivery_id: string) {
  return useMutation({
    mutationKey: ["inbox"],
    mutationFn: async () => {
      const { data, error } = await client.POST("/deliveries/{delivery_id}/replay", {
        params: { path: { delivery_id } },
      });
      if (error) throw error;
      return data;
    },
  });
}
