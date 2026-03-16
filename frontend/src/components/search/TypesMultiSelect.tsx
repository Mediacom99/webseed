import { useState, useRef, useEffect } from "react";
import { Check, ChevronDown, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface TypeGroup {
  label: string;
  types: string[];
}

const TYPE_GROUPS: TypeGroup[] = [
  {
    label: "Food & Drink",
    types: [
      "restaurant", "italian_restaurant", "pizza_restaurant", "meal_takeaway",
      "meal_delivery", "cafe", "coffee_shop", "bakery", "bar", "ice_cream_shop",
      "seafood_restaurant", "steak_house", "sushi_restaurant", "brunch_restaurant",
      "chinese_restaurant", "greek_restaurant", "indian_restaurant", "indonesian_restaurant",
      "japanese_restaurant", "korean_restaurant", "lebanese_restaurant",
      "mediterranean_restaurant", "middle_eastern_restaurant", "ramen_restaurant",
      "fast_food_restaurant",
    ],
  },
  {
    label: "Beauty & Wellness",
    types: ["hair_salon", "beauty_salon", "barber_shop", "spa", "nail_salon"],
  },
  {
    label: "Health",
    types: ["dentist", "dental_clinic", "doctor", "physiotherapist", "veterinary_care"],
  },
  {
    label: "Automotive",
    types: ["car_repair", "car_wash"],
  },
  {
    label: "Accommodation",
    types: ["hotel", "bed_and_breakfast", "lodging", "guest_house", "motel", "hostel"],
  },
  {
    label: "Fitness",
    types: ["gym", "fitness_center"],
  },
  {
    label: "Retail",
    types: [
      "store", "clothing_store", "shoe_store", "jewelry_store", "pet_store",
      "furniture_store", "electronics_store", "book_store", "gift_shop",
      "florist", "bicycle_store",
    ],
  },
  {
    label: "Services",
    types: ["laundry", "tailor", "locksmith", "plumber", "electrician", "roofing_contractor"],
  },
];

function formatType(type: string): string {
  return type.replace(/_/g, " ");
}

interface TypesMultiSelectProps {
  value: string[];
  onChange: (types: string[]) => void;
}

export default function TypesMultiSelect({
  value,
  onChange,
}: TypesMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on outside click or Escape
  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const toggle = (type: string) => {
    if (value.includes(type)) {
      onChange(value.filter((t) => t !== type));
    } else {
      onChange([...value, type]);
    }
  };

  const remove = (type: string) => {
    onChange(value.filter((t) => t !== type));
  };

  return (
    <div ref={containerRef} className="relative">
      <Button
        type="button"
        variant="outline"
        className="w-full justify-between"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-label="Select business types"
      >
        <span className="truncate text-left">
          {value.length === 0
            ? "Select types..."
            : `${value.length} type${value.length > 1 ? "s" : ""} selected`}
        </span>
        <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </Button>

      {/* Selected chips */}
      {value.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {value.map((type) => (
            <Badge key={type} variant="secondary" className="gap-1 text-xs">
              {formatType(type)}
              <button
                type="button"
                className="ml-0.5 rounded-full hover:bg-muted"
                onClick={() => remove(type)}
                aria-label={`Remove ${formatType(type)}`}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      {/* Dropdown */}
      {open && (
        <div className="absolute z-50 mt-1 max-h-72 w-full overflow-auto rounded-md border bg-popover p-1 shadow-md">
          {TYPE_GROUPS.map((group) => (
            <div key={group.label}>
              <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                {group.label}
              </div>
              {group.types.map((type) => {
                const selected = value.includes(type);
                return (
                  <button
                    key={type}
                    type="button"
                    className={cn(
                      "flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent",
                      selected && "bg-accent",
                    )}
                    onClick={() => toggle(type)}
                  >
                    <span
                      className={cn(
                        "flex h-4 w-4 items-center justify-center rounded-sm border",
                        selected
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-muted-foreground",
                      )}
                    >
                      {selected && <Check className="h-3 w-3" />}
                    </span>
                    <span className="capitalize">{formatType(type)}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
