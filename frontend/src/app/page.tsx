export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2">
      <main className="flex flex-col items-center justify-center w-full flex-1 px-20 text-center">
        <h1 className="text-6xl font-bold text-blue-600 mb-4">ValueVerse</h1>
        <p className="text-2xl text-gray-700 mb-8">
          B2B Value Realization Operating System
        </p>
        <div className="flex flex-wrap items-center justify-around max-w-4xl mt-6 sm:w-full">
          <div className="p-6 mt-6 text-left border w-96 rounded-xl hover:text-blue-600 hover:border-blue-600">
            <h3 className="text-2xl font-bold">Frontend ✓</h3>
            <p className="mt-4 text-xl">
              Next.js 14 with TypeScript and Tailwind CSS
            </p>
          </div>

          <div className="p-6 mt-6 text-left border w-96 rounded-xl hover:text-blue-600 hover:border-blue-600">
            <h3 className="text-2xl font-bold">Backend ✓</h3>
            <p className="mt-4 text-xl">FastAPI with JWT authentication</p>
          </div>

          <div className="p-6 mt-6 text-left border w-96 rounded-xl hover:text-blue-600 hover:border-blue-600">
            <h3 className="text-2xl font-bold">Database ✓</h3>
            <p className="mt-4 text-xl">PostgreSQL 15 with Docker</p>
          </div>
        </div>

        <div className="mt-8">
          <a
            href="http://localhost:8000/docs"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            target="_blank"
            rel="noopener noreferrer"
          >
            View API Docs →
          </a>
        </div>
      </main>
    </div>
  );
}
