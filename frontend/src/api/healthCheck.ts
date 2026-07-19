import { useQuery } from "@tanstack/react-query";
import { client } from "./client";
import { ApiError } from "./errors";

export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data, response } = await client.GET("/healthz");
      if (!response.ok || !data) throw new ApiError(response.status, "health check failed");
      return data;
    },
  });
}
