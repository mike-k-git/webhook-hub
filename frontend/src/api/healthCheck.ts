import { useQuery } from "@tanstack/react-query";
import { client } from "./client";

export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data, error } = await client.GET("/healthz");
      if (error) throw error;
      return data;
    },
  });
}
