import { ArrowDownTrayIcon, ArrowTopRightOnSquareIcon, MapIcon } from "@/components/icons";
import { ButtonLink, PageSection } from "@/components/ui/button";
import { MAP_PDF_DOWNLOAD_URL, MAP_PDF_FILENAME, MAP_PDF_OPEN_URL } from "@/lib/map-pdf-url";
import { PROJECT_REPO_URL } from "@/lib/project-repo";

const externalLinkClass =
  "font-medium text-blue-700 underline decoration-blue-400 underline-offset-2 hover:text-blue-900";

export function PdfViewer() {
  return (
    <PageSection title="County map (PDF)" icon={<MapIcon className="size-6 text-blue-700" />}>
      <p className="text-sm text-zinc-600">
        The full county map is hosted in the{" "}
        <a href={PROJECT_REPO_URL} target="_blank" rel="noopener noreferrer" className={externalLinkClass}>
          open-source project repository
        </a>
        . Other counties can fork it to run their own VSPC rebalancing. Open the map in your browser or download a
        copy.
      </p>
      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        <ButtonLink href={MAP_PDF_OPEN_URL} target="_blank" rel="noopener noreferrer" variant="secondary">
          <ArrowTopRightOnSquareIcon className="size-4" />
          Open county map (PDF)
          <span className="sr-only"> (opens in a new tab)</span>
        </ButtonLink>
        <ButtonLink href={MAP_PDF_DOWNLOAD_URL} download={MAP_PDF_FILENAME} variant="secondary">
          <ArrowDownTrayIcon className="size-4" />
          Download county map (PDF)
        </ButtonLink>
      </div>
    </PageSection>
  );
}
