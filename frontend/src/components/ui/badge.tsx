import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-full border border-transparent px-2 py-0.5 text-xs font-medium whitespace-nowrap transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 [&>svg]:pointer-events-none [&>svg]:size-3",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground [a&]:hover:bg-primary/90",
        secondary: "bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90",
        destructive:
          "bg-destructive text-white focus-visible:ring-destructive/20 dark:bg-destructive/60 dark:focus-visible:ring-destructive/40 [a&]:hover:bg-destructive/90",
        outline:
          "border-border text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
        ghost: "[a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
        link: "text-primary underline-offset-4 [a&]:hover:underline",
        success:
          "bg-green-100 text-green-700 focus-visible:ring-green-50/20 dark:bg-green-950 dark:text-green-300 dark:focus-visible:ring-green-950/40 [a&]:hover:bg-green-50/90",
        warning:
          "bg-amber-100 text-amber-700 focus-visible:ring-amber-50/20 dark:bg-amber-950 dark:text-amber-300 dark:focus-visible:ring-amber-950/40 [a&]:hover:bg-amber-50/90",
        info: "bg-blue-100 text-blue-700 focus-visible:ring-blue-50/20 dark:bg-blue-950 dark:text-blue-300 dark:focus-visible:ring-blue-950/40 [a&]:hover:bg-blue-50/90",
        danger:
          "bg-red-100 text-red-700 focus-visible:ring-red-50/20 dark:bg-red-950 dark:text-red-300 dark:focus-visible:ring-red-950/40 [a&]:hover:bg-red-50/90",
        critical:
          "bg-rose-100 text-rose-700 focus-visible:ring-rose-50/20 dark:bg-rose-950 dark:text-rose-300 dark:focus-visible:ring-rose-950/40 [a&]:hover:bg-rose-50/90",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

function Badge({
  className,
  variant = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "span";

  return (
    <Comp
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  );
}

export { Badge, badgeVariants };
