import React from "react";
import { Sources } from "./Sources";
import { Destinations } from "./Destinations";
import { RouteConfig } from "./RouteConfig";

export function Config() {
  return (
    <React.Fragment>
      <Sources />
      <Destinations />
      <RouteConfig />
    </React.Fragment>
  );
}
