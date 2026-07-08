const tones: Record<string, string> = {
  succeeded: "bg-green-50 text-green-700 ring-green-600/20",
  active: "bg-green-50 text-green-700 ring-green-600/20",
  pending: "bg-amber-50 text-amber-700 ring-amber-600/20",
  paused: "bg-amber-50 text-amber-700 ring-amber-600/20",
  delivering: "bg-blue-50 text-blue-700 ring-blue-600/20",
  failed: "bg-red-50 text-red-700 ring-red-600/20",
  dead_letter: "bg-rose-100 text-rose-800 ring-rose-700/30",
};

export function Badge({ status, count }: { status: string; count?: number }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${tones[status] ?? "bg-gray-100 text-gray-600 ring-gray-500/20"}`}
    >
      {status}
      {count !== undefined && ` ${count}`}
    </span>
  );
}
