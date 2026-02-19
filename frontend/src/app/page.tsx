"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [apiStatus, setApiStatus] = useState<string>("checking...");

  useEffect(() => {
    fetch("http://localhost:8000/api/health")
      .then((res) => res.json())
      .then((data) => setApiStatus(data.status))
      .catch(() => setApiStatus("offline"));
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-col items-center gap-8">
        <h1 className="text-4xl font-bold text-black dark:text-white">
          AURA
        </h1>
        <p className="text-lg text-zinc-600 dark:text-zinc-400">
          FastAPI + Next.js
        </p>
        <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            API Status:{" "}
            <span
              className={
                apiStatus === "healthy"
                  ? "font-semibold text-green-600"
                  : "font-semibold text-red-500"
              }
            >
              {apiStatus}
            </span>
          </p>
        </div>
      </main>
    </div>
  );
}
