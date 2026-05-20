import * as React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

const cn = (...inputs: any[]) => twMerge(clsx(inputs));

const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'default' | 'outline' | 'ghost' }
>(({ className, variant = 'default', ...props }, ref) => {
  const variants = {
    default: "bg-gradient-to-r from-cyan-400 to-purple-500 text-white hover:opacity-90",
    outline: "border border-gray-700 text-white hover:border-cyan-400",
    ghost: "text-gray-400 hover:text-white hover:bg-gray-800",
  };

  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-xl px-6 py-3 text-sm font-medium transition-all duration-200 disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    />
  );
});
Button.displayName = "Button";

export { Button };
