import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  useListSettingsSettingsGet,
  useUpdateSettingSettingsKeyPut,
} from "@/api/endpoints/settings/settings";

interface ConfigItem {
  key: string;
  value: string;
  description: string;
}

function humanize(key: string): string {
  return key
    .replace(/^config\./, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ConfigTable() {
  const { data } = useListSettingsSettingsGet({ prefix: "config" });
  const updateSetting = useUpdateSettingSettingsKeyPut();

  const [edits, setEdits] = useState<Map<string, string>>(new Map());
  const [focused, setFocused] = useState<string | null>(null);

  const rawData = Array.isArray(data?.data) ? data.data : [];
  const settings: ConfigItem[] = rawData.map((s) => {
    const item = s as Record<string, string>;
    return {
      key: item.key,
      value: item.value,
      description: item.description ?? "",
    };
  });

  // Initialize edits
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
        onSuccess: () => toast.success(`Saved ${humanize(key)}`),
        onError: () => toast.error(`Failed to save ${humanize(key)}`),
      },
    );
  };

  if (settings.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No config values configured
      </p>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Setting</TableHead>
            <TableHead>Value</TableHead>
            <TableHead className="w-16" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {settings.map((setting) => {
            const dirty = isDirty(setting.key);
            return (
              <TableRow key={setting.key}>
                <TableCell>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-sm font-medium cursor-help">
                        {humanize(setting.key)}
                      </span>
                    </TooltipTrigger>
                    {setting.description && (
                      <TooltipContent side="right" className="max-w-xs">
                        <p className="text-xs">{setting.description}</p>
                      </TooltipContent>
                    )}
                  </Tooltip>
                  {focused === setting.key && setting.description && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      {setting.description}
                    </p>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Input
                      value={edits.get(setting.key) ?? setting.value}
                      onChange={(e) =>
                        setEdits((prev) => {
                          const next = new Map(prev);
                          next.set(setting.key, e.target.value);
                          return next;
                        })
                      }
                      onFocus={() => setFocused(setting.key)}
                      onBlur={() => setFocused(null)}
                      className="max-w-xs"
                    />
                    {dirty && (
                      <span className="h-2 w-2 shrink-0 rounded-full bg-amber-500" />
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleSave(setting.key)}
                    disabled={!dirty || updateSetting.isPending}
                  >
                    <Save className="h-3 w-3" />
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
