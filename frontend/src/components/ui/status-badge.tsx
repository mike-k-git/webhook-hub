import type { components } from "@/api/schema";
import { Badge, badgeVariants } from "./badge";
import type { VariantProps } from "class-variance-authority";

type BadgeVariants = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;
type DeliveryStatus = components["schemas"]["DeliveryStatus"];

const statusVariant: Record<DeliveryStatus, BadgeVariants> = {
  succeeded: "success",
  pending: "warning",
  delivering: "info",
  failed: "danger",
  dead_letter: "critical",
};

export function StatusBadge({ status, count }: { status: DeliveryStatus; count?: number }) {
  return (
    <Badge variant={statusVariant[status]}>
      {status}
      {count !== undefined && ` ${count}`}
    </Badge>
  );
}
