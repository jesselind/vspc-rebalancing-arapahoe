import { CsvSection } from "@/components/csv-section";
import { FeedbackButton } from "@/components/feedback-button";
import { PdfViewer } from "@/components/pdf-viewer";
import { PrecinctLookup } from "@/components/precinct-lookup";
import { WhySection } from "@/components/why-section";
import { ButtonLink } from "@/components/ui/button";
import { loadDatasets, loadPrecinctAssignments } from "@/lib/data";
import { PROJECT_REPO_URL } from "@/lib/project-repo";

const GITHUB_ICON_SRC = "/GitHub_Invertocat_Black.svg";

async function loadHomeData() {
  try {
    const [datasets, assignmentsMap] = await Promise.all([loadDatasets(), loadPrecinctAssignments()]);
    return { datasets, assignments: Array.from(assignmentsMap.values()) };
  } catch {
    return null;
  }
}

export default async function Home() {
  const homeData = await loadHomeData();
  if (!homeData) {
    return (
      <div className="min-h-screen bg-zinc-100 p-6">
        <main id="main-content" className="mx-auto max-w-3xl rounded-xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
          <h1 className="text-2xl font-semibold text-amber-950">Data not prepared yet</h1>
          <p className="mt-2 text-sm text-amber-900">
            The server could not load CSV data from the deployed bundle. For local dev, run{" "}
            <code className="rounded bg-amber-100 px-1">npm run sync:assets</code> in{" "}
            <code className="rounded bg-amber-100 px-1">web/</code>, then rebuild and redeploy.
          </p>
        </main>
      </div>
    );
  }

  const { datasets, assignments } = homeData;

  return (
      <div className="flex min-h-screen flex-col bg-white">
        <header className="border-b border-blue-900 bg-blue-950 px-4 py-5 md:px-6">
          <div className="mx-auto max-w-7xl">
            <h1 className="text-2xl font-bold tracking-tight text-white md:text-3xl">
              Voter Service Polling Center (VSPC) Lookup
            </h1>
            <p className="mt-1 text-sm text-blue-200">Arapahoe County residents only</p>
          </div>
        </header>

        <main id="main-content" className="flex-1 px-4 py-6 md:px-6">
          <div className="mx-auto w-full max-w-7xl">
            <PrecinctLookup assignments={assignments} />
            <WhySection />
            <CsvSection datasets={datasets} />
            <PdfViewer />
          </div>
        </main>

        <footer className="bg-zinc-50 px-4 py-5 md:px-6">
          <div className="mx-auto flex max-w-7xl flex-col items-center gap-3 text-center">
            <p className="text-sm text-zinc-600">Open source. Fork and adapt the rebalancing tools for your county.</p>
            <ButtonLink href={PROJECT_REPO_URL} target="_blank" rel="noopener noreferrer" variant="secondary">
              <img src={GITHUB_ICON_SRC} alt="" width={16} height={16} className="size-4 shrink-0" />
              View project on GitHub
              <span className="sr-only"> (opens in a new tab)</span>
            </ButtonLink>
            <p className="text-sm text-zinc-600">Questions or incorrect data?</p>
            <FeedbackButton />
          </div>
        </footer>
      </div>
    );
}
