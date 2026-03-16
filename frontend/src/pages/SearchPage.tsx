import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import SearchForm from "@/components/search/SearchForm";

export default function SearchPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Search</h1>
      <Card>
        <CardHeader>
          <CardTitle>Find Businesses</CardTitle>
        </CardHeader>
        <CardContent>
          <SearchForm />
        </CardContent>
      </Card>
    </div>
  );
}
