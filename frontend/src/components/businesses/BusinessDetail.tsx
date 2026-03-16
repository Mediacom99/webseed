import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Trash2, ShieldBan, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import {
  useUpdateStatusBusinessesPlaceIdStatusPatch,
  useBlacklistAddBusinessesPlaceIdBlacklistPost,
  useBlacklistRemoveBusinessesPlaceIdBlacklistDelete,
  useDeleteBusinessBusinessesPlaceIdDelete,
} from "@/api/endpoints/businesses/businesses";

const ALL_STATUSES = [
  "searched",
  "enriched",
  "generated",
  "tested",
  "deployed",
  "email_queued",
  "emailed",
  "opted_out",
];

interface BusinessData {
  place_id: string;
  name?: string;
  address?: string;
  phone?: string;
  rating?: number;
  reviews_count?: number;
  lead_score?: number;
  status?: string;
  website_url?: string;
  vercel_url?: string;
  error_detail?: string;
  city?: string;
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
  const [newStatus, setNewStatus] = useState(business.status ?? "");

  const updateStatus = useUpdateStatusBusinessesPlaceIdStatusPatch();
  const blacklistAdd = useBlacklistAddBusinessesPlaceIdBlacklistPost();
  const blacklistRemove = useBlacklistRemoveBusinessesPlaceIdBlacklistDelete();
  const deleteBusiness = useDeleteBusinessBusinessesPlaceIdDelete();

  const isOptedOut = business.status === "opted_out";

  const handleStatusChange = () => {
    if (!newStatus || newStatus === business.status) return;

    updateStatus.mutate(
      { placeId: business.place_id, data: { to: newStatus } },
      {
        onSuccess: () => {
          toast.success(`Status changed to ${newStatus}`);
          onRefresh();
        },
        onError: () => toast.error("Failed to change status"),
      },
    );
  };

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

  const fields: Array<{ label: string; value: unknown }> = [
    { label: "Place ID", value: business.place_id },
    { label: "Name", value: business.name },
    { label: "Address", value: business.address },
    { label: "City", value: business.city },
    { label: "Phone", value: business.phone },
    { label: "Rating", value: business.rating },
    { label: "Reviews", value: business.reviews_count },
    { label: "Lead Score", value: business.lead_score },
    { label: "Website URL", value: business.website_url },
    { label: "Vercel URL", value: business.vercel_url },
    { label: "Error", value: business.error_detail },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>{business.name ?? "Unknown Business"}</CardTitle>
            {business.status && <StatusBadge status={business.status} />}
          </div>
          <div className="flex items-center gap-2">
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
                    This will permanently remove {business.name ?? "this business"}{" "}
                    from the database.
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
        </CardHeader>
        <CardContent>
          <dl className="grid gap-3 md:grid-cols-2">
            {fields.map(({ label, value }) =>
              value != null && value !== "" ? (
                <div key={label}>
                  <dt className="text-sm text-muted-foreground">{label}</dt>
                  <dd className="text-sm font-medium break-all">
                    {String(value)}
                  </dd>
                </div>
              ) : null,
            )}
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Change Status</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <Select value={newStatus} onValueChange={setNewStatus}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              {ALL_STATUSES.map((s) => (
                <SelectItem key={s} value={s}>
                  {s.replace(/_/g, " ")}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={handleStatusChange}
            disabled={
              !newStatus ||
              newStatus === business.status ||
              updateStatus.isPending
            }
          >
            Update
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
