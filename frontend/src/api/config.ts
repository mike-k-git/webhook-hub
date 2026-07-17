import { useMutation, useQuery } from "@tanstack/react-query";
import { client } from "./client";
import type { components } from "./schema";
import { ApiError } from "./errors";

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

export function useCreateSource() {
  return useMutation({
    mutationFn: async (newSource: components["schemas"]["SourceCreate"]) => {
      const { data, error, response } = await client.POST("/sources", { body: newSource });
      if (error)
        throw new ApiError(
          response.status,
          typeof error.detail === "string" ? error.detail : "create source error",
        );
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

export function useCreateDestination() {
  return useMutation({
    mutationFn: async (newDestination: components["schemas"]["DestinationCreate"]) => {
      const { data, error, response } = await client.POST("/destinations", {
        body: newDestination,
      });
      if (error)
        throw new ApiError(
          response.status,
          typeof error.detail === "string" ? error.detail : "create destination error",
        );
      return data;
    },
  });
}

export function useToggleDestination() {
  return useMutation({
    mutationFn: async ({ id, active }: { id: string; active: boolean }) => {
      const { data, error, response } = await client.PATCH("/destinations/{destination_id}", {
        params: { path: { destination_id: id } },
        body: { active },
      });
      if (error)
        throw new ApiError(
          response.status,
          typeof error.detail === "string" ? error.detail : "toggle destination error",
        );
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

export function useCreateRoute() {
  return useMutation({
    mutationFn: async (newRoute: components["schemas"]["RouteCreate"]) => {
      const { data, error, response } = await client.POST("/routes", {
        body: newRoute,
      });
      if (error)
        throw new ApiError(
          response.status,
          typeof error.detail === "string" ? error.detail : "create route error",
        );
      return data;
    },
  });
}

export function useDeleteRoute() {
  return useMutation({
    mutationFn: async ({ id }: { id: string }) => {
      const { error, response } = await client.DELETE("/routes/{route_id}", {
        params: { path: { route_id: id } },
      });
      if (error)
        throw new ApiError(
          response.status,
          typeof error.detail === "string" ? error.detail : "route deletion error",
        );
    },
  });
}
