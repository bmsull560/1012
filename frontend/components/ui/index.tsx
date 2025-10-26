// Stub components for missing UI elements
import * as React from "react"
import { cn } from "@/utils"

// ScrollArea
export const ScrollArea = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => (
  <div ref={ref} className={cn("overflow-auto", className)} {...props}>
    {children}
  </div>
))
ScrollArea.displayName = "ScrollArea"

// Separator
export const Separator = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { orientation?: 'horizontal' | 'vertical' }
>(({ className, orientation = 'horizontal', ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "shrink-0 bg-border",
      orientation === 'vertical' ? 'h-full w-[1px]' : 'h-[1px] w-full',
      className
    )}
    {...props}
  />
))
Separator.displayName = "Separator"

// Progress
export const Progress = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value?: number }
>(({ className, value = 0, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("relative h-4 w-full overflow-hidden rounded-full bg-secondary", className)}
    {...props}
  >
    <div
      className="h-full w-full flex-1 bg-primary transition-all"
      style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
    />
  </div>
))
Progress.displayName = "Progress"

// Avatar
export const Avatar = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full", className)}
    {...props}
  />
))
Avatar.displayName = "Avatar"

export const AvatarImage = React.forwardRef<
  HTMLImageElement,
  React.ImgHTMLAttributes<HTMLImageElement>
>(({ className, ...props }, ref) => (
  <img
    ref={ref}
    className={cn("aspect-square h-full w-full", className)}
    {...props}
  />
))
AvatarImage.displayName = "AvatarImage"

export const AvatarFallback = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex h-full w-full items-center justify-center rounded-full bg-muted",
      className
    )}
    {...props}
  />
))
AvatarFallback.displayName = "AvatarFallback"

// Label
export const Label = React.forwardRef<
  HTMLLabelElement,
  React.LabelHTMLAttributes<HTMLLabelElement>
>(({ className, ...props }, ref) => (
  <label
    ref={ref}
    className={cn(
      "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
      className
    )}
    {...props}
  />
))
Label.displayName = "Label"

// Slider
export const Slider = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value?: number[]; onValueChange?: (value: number[]) => void }
>(({ className, value = [50], ...props }, ref) => (
  <div
    ref={ref}
    className={cn("relative flex w-full touch-none select-none items-center", className)}
    {...props}
  >
    <div className="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
      <div className="absolute h-full bg-primary" style={{ width: `${value[0]}%` }} />
    </div>
  </div>
))
Slider.displayName = "Slider"

// Switch
export const Switch = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { checked?: boolean; onCheckedChange?: (checked: boolean) => void }
>(({ className, checked = false, ...props }, ref) => (
  <button
    ref={ref}
    className={cn(
      "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
      checked ? "bg-primary" : "bg-input",
      className
    )}
    {...props}
  >
    <span
      className={cn(
        "pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform",
        checked ? "translate-x-5" : "translate-x-0"
      )}
    />
  </button>
))
Switch.displayName = "Switch"

// Select components
export const Select = ({ children, ...props }: any) => <div {...props}>{children}</div>
export const SelectTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ className, children, ...props }, ref) => (
  <button
    ref={ref}
    className={cn(
      "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    {...props}
  >
    {children}
  </button>
))
SelectTrigger.displayName = "SelectTrigger"

export const SelectContent = ({ children, ...props }: any) => (
  <div className="relative z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md" {...props}>
    {children}
  </div>
)
export const SelectItem = ({ children, ...props }: any) => (
  <div className="relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground" {...props}>
    {children}
  </div>
)
export const SelectValue = ({ placeholder = "Select...", ...props }: any) => <span {...props}>{placeholder}</span>

// Tooltip components
export const TooltipProvider = ({ children }: any) => <>{children}</>
export const Tooltip = ({ children }: any) => <>{children}</>
export const TooltipTrigger = ({ children }: any) => <>{children}</>
export const TooltipContent = ({ children }: any) => (
  <div className="z-50 overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md">
    {children}
  </div>
)

// Dialog components
export const Dialog = ({ children }: any) => <>{children}</>
export const DialogTrigger = ({ children }: any) => <>{children}</>
export const DialogContent = ({ children }: any) => (
  <div className="fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg">
    {children}
  </div>
)
export const DialogHeader = ({ children }: any) => <div className="flex flex-col space-y-1.5 text-center sm:text-left">{children}</div>
export const DialogTitle = ({ children }: any) => <h2 className="text-lg font-semibold leading-none tracking-tight">{children}</h2>
export const DialogDescription = ({ children }: any) => <p className="text-sm text-muted-foreground">{children}</p>
export const DialogFooter = ({ children }: any) => (
  <div className="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2">
    {children}
  </div>
)
export const DialogClose = ({ children, ...props }: any) => <button {...props}>{children}</button>

// Alert components
export const Alert = ({ children, className, ...props }: any) => (
  <div className={cn("relative w-full rounded-lg border p-4", className)} {...props}>
    {children}
  </div>
)
export const AlertTitle = ({ children }: any) => <h5 className="mb-1 font-medium leading-none tracking-tight">{children}</h5>
export const AlertDescription = ({ children }: any) => <div className="text-sm [&_p]:leading-relaxed">{children}</div>

// Popover components
export const Popover = ({ children }: any) => <>{children}</>
export const PopoverTrigger = ({ children }: any) => <>{children}</>
export const PopoverContent = ({ children }: any) => (
  <div className="z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none">
    {children}
  </div>
)

// Command components
export const Command = ({ children }: any) => <div className="flex h-full w-full flex-col overflow-hidden rounded-md bg-popover text-popover-foreground">{children}</div>
export const CommandInput = (props: any) => <input className="flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground" {...props} />
export const CommandList = ({ children }: any) => <div className="max-h-[300px] overflow-y-auto overflow-x-hidden">{children}</div>
export const CommandEmpty = ({ children }: any) => <div className="py-6 text-center text-sm">{children}</div>
export const CommandGroup = ({ children }: any) => <div className="overflow-hidden p-1 text-foreground">{children}</div>
export const CommandItem = ({ children }: any) => <div className="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none">{children}</div>

// DropdownMenu components
export const DropdownMenu = ({ children }: any) => <div className="relative inline-block text-left">{children}</div>
export const DropdownMenuTrigger = ({ children, ...props }: any) => <button {...props}>{children}</button>
export const DropdownMenuContent = ({ children, ...props }: any) => (
  <div className="z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md" {...props}>
    {children}
  </div>
)
export const DropdownMenuItem = ({ children, ...props }: any) => (
  <div className="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50" {...props}>
    {children}
  </div>
)
export const DropdownMenuLabel = ({ children, ...props }: any) => (
  <div className="px-2 py-1.5 text-sm font-semibold" {...props}>{children}</div>
)
export const DropdownMenuSeparator = ({ ...props }: any) => (
  <div className="-mx-1 my-1 h-px bg-muted" {...props} />
)
export const DropdownMenuGroup = ({ children, ...props }: any) => <div {...props}>{children}</div>
export const DropdownMenuPortal = ({ children, ...props }: any) => <>{children}</>
export const DropdownMenuSub = ({ children, ...props }: any) => <>{children}</>
export const DropdownMenuSubContent = ({ children, ...props }: any) => (
  <div className="z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md" {...props}>
    {children}
  </div>
)
export const DropdownMenuSubTrigger = ({ children, ...props }: any) => <button {...props}>{children}</button>
export const DropdownMenuRadioGroup = ({ children, ...props }: any) => <div {...props}>{children}</div>
export const DropdownMenuRadioItem = ({ children, ...props }: any) => (
  <div className="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground" {...props}>
    {children}
  </div>
)
export const DropdownMenuCheckboxItem = ({ children, ...props }: any) => (
  <div className="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground" {...props}>
    {children}
  </div>
)
export const DropdownMenuShortcut = ({ children, ...props }: any) => <span className="ml-auto text-xs tracking-widest opacity-60" {...props}>{children}</span>

// Collapsible components
export const Collapsible = ({ children }: any) => <>{children}</>
export const CollapsibleTrigger = ({ children }: any) => <>{children}</>
export const CollapsibleContent = ({ children }: any) => <>{children}</>
