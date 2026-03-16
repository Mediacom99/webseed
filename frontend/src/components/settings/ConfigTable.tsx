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
  useListSettingsSettingsGet,
  useUpdateSettingSettingsKeyPut,
} from "@/api/endpoints/settings/settings";

interface ConfigItem {
  key: string;
  value: string;
  description: string;
}

export default function ConfigTable() {
  const { data } = useListSettingsSettingsGet({ prefix: "config" });
  const updateSetting = useUpdateSettingSettingsKeyPut();

  const [edits, setEdits] = useState<Map<string, string>>(new Map());

  const settings: ConfigItem[] = (data?.data ?? []).map((s) => {
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
        onSuccess: () => toast.success(`Saved ${key}`),
        onError: () => toast.error(`Failed to save ${key}`),
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
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Key</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Description</TableHead>
          <TableHead className="w-20" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {settings.map((setting) => (
          <TableRow key={setting.key}>
            <TableCell className="font-mono text-sm">{setting.key}</TableCell>
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
                  className="max-w-xs"
                />
                {isDirty(setting.key) && (
                  <span className="text-xs text-amber-600">*</span>
                )}
              </div>
            </TableCell>
            <TableCell className="text-sm text-muted-foreground">
              {setting.description}
            </TableCell>
            <TableCell>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleSave(setting.key)}
                disabled={!isDirty(setting.key) || updateSetting.isPending}
              >
                <Save className="h-3 w-3" />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
