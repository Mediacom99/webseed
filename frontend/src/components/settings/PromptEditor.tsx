import { useState, useEffect } from "react";
import { toast } from "sonner";
import { ChevronDown, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  useListSettingsSettingsGet,
  useUpdateSettingSettingsKeyPut,
} from "@/api/endpoints/settings/settings";

interface SettingItem {
  key: string;
  value: string;
  description: string;
}

export default function PromptEditor() {
  const { data } = useListSettingsSettingsGet({ prefix: "prompt" });
  const updateSetting = useUpdateSettingSettingsKeyPut();

  const [edits, setEdits] = useState<Map<string, SettingItem>>(new Map());

  const settings: SettingItem[] = (data?.data ?? []).map((s) => {
    const item = s as Record<string, string>;
    return {
      key: item.key,
      value: item.value,
      description: item.description ?? "",
    };
  });

  // Initialize edits from settings data
  useEffect(() => {
    if (settings.length > 0 && edits.size === 0) {
      const map = new Map<string, SettingItem>();
      for (const s of settings) {
        map.set(s.key, { ...s });
      }
      setEdits(map);
    }
  }, [settings, edits.size]);

  const isDirty = (key: string) => {
    const original = settings.find((s) => s.key === key);
    const edited = edits.get(key);
    if (!original || !edited) return false;
    return (
      original.value !== edited.value ||
      original.description !== edited.description
    );
  };

  const handleSave = (key: string) => {
    const edited = edits.get(key);
    if (!edited) return;

    updateSetting.mutate(
      {
        key,
        data: { value: edited.value, description: edited.description },
      },
      {
        onSuccess: () => toast.success(`Saved ${key}`),
        onError: () => toast.error(`Failed to save ${key}`),
      },
    );
  };

  const updateEdit = (key: string, field: "value" | "description", val: string) => {
    setEdits((prev) => {
      const next = new Map(prev);
      const current = next.get(key);
      if (current) {
        next.set(key, { ...current, [field]: val });
      }
      return next;
    });
  };

  if (settings.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No prompts configured</p>
    );
  }

  return (
    <div className="space-y-3">
      {settings.map((setting) => {
        const edited = edits.get(setting.key);
        const dirty = isDirty(setting.key);

        return (
          <Collapsible key={setting.key}>
            <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md border p-3 text-left hover:bg-muted">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm">{setting.key}</span>
                {dirty && (
                  <span className="text-xs text-amber-600">unsaved</span>
                )}
              </div>
              <ChevronDown className="h-4 w-4" />
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-3 p-3">
              <div className="space-y-1">
                <Label>Value</Label>
                <Textarea
                  rows={8}
                  value={edited?.value ?? setting.value}
                  onChange={(e) =>
                    updateEdit(setting.key, "value", e.target.value)
                  }
                />
              </div>
              <div className="space-y-1">
                <Label>Description</Label>
                <Input
                  value={edited?.description ?? setting.description}
                  onChange={(e) =>
                    updateEdit(setting.key, "description", e.target.value)
                  }
                />
              </div>
              <Button
                size="sm"
                onClick={() => handleSave(setting.key)}
                disabled={!dirty || updateSetting.isPending}
              >
                <Save className="mr-1 h-3 w-3" /> Save
              </Button>
            </CollapsibleContent>
          </Collapsible>
        );
      })}
    </div>
  );
}
