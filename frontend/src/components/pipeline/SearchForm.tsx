import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { usePipelineSearchPipelineSearchPost } from "@/api/endpoints/pipeline/pipeline";

const searchSchema = z.object({
  location: z.string().min(1, "Location is required"),
  query: z.string().min(1, "Query is required"),
  types: z.string().optional(),
  limit: z.number().int().min(1).max(100),
  min_score: z.number().int().min(0).max(60),
  grid_size: z.number().int().min(1).max(10),
});

type SearchFormValues = z.infer<typeof searchSchema>;

interface SearchFormProps {
  onJobStarted: (jobId: string) => void;
}

export default function SearchForm({ onJobStarted }: SearchFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } = useForm<SearchFormValues>({
    resolver: zodResolver(searchSchema) as any,
    defaultValues: {
      location: "",
      query: "",
      types: "",
      limit: 10,
      min_score: 0,
      grid_size: 3,
    },
  });

  const mutation = usePipelineSearchPipelineSearchPost();
  const minScore = watch("min_score");

  const onSubmit = (data: SearchFormValues) => {
    const types = data.types
      ? data.types.split(",").map((t) => t.trim()).filter(Boolean)
      : [];

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
          onJobStarted(jobId);
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
          <Label htmlFor="location">Location *</Label>
          <Input
            id="location"
            placeholder="e.g. Milano, Italia"
            {...register("location")}
          />
          {errors.location && (
            <p className="text-xs text-destructive">{errors.location.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="query">Query *</Label>
          <Input
            id="query"
            placeholder="e.g. ristorante"
            {...register("query")}
          />
          {errors.query && (
            <p className="text-xs text-destructive">{errors.query.message}</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor="types">Types (comma-separated)</Label>
          <Input
            id="types"
            placeholder="e.g. restaurant, cafe"
            {...register("types")}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="limit">Limit</Label>
          <Input
            id="limit"
            type="number"
            min={1}
            max={100}
            {...register("limit", { valueAsNumber: true })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="grid_size">Grid Size</Label>
          <Input
            id="grid_size"
            type="number"
            min={1}
            max={10}
            {...register("grid_size", { valueAsNumber: true })}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Min Score: {minScore}</Label>
        <Slider
          min={0}
          max={60}
          step={1}
          value={[minScore]}
          onValueChange={([val]) => setValue("min_score", val)}
        />
      </div>

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Starting search..." : "Start Search"}
      </Button>
    </form>
  );
}
