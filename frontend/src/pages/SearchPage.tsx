import { Search } from "lucide-react";

export default function SearchPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Search</h1>
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
        <Search className="mb-4 h-12 w-12 text-muted-foreground" />
        <p className="text-lg text-muted-foreground">Search coming soon</p>
      </div>
    </div>
  );
}
