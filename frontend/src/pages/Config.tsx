import { Sources } from "./Sources";
import { Destinations } from "./Destinations";
import { RouteConfig } from "./RouteConfig";
import { Separator } from "@/components/ui/separator";

export function Config() {
  return (
    <div className="flex items-center w-full max-w-4xl flex-col gap-10 py-5">
      <Sources />
      <Separator />
      <Destinations />
      <Separator />
      <RouteConfig />
    </div>
  );
}
