import { useQuery } from "@tanstack/react-query";
import { client } from "./client";

export function useSources() {
  return useQuery({
    queryKey: ["sources"],
    queryFn: async () => {
      const { data, error } = await client.GET("/sources", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useDestinations() {
  return useQuery({
    queryKey: ["destinations"],
    queryFn: async () => {
      const { data, error } = await client.GET("/destinations", {});
      if (error) throw error;
      return data;
    },
  });
}

export function useRoutes() {
  return useQuery({
    queryKey: ["routes"],
    queryFn: async () => {
      const { data, error } = await client.GET("/routes", {});
      if (error) throw error;
      return data;
    },
  });
}
