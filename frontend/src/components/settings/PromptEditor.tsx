import { useState, useEffect, useMemo } from "react";
import { toast } from "sonner";
import { ChevronDown, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
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

const PROMPT_GROUPS = [
  {
    label: "Site Generation",
    prefixes: ["prompt.site_gen"],
  },
  {
    label: "Code Review",
    prefixes: ["prompt.code_review"],
  },
  {
    label: "Visual Test",
    prefixes: ["prompt.visual_test"],
  },
  {
    label: "Fix HTML",
    prefixes: ["prompt.fix_html"],
  },
  {
    label: "Email Generation",
    prefixes: ["prompt.email_gen"],
  },
];

function groupPrompts(
  settings: SettingItem[],
): { label: string; items: SettingItem[] }[] {
  const groups: { label: string; items: SettingItem[] }[] = [];
  const used = new Set<string>();

  for (const group of PROMPT_GROUPS) {
    const items = settings.filter((s) =>
      group.prefixes.some((p) => s.key.startsWith(p)),
    );
    for (const item of items) used.add(item.key);
    if (items.length > 0) {
      groups.push({ label: group.label, items });
    }
  }

  // Catch any ungrouped prompts
  const ungrouped = settings.filter((s) => !used.has(s.key));
  if (ungrouped.length > 0) {
    groups.push({ label: "Other", items: ungrouped });
  }

  return groups;
}

export default function PromptEditor() {
  const { data } = useListSettingsSettingsGet({ prefix: "prompt" });
  const updateSetting = useUpdateSettingSettingsKeyPut();

  const [edits, setEdits] = useState<Map<string, string>>(new Map());

  const rawData = Array.isArray(data?.data) ? data.data : [];
  const settings: SettingItem[] = rawData.map((s) => {
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
      const map = new Map<string, string>();
      for (const s of settings) {
        map.set(s.key, s.value);
      }
      setEdits(map);
    }
  }, [settings, edits.size]);

  const isDirty = (key: string) => {
    const original = settings.find((s) => s.key === key);
    const edited = edits.get(key);
    return original && edited !== undefined && original.value !== edited;
  };

  const handleSave = (key: string) => {
    const value = edits.get(key);
    if (value === undefined) return;

    updateSetting.mutate(
      { key, data: { value } },
      {
        onSuccess: () => toast.success(`Saved ${key}`),
        onError: () => toast.error(`Failed to save ${key}`),
      },
    );
  };

  const updateEdit = (key: string, val: string) => {
    setEdits((prev) => {
      const next = new Map(prev);
      next.set(key, val);
      return next;
    });
  };

  const groups = useMemo(() => groupPrompts(settings), [settings]);

  if (settings.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No prompts configured</p>
    );
  }

  return (
    <div className="space-y-4">
      {groups.map((group) => {
        const unsavedCount = group.items.filter((i) =>
          isDirty(i.key),
        ).length;

        return (
          <Collapsible key={group.label} defaultOpen>
            <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md border p-3 text-left hover:bg-muted">
              <div className="flex items-center gap-2">
                <span className="font-medium">{group.label}</span>
                <span className="text-xs text-muted-foreground">
                  ({group.items.length})
                </span>
                {unsavedCount > 0 && (
                  <span className="rounded-full bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700">
                    {unsavedCount} unsaved
                  </span>
                )}
              </div>
              <ChevronDown className="h-4 w-4" />
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-3 pt-2">
              {group.items.map((setting) => {
                const dirty = isDirty(setting.key);
                return (
                  <div
                    key={setting.key}
                    className="space-y-2 rounded-md border p-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm">{setting.key}</span>
                        {dirty && (
                          <span className="h-2 w-2 rounded-full bg-amber-500" />
                        )}
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleSave(setting.key)}
                        disabled={!dirty || updateSetting.isPending}
                      >
                        <Save className="mr-1 h-3 w-3" /> Save
                      </Button>
                    </div>
                    {setting.description && (
                      <p className="text-xs text-muted-foreground">
                        {setting.description}
                      </p>
                    )}
                    <Textarea
                      rows={6}
                      value={edits.get(setting.key) ?? setting.value}
                      onChange={(e) =>
                        updateEdit(setting.key, e.target.value)
                      }
                      className="font-mono text-xs"
                    />
                  </div>
                );
              })}
            </CollapsibleContent>
          </Collapsible>
        );
      })}
    </div>
  );
}
