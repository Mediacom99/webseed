import BusinessTable from "@/components/businesses/BusinessTable";

export default function BusinessesPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Businesses</h1>
      <BusinessTable />
    </div>
  );
}
