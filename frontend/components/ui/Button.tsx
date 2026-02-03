'use client'

import { ButtonHTMLAttributes, FC } from 'react'
import { motion } from 'framer-motion'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
}

export const Button: FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  className = '',
  ...props
}) => {
  const variants = {
    primary: 'bg-gradient-to-r from-brand-primary-600 to-brand-secondary-600 hover:from-brand-primary-700 hover:to-brand-secondary-700 shadow-lg shadow-brand-primary-500/30 text-white',
    secondary: 'bg-surface-medium hover:bg-surface-light border-2 border-gray-700 hover:border-gray-600 text-white',
    danger: 'bg-red-600 hover:bg-red-700 shadow-lg shadow-red-500/30 text-white',
    ghost: 'hover:bg-white/10 border-2 border-transparent hover:border-white/20 text-white',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  }

  const { onDrag, onDragStart, onDragEnd, ...buttonProps } = props as any

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`
        rounded-lg font-semibold transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-brand-primary-500 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
      disabled={loading}
      {...buttonProps}
    >
      {loading ? '...' : children}
    </motion.button>
  )
}
