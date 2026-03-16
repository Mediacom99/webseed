import { useState } from "react";
import { Loader2, Trash2, Ban } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  usePipelineGeneratePipelineGeneratePost,
  usePipelineTestPipelineTestPost,
  usePipelineDeployPipelineDeployPost,
  usePipelineEmailPipelineEmailPost,
  usePipelineEnrichPipelineEnrichPost,
} from "@/api/endpoints/pipeline/pipeline";
import {
  useBlacklistAddBusinessesPlaceIdBlacklistPost,
  useHardDeleteBusinessesHardDeletePost,
} from "@/api/endpoints/businesses/businesses";
import type { BusinessRow } from "./BusinessTable";

const STATUS_TO_NEXT_ACTION: Record<string, { label: string; step: string }> = {
  enriched: { label: "Generate", step: "generate" },
  generated: { label: "Test", step: "test" },
  tested: { label: "Deploy", step: "deploy" },
  deployed: { label: "Email", step: "email" },
  error_enrich: { label: "Retry Enrich", step: "enrich" },
  error_generate: { label: "Retry Generate", step: "generate" },
  error_test: { label: "Retry Test", step: "test" },
  error_deploy: { label: "Retry Deploy", step: "deploy" },
  error_email: { label: "Retry Email", step: "email" },
};

interface BulkActionBarProps {
  selectedIds: Set<string>;
  businesses: BusinessRow[];
  onActionComplete: () => void;
}

export default function BulkActionBar({
  selectedIds,
  businesses,
  onActionComplete,
}: BulkActionBarProps) {
  const [blacklisting, setBlacklisting] = useState(false);

  const generateMutation = usePipelineGeneratePipelineGeneratePost();
  const testMutation = usePipelineTestPipelineTestPost();
  const deployMutation = usePipelineDeployPipelineDeployPost();
  const emailMutation = usePipelineEmailPipelineEmailPost();
  const enrichMutation = usePipelineEnrichPipelineEnrichPost();
  const hardDeleteMutation = useHardDeleteBusinessesHardDeletePost();
  const blacklistMutation = useBlacklistAddBusinessesPlaceIdBlacklistPost();

  const count = selectedIds.size;
  if (count === 0) return null;

  const selectedBusinesses = businesses.filter((b) =>
    selectedIds.has(b.place_id),
  );
  const selectedStatuses = new Set(selectedBusinesses.map((b) => b.status));

  // Determine applicable actions
  const actions: { label: string; step: string }[] = [];
  const seen = new Set<string>();
  for (const status of selectedStatuses) {
    const action = STATUS_TO_NEXT_ACTION[status];
    if (action && !seen.has(action.step)) {
      seen.add(action.step);
      actions.push(action);
    }
  }

  const placeIds = Array.from(selectedIds);

  const runStep = (step: string, label: string) => {
    const data = { data: { place_ids: placeIds } };
    const opts = {
      onSuccess: () => {
        toast.success(`${label} started for ${count} business${count > 1 ? "es" : ""}`);
        onActionComplete();
      },
      onError: () => toast.error(`${label} failed`),
    };

    switch (step) {
      case "enrich":
        enrichMutation.mutate(data, opts);
        break;
      case "generate":
        generateMutation.mutate(data, opts);
        break;
      case "test":
        testMutation.mutate(data, opts);
        break;
      case "deploy":
        deployMutation.mutate(data, opts);
        break;
      case "email":
        emailMutation.mutate(data, opts);
        break;
    }
  };

  const handleBlacklist = async () => {
    setBlacklisting(true);
    try {
      for (const id of placeIds) {
        await blacklistMutation.mutateAsync({ placeId: id });
      }
      toast.success(`${count} business${count > 1 ? "es" : ""} blacklisted`);
      onActionComplete();
    } catch {
      toast.error("Blacklist failed");
    } finally {
      setBlacklisting(false);
    }
  };

  const handleDelete = () => {
    hardDeleteMutation.mutate(
      { data: { place_ids: placeIds } },
      {
        onSuccess: () => {
          toast.success(`Deleted ${count} business${count > 1 ? "es" : ""}`);
          onActionComplete();
        },
        onError: () => toast.error("Delete failed"),
      },
    );
  };

  const anyPending =
    generateMutation.isPending ||
    testMutation.isPending ||
    deployMutation.isPending ||
    emailMutation.isPending ||
    enrichMutation.isPending;

  return (
    <div className="sticky bottom-0 flex flex-wrap items-center gap-2 rounded-lg border bg-background p-3 shadow-sm">
      <span className="text-sm font-medium text-muted-foreground">
        {count} selected
      </span>

      {/* Pipeline actions */}
      {actions.map((action) => (
        <Button
          key={action.step}
          size="sm"
          onClick={() => runStep(action.step, action.label)}
          disabled={anyPending}
        >
          {anyPending && <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />}
          {action.label}
        </Button>
      ))}

      {/* Blacklist */}
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button
            size="sm"
            variant="outline"
            disabled={blacklisting}
          >
            <Ban className="mr-1.5 h-3 w-3" />
            Blacklist
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Blacklist {count} business{count > 1 ? "es" : ""}?</AlertDialogTitle>
            <AlertDialogDescription>
              They will be marked as opted out and skipped in future pipeline runs.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => void handleBlacklist()}>
              Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete */}
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button size="sm" variant="destructive" disabled={hardDeleteMutation.isPending}>
            <Trash2 className="mr-1.5 h-3 w-3" />
            Delete
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {count} business{count > 1 ? "es" : ""}?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove the selected businesses from the database.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
