import { Badge } from "./badge";

export function LivenessBadge({ active }: { active: boolean }) {
  if (active) {
    return <Badge variant="success">active</Badge>;
  }

  return <Badge variant="warning">paused</Badge>;
}
