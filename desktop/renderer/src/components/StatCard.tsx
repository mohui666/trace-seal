interface StatCardProps {
  label: string;
  value: string | number;
  variant?: 'default' | 'danger' | 'warning' | 'success';
}

const variantStyles = {
  default: 'border-gray-800',
  danger: 'border-red-800 bg-red-950/20',
  warning: 'border-yellow-800 bg-yellow-950/20',
  success: 'border-green-800 bg-green-950/20',
};

export function StatCard({ label, value, variant = 'default' }: StatCardProps) {
  return (
    <div className={`rounded-lg border p-4 ${variantStyles[variant]}`}>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-100">{value}</p>
    </div>
  );
}