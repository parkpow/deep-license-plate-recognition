import { getBaseUrl } from "@/lib/utils";

interface EmptyStateProps {
  uuid: string;
}

export function EmptyState({ uuid }: EmptyStateProps) {
  return (
    <div className="bg-white rounded-lg shadow p-8 text-center">
      <h3 className="text-lg font-medium mb-2">No data yet</h3>
      <p className="text-gray-500 mb-4">
        Send data to your webhook URL to see license plate information here.
      </p>
      {/* <div className="text-sm bg-gray-50 p-4 rounded-md">
        <p className="font-mono">
          POST {getBaseUrl()}/api/webhook/{uuid}
        </p>
      </div> */}
    </div>
  );
}
