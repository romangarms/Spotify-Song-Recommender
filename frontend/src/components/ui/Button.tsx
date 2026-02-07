import type { ButtonHTMLAttributes } from 'react';
import { forwardRef } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  as?: 'button' | 'a';
  href?: string;
  target?: string;
  rel?: string;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-spotify-green text-white hover:bg-spotify-green-light hover:scale-[1.02] active:scale-[0.98]',
  secondary:
    'bg-spotify-light-gray text-white border border-gray-600 hover:border-spotify-green',
  ghost: 'text-spotify-text hover:text-white bg-transparent',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-6 py-3 text-base',
  lg: 'px-8 py-4 text-lg',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      className = '',
      disabled,
      children,
      as = 'button',
      href,
      target,
      rel,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'font-semibold rounded-full transition-all duration-200 inline-flex items-center justify-center cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none';

    const combinedClassName = `${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`;

    if (as === 'a' && href) {
      return (
        <a
          href={href}
          target={target}
          rel={rel}
          className={combinedClassName}
        >
          {isLoading ? (
            <>
              <span className="animate-spin mr-2">⟳</span>
              Loading...
            </>
          ) : (
            children
          )}
        </a>
      );
    }

    return (
      <button
        ref={ref}
        className={combinedClassName}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <span className="animate-spin mr-2">⟳</span>
            Loading...
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
