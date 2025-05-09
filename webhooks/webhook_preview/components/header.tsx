import { Car } from "lucide-react";

export function Header() {
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-4">
      <div className="flex items-center space-x-4">
        <Car className="text-3xl text-gray-900" />
        <h1 className="text-2xl font-bold text-gray-900">
          Licence Plate Webhook Receiver
        </h1>
      </div>
    </div>
  );
}
