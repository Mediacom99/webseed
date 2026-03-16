import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  Trash2,
  ShieldBan,
  ShieldCheck,
  ArrowLeft,
  Loader2,
  Star,
} from "lucide-react";
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
import StatusBadge from "./StatusBadge";
import PipelineGraph from "./PipelineGraph";
import InfoCards from "./InfoCards";
import {
  useBlacklistAddBusinessesPlaceIdBlacklistPost,
  useBlacklistRemoveBusinessesPlaceIdBlacklistDelete,
  useDeleteBusinessBusinessesPlaceIdDelete,
} from "@/api/endpoints/businesses/businesses";
import {
  usePipelineEnrichPipelineEnrichPost,
  usePipelineGeneratePipelineGeneratePost,
  usePipelineTestPipelineTestPost,
  usePipelineDeployPipelineDeployPost,
  usePipelineEmailPipelineEmailPost,
} from "@/api/endpoints/pipeline/pipeline";

const STATUS_TO_NEXT: Record<
  string,
  { label: string; step: string } | undefined
> = {
  searched: { label: "Enrich", step: "enrich" },
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

const NO_ACTION_STATUSES = new Set([
  "emailed",
  "email_queued",
  "opted_out",
]);

const RUNNING_STATUSES = new Set([
  "running_enrich",
  "running_generate",
  "running_test",
  "running_deploy",
  "running_email",
]);

export interface BusinessData {
  place_id: string;
  name?: string;
  address?: string;
  phone?: string;
  rating?: number;
  reviews?: number;
  lead_score?: number;
  status?: string;
  primary_type?: string;
  vercel_url?: string;
  error_detail?: string;
  [key: string]: unknown;
}

interface BusinessDetailProps {
  business: BusinessData;
  onRefresh: () => void;
}

export default function BusinessDetail({
  business,
  onRefresh,
}: BusinessDetailProps) {
  const navigate = useNavigate();
  const status = business.status ?? "searched";
  const isOptedOut = status === "opted_out";
  const isRunning = RUNNING_STATUSES.has(status);
  const nextAction = STATUS_TO_NEXT[status];
  const showAction = !NO_ACTION_STATUSES.has(status) && !isRunning;

  const blacklistAdd = useBlacklistAddBusinessesPlaceIdBlacklistPost();
  const blacklistRemove =
    useBlacklistRemoveBusinessesPlaceIdBlacklistDelete();
  const deleteBusiness = useDeleteBusinessBusinessesPlaceIdDelete();

  const enrichMutation = usePipelineEnrichPipelineEnrichPost();
  const generateMutation = usePipelineGeneratePipelineGeneratePost();
  const testMutation = usePipelineTestPipelineTestPost();
  const deployMutation = usePipelineDeployPipelineDeployPost();
  const emailMutation = usePipelineEmailPipelineEmailPost();

  const handleBlacklistToggle = () => {
    if (isOptedOut) {
      blacklistRemove.mutate(
        { placeId: business.place_id },
        {
          onSuccess: () => {
            toast.success("Removed from blacklist");
            onRefresh();
          },
          onError: () => toast.error("Failed to remove from blacklist"),
        },
      );
    } else {
      blacklistAdd.mutate(
        { placeId: business.place_id },
        {
          onSuccess: () => {
            toast.success("Added to blacklist");
            onRefresh();
          },
          onError: () => toast.error("Failed to add to blacklist"),
        },
      );
    }
  };

  const handleDelete = () => {
    deleteBusiness.mutate(
      { placeId: business.place_id },
      {
        onSuccess: () => {
          toast.success("Business deleted");
          navigate("/businesses");
        },
        onError: () => toast.error("Failed to delete business"),
      },
    );
  };

  const handleNextStep = () => {
    if (!nextAction) return;
    const data = { data: { place_ids: [business.place_id] } };
    const opts = {
      onSuccess: () => {
        toast.success(`${nextAction.label} started`);
        onRefresh();
      },
      onError: () => toast.error(`${nextAction.label} failed`),
    };

    switch (nextAction.step) {
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

  const anyPending =
    enrichMutation.isPending ||
    generateMutation.isPending ||
    testMutation.isPending ||
    deployMutation.isPending ||
    emailMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <button
          type="button"
          className="mb-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          onClick={() => navigate("/businesses")}
        >
          <ArrowLeft className="h-4 w-4" />
          Businesses
        </button>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold">
            {business.name ?? "Unknown Business"}
          </h1>
          <StatusBadge status={status} />
          {business.primary_type && (
            <span className="text-sm capitalize text-muted-foreground">
              {(business.primary_type as string).replace(/_/g, " ")}
            </span>
          )}
          {business.rating != null && (
            <span className="flex items-center gap-1 text-sm">
              <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
              {business.rating}
              {business.reviews != null && (
                <span className="text-muted-foreground">
                  ({business.reviews})
                </span>
              )}
            </span>
          )}
        </div>
      </div>

      {/* Pipeline graph */}
      <PipelineGraph status={status} />

      {/* Actions */}
      <div className="flex flex-wrap items-center gap-2">
        {isRunning && (
          <Button disabled>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Running...
          </Button>
        )}
        {showAction && nextAction && (
          <Button onClick={handleNextStep} disabled={anyPending}>
            {anyPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {nextAction.label}
          </Button>
        )}
        <Button
          variant={isOptedOut ? "default" : "outline"}
          size="sm"
          onClick={handleBlacklistToggle}
        >
          {isOptedOut ? (
            <>
              <ShieldCheck className="mr-1 h-4 w-4" /> Unblacklist
            </>
          ) : (
            <>
              <ShieldBan className="mr-1 h-4 w-4" /> Blacklist
            </>
          )}
        </Button>
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="destructive" size="sm">
              <Trash2 className="mr-1 h-4 w-4" /> Delete
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete business?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently remove{" "}
                {business.name ?? "this business"} from the database.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleDelete}>
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      {/* Info cards */}
      <InfoCards business={business} onRefresh={onRefresh} />
    </div>
  );
}
