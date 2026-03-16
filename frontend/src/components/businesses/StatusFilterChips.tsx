import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const STATUS_GROUPS: { key: string; label: string; statuses: string[] }[] = [
  { key: "all", label: "All", statuses: [] },
  { key: "searched", label: "Searched", statuses: ["searched"] },
  { key: "enriched", label: "Enriched", statuses: ["enriched"] },
  { key: "generated", label: "Generated", statuses: ["generated"] },
  { key: "tested", label: "Tested", statuses: ["tested"] },
  { key: "deployed", label: "Deployed", statuses: ["deployed"] },
  {
    key: "emailed",
    label: "Emailed",
    statuses: ["emailed", "email_queued"],
  },
  {
    key: "errors",
    label: "Errors",
    statuses: [
      "error_enrich",
      "error_generate",
      "error_test",
      "error_deploy",
      "error_email",
      "error_run",
    ],
  },
  { key: "opted_out", label: "Opted Out", statuses: ["opted_out"] },
];

interface StatusFilterChipsProps {
  stats: Record<string, number>;
  activeFilter: string;
  onFilterChange: (filter: string) => void;
}

export default function StatusFilterChips({
  stats,
  activeFilter,
  onFilterChange,
}: StatusFilterChipsProps) {
  const total = Object.values(stats).reduce((sum, n) => sum + n, 0);

  return (
    <div className="flex flex-wrap gap-1.5" role="group" aria-label="Status filters">
      {STATUS_GROUPS.map((group) => {
        const count =
          group.key === "all"
            ? total
            : group.statuses.reduce((sum, s) => sum + (stats[s] ?? 0), 0);

        // Hide zero-count chips except "All"
        if (count === 0 && group.key !== "all") return null;

        const isActive = activeFilter === group.key;

        return (
          <Badge
            key={group.key}
            variant={isActive ? "default" : "outline"}
            className={cn(
              "cursor-pointer select-none",
              isActive && "ring-2 ring-ring ring-offset-1",
            )}
            onClick={() => onFilterChange(group.key)}
          >
            {group.label} ({count})
          </Badge>
        );
      })}
    </div>
  );
}

/** Given a filter key, return the statuses to query for, or undefined for "all" */
export function filterKeyToStatuses(key: string): string[] | undefined {
  if (key === "all") return undefined;
  const group = STATUS_GROUPS.find((g) => g.key === key);
  return group?.statuses;
}
