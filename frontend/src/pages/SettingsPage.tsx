import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PromptEditor from "@/components/settings/PromptEditor";
import ConfigTable from "@/components/settings/ConfigTable";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <Tabs defaultValue="prompts">
        <TabsList>
          <TabsTrigger value="prompts">Prompts</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
        </TabsList>
        <TabsContent value="prompts" className="mt-4">
          <PromptEditor />
        </TabsContent>
        <TabsContent value="config" className="mt-4">
          <ConfigTable />
        </TabsContent>
      </Tabs>
    </div>
  );
}
