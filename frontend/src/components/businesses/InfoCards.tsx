import { useState } from "react";
import {
  MapPin,
  Phone,
  Mail,
  ExternalLink,
  Star,
  ChevronDown,
  Clock,
  CreditCard,
} from "lucide-react";
import { toast } from "sonner";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useUpdateStatusBusinessesPlaceIdStatusPatch } from "@/api/endpoints/businesses/businesses";
import type { BusinessData } from "./BusinessDetail";

const RESET_STATUSES = [
  "searched",
  "enriched",
  "generated",
  "tested",
  "deployed",
  "email_queued",
  "emailed",
];

interface InfoCardsProps {
  business: BusinessData;
  onRefresh: () => void;
}

export default function InfoCards({ business, onRefresh }: InfoCardsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <ContactCard business={business} />
      <ScoresCard business={business} />
      <BusinessInfoCard business={business} />
      <ReviewsCard business={business} />
      <SiteDeploymentCard business={business} />
      <TestingCard business={business} />
      <ErrorCard business={business} onRefresh={onRefresh} />
      <MetadataCard business={business} />
    </div>
  );
}

function ContactCard({ business }: { business: BusinessData }) {
  const { address, phone, email, maps_url } = business as Record<
    string,
    unknown
  >;
  if (!address && !phone && !email && !maps_url) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Contact</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {address && (
          <div className="flex items-start gap-2">
            <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <span>{address as string}</span>
          </div>
        )}
        {phone && (
          <div className="flex items-center gap-2">
            <Phone className="h-4 w-4 shrink-0 text-muted-foreground" />
            <a
              href={`tel:${phone as string}`}
              className="hover:underline"
            >
              {phone as string}
            </a>
          </div>
        )}
        {email && (email as string) !== "" && (
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 shrink-0 text-muted-foreground" />
            <a
              href={`mailto:${email as string}`}
              className="hover:underline"
            >
              {email as string}
            </a>
          </div>
        )}
        {maps_url && (maps_url as string) !== "" && (
          <div className="flex items-center gap-2">
            <ExternalLink className="h-4 w-4 shrink-0 text-muted-foreground" />
            <a
              href={maps_url as string}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline"
            >
              View on Google Maps
            </a>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ScoresCard({ business }: { business: BusinessData }) {
  const leadScore = business.lead_score;
  const rating = business.rating;
  const reviews = business.reviews;
  const priceLevel = business.price_level as string | undefined;

  if (leadScore == null && rating == null) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Scores</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {leadScore != null && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Lead Score</span>
              <span className="font-semibold">{leadScore}/100</span>
            </div>
            <Progress value={leadScore} className="h-2" />
          </div>
        )}
        {rating != null && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Rating</span>
            <span className="flex items-center gap-1 font-semibold">
              <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
              {rating}
              {reviews != null && (
                <span className="font-normal text-muted-foreground">
                  ({reviews} reviews)
                </span>
              )}
            </span>
          </div>
        )}
        {priceLevel && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Price Level</span>
            <span className="font-semibold">{priceLevel}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function BusinessInfoCard({ business }: { business: BusinessData }) {
  const types = business.types as string[] | undefined;
  const businessStatus = business.business_status as string | undefined;
  const openingHours = business.opening_hours_summary as string | undefined;
  const acceptsCreditCards = business.accepts_credit_cards as
    | boolean
    | undefined;
  const editorialSummary = business.editorial_summary as string | undefined;

  if (
    !types?.length &&
    !businessStatus &&
    !openingHours &&
    acceptsCreditCards == null &&
    !editorialSummary
  )
    return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Business Info</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {types && types.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {types.map((t) => (
              <Badge key={t} variant="secondary" className="text-xs capitalize">
                {t.replace(/_/g, " ")}
              </Badge>
            ))}
          </div>
        )}
        {businessStatus && (
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Status</span>
            <span>{businessStatus}</span>
          </div>
        )}
        {openingHours && (
          <div className="flex items-start gap-2">
            <Clock className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="whitespace-pre-line">{openingHours}</span>
          </div>
        )}
        {acceptsCreditCards != null && (
          <div className="flex items-center gap-2">
            <CreditCard className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span>
              {acceptsCreditCards
                ? "Accepts credit cards"
                : "No credit cards"}
            </span>
          </div>
        )}
        {editorialSummary && (
          <p className="text-muted-foreground italic">{editorialSummary}</p>
        )}
      </CardContent>
    </Card>
  );
}

function ReviewsCard({ business }: { business: BusinessData }) {
  const reviewTexts = business.review_texts as string[] | undefined;
  if (!reviewTexts?.length) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Reviews</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {reviewTexts.map((text, i) => (
          <blockquote
            key={i}
            className="border-l-2 border-muted pl-3 text-sm italic text-muted-foreground"
          >
            {text}
          </blockquote>
        ))}
      </CardContent>
    </Card>
  );
}

function SiteDeploymentCard({ business }: { business: BusinessData }) {
  const vercelUrl = business.vercel_url as string | undefined;
  const emailSentAt = business.email_sent_at as string | undefined;
  if (!vercelUrl) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Site & Deployment</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="flex items-center gap-2">
          <ExternalLink className="h-4 w-4 shrink-0 text-muted-foreground" />
          <a
            href={vercelUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            {vercelUrl}
          </a>
        </div>
        {emailSentAt && emailSentAt !== "" && (
          <div className="text-muted-foreground">
            Email sent: {new Date(emailSentAt).toLocaleString("it-IT")}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TestingCard({ business }: { business: BusinessData }) {
  const iterations = business.test_iterations as number | undefined;
  const issues = business.test_issues as
    | Record<string, unknown>[]
    | undefined;

  if (!iterations || iterations === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Testing</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Iterations</span>
          <span className="font-semibold">{iterations}</span>
        </div>
        {issues && issues.length > 0 && (
          <Collapsible>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-1 px-0 text-xs">
                {issues.length} issue{issues.length > 1 ? "s" : ""}
                <ChevronDown className="h-3 w-3" />
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-1 pt-1">
              {issues.map((issue, i) => (
                <div
                  key={i}
                  className="rounded bg-muted p-2 text-xs"
                >
                  {JSON.stringify(issue)}
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  );
}

function ErrorCard({
  business,
  onRefresh,
}: {
  business: BusinessData;
  onRefresh: () => void;
}) {
  const errorDetail = business.error_detail as string | undefined;
  const status = business.status ?? "";
  const [resetTo, setResetTo] = useState("");
  const updateStatus = useUpdateStatusBusinessesPlaceIdStatusPatch();

  if (!errorDetail || errorDetail === "") return null;

  const handleReset = () => {
    if (!resetTo) return;
    updateStatus.mutate(
      { placeId: business.place_id, data: { to: resetTo } },
      {
        onSuccess: () => {
          toast.success(`Status reset to ${resetTo}`);
          onRefresh();
        },
        onError: () => toast.error("Failed to reset status"),
      },
    );
  };

  return (
    <Card className="border-red-200 dark:border-red-900">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-red-600 dark:text-red-400">
          Error
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div>
          <span className="text-muted-foreground">Failed at: </span>
          <span className="font-medium">{status.replace(/_/g, " ")}</span>
        </div>
        <p className="text-muted-foreground">{errorDetail}</p>
        <div className="flex items-center gap-2">
          <Select value={resetTo} onValueChange={setResetTo}>
            <SelectTrigger className="w-40 h-8 text-xs">
              <SelectValue placeholder="Reset to..." />
            </SelectTrigger>
            <SelectContent>
              {RESET_STATUSES.map((s) => (
                <SelectItem key={s} value={s}>
                  {s.replace(/_/g, " ")}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            size="sm"
            onClick={handleReset}
            disabled={!resetTo || updateStatus.isPending}
          >
            Reset
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function MetadataCard({ business }: { business: BusinessData }) {
  const createdAt = business.created_at as string | undefined;
  const updatedAt = business.updated_at as string | undefined;

  if (!createdAt && !updatedAt) return null;

  const fmt = (d: string) => {
    try {
      return new Date(d).toLocaleString("it-IT");
    } catch {
      return d;
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Metadata</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1 text-sm">
        {createdAt && (
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Created</span>
            <span>{fmt(createdAt)}</span>
          </div>
        )}
        {updatedAt && (
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Updated</span>
            <span>{fmt(updatedAt)}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
