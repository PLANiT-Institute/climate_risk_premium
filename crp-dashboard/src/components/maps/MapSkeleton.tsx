export default function MapSkeleton() {
  return (
    <div className="h-[500px] w-full rounded-lg bg-gray-100 animate-pulse flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block w-8 h-8 border-4 border-gray-300 border-t-teal-500 rounded-full animate-spin mb-3"></div>
        <p className="text-gray-400">Loading map...</p>
      </div>
    </div>
  );
}
