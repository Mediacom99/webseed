import { useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Link } from "react-router-dom";
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
import { usePipelineEnrichPipelineEnrichPost } from "@/api/endpoints/pipeline/pipeline";
import { useBlacklistAddBusinessesPlaceIdBlacklistPost } from "@/api/endpoints/businesses/businesses";

interface SearchActionBarProps {
  selectedIds: Set<string>;
  onActionComplete: () => void;
}

export default function SearchActionBar({
  selectedIds,
  onActionComplete,
}: SearchActionBarProps) {
  const [blacklisting, setBlacklisting] = useState(false);
  const enrichMutation = usePipelineEnrichPipelineEnrichPost();
  const blacklistMutation = useBlacklistAddBusinessesPlaceIdBlacklistPost();

  const count = selectedIds.size;
  if (count === 0) return null;

  const handleEnrich = () => {
    enrichMutation.mutate(
      { data: { place_ids: Array.from(selectedIds) } },
      {
        onSuccess: () => {
          toast.success(
            <div>
              {count} business{count > 1 ? "es" : ""} sent to enrich —{" "}
              <Link
                to="/businesses?status=enriched"
                className="underline font-medium"
              >
                View in Businesses
              </Link>
            </div>,
          );
          onActionComplete();
        },
        onError: (error) => {
          toast.error(
            `Enrich failed: ${error instanceof Error ? error.message : "Unknown error"}`,
          );
        },
      },
    );
  };

  const handleBlacklist = async () => {
    setBlacklisting(true);
    const ids = Array.from(selectedIds);
    try {
      for (const id of ids) {
        await blacklistMutation.mutateAsync({ placeId: id });
      }
      toast.success(`${count} business${count > 1 ? "es" : ""} blacklisted`);
      onActionComplete();
    } catch (error) {
      toast.error(
        `Blacklist failed: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setBlacklisting(false);
    }
  };

  return (
    <div className="sticky bottom-0 flex items-center gap-3 rounded-lg border bg-background p-3 shadow-sm">
      <span className="text-sm text-muted-foreground">
        {count} selected
      </span>
      <Button
        size="sm"
        onClick={handleEnrich}
        disabled={enrichMutation.isPending}
      >
        {enrichMutation.isPending && (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        )}
        Enrich Selected
      </Button>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button size="sm" variant="destructive" disabled={blacklisting}>
            {blacklisting && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Blacklist Selected
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Blacklist businesses?</AlertDialogTitle>
            <AlertDialogDescription>
              This will mark {count} business{count > 1 ? "es" : ""} as opted
              out. They will be skipped in future pipeline runs.
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
    </div>
  );
}
