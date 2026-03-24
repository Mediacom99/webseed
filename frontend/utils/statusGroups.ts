interface StatusGroup {
  key: string;
  label: string;
  statuses?: string[];
}

export const STATUS_GROUPS: StatusGroup[] = [
  { key: "all", label: "All" },
  { key: "searched", label: "Searched", statuses: ["searched"] },
  { key: "enriched", label: "Enriched", statuses: ["enriched"] },
  { key: "generated", label: "Generated", statuses: ["generated"] },
  { key: "tested", label: "Tested", statuses: ["tested"] },
  { key: "deployed", label: "Deployed", statuses: ["deployed"] },
  { key: "emailed", label: "Emailed", statuses: ["emailed", "email_queued"] },
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

export function filterKeyToStatuses(
  key: string,
): string[] | undefined {
  const group = STATUS_GROUPS.find((g) => g.key === key);
  if (!group || key === "all") return undefined;
  return group.statuses ? [...group.statuses] : undefined;
}
