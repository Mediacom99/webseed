import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ChevronDown, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { usePipelineSearchPipelineSearchPost } from "@/api/endpoints/pipeline/pipeline";
import TypesMultiSelect from "./TypesMultiSelect";

const searchSchema = z.object({
  location: z.string().min(1, "Location is required"),
  query: z.string().min(1, "Query is required"),
  limit: z.number().int().min(1).max(100),
  min_score: z.number().int().min(0).max(60),
  grid_size: z.number().int().min(1).max(10),
});

type SearchFormValues = z.infer<typeof searchSchema>;

interface SearchFormProps {
  onJobStarted?: (jobId: string) => void;
}

export default function SearchForm({ onJobStarted }: SearchFormProps) {
  const [types, setTypes] = useState<string[]>([]);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } = useForm<SearchFormValues>({
    resolver: zodResolver(searchSchema) as any,
    defaultValues: {
      location: "",
      query: "",
      limit: 10,
      min_score: 0,
      grid_size: 3,
    },
  });

  const mutation = usePipelineSearchPipelineSearchPost();

  const onSubmit = (data: SearchFormValues) => {
    mutation.mutate(
      {
        data: {
          location: data.location,
          query: data.query,
          types,
          limit: data.limit,
          min_score: data.min_score,
          grid_size: data.grid_size,
        },
      },
      {
        onSuccess: (response) => {
          const resp = response as { data: { job_id: string } };
          const jobId = resp.data.job_id;
          toast.success(`Search started (job: ${jobId.slice(0, 8)}...)`);
          onJobStarted?.(jobId);
        },
        onError: (error) => {
          toast.error(
            `Search failed: ${error instanceof Error ? error.message : "Unknown error"}`,
          );
        },
      },
    );
  };

  return (
    <form
      onSubmit={(e) => void handleSubmit(onSubmit)(e)}
      className="space-y-4"
    >
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="search-location">Location *</Label>
          <Input
            id="search-location"
            placeholder="e.g. Milano, Italia"
            {...register("location")}
          />
          {errors.location && (
            <p className="text-xs text-destructive">
              {errors.location.message}
            </p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="search-query">Query *</Label>
          <Input
            id="search-query"
            placeholder="e.g. ristorante"
            {...register("query")}
          />
          {errors.query && (
            <p className="text-xs text-destructive">{errors.query.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Business Types</Label>
        <TypesMultiSelect value={types} onChange={setTypes} />
      </div>

      <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
        <CollapsibleTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="gap-1 px-0 text-muted-foreground"
          >
            Advanced options
            <ChevronDown
              className={`h-4 w-4 transition-transform ${advancedOpen ? "rotate-180" : ""}`}
            />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-2">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="search-limit">Limit</Label>
              <Input
                id="search-limit"
                type="number"
                min={1}
                max={100}
                {...register("limit", { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="search-min-score">Min Score</Label>
              <Input
                id="search-min-score"
                type="number"
                min={0}
                max={60}
                {...register("min_score", { valueAsNumber: true })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="search-grid-size">Grid Size</Label>
              <Input
                id="search-grid-size"
                type="number"
                min={1}
                max={10}
                {...register("grid_size", { valueAsNumber: true })}
              />
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending && (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        )}
        {mutation.isPending ? "Searching..." : "Start Search"}
      </Button>
    </form>
  );
}
