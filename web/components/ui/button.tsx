import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";

type Variant = "primary" | "secondary" | "tab" | "tabActive";

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-blue-700 text-white shadow-sm hover:bg-blue-800 focus-visible:outline-blue-700 px-4 py-2.5",
  secondary:
    "border border-zinc-300 bg-white text-zinc-900 shadow-sm hover:bg-zinc-50 focus-visible:outline-zinc-500 px-4 py-2.5",
  tab: "bg-zinc-100 text-zinc-800 hover:bg-zinc-200 focus-visible:outline-zinc-500 px-3 py-2",
  tabActive: "bg-blue-700 text-white shadow-sm focus-visible:outline-blue-700 px-3 py-2",
};

const baseClasses =
  "flex w-full items-center justify-center gap-2 rounded-lg text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:pointer-events-none disabled:opacity-50 sm:inline-flex sm:w-auto";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  children: ReactNode;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", className = "", type = "button", children, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
});

type ButtonLinkProps = {
  href: string;
  variant?: Variant;
  className?: string;
  children: ReactNode;
  download?: boolean | string;
  target?: string;
  rel?: string;
};

export function ButtonLink({
  href,
  variant = "secondary",
  className = "",
  children,
  download,
  target,
  rel,
}: ButtonLinkProps) {
  return (
    <a
      href={href}
      download={download}
      target={target}
      rel={rel}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
    >
      {children}
    </a>
  );
}

export function PageSection({
  title,
  titleAccessory,
  icon,
  showDivider = true,
  children,
}: {
  title: string;
  titleAccessory?: ReactNode;
  icon?: ReactNode;
  showDivider?: boolean;
  children: ReactNode;
}) {
  return (
    <section
      className={`mt-5 first:mt-0 ${showDivider ? "border-t border-zinc-200 pt-4 first:border-t-0 first:pt-0" : ""}`}
    >
      <div className="flex items-center gap-2">
        {icon}
        <h2 className="text-lg font-semibold tracking-tight text-zinc-900">{title}</h2>
        {titleAccessory}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}
