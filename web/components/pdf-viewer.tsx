import { ArrowDownTrayIcon, ArrowTopRightOnSquareIcon, MapIcon } from "@/components/icons";
import { ButtonLink, PageSection } from "@/components/ui/button";
import {
  COUNTY_ELECTION_PRECINCTS_URL,
  COUNTY_PRECINCT_MAP_PDF_URL,
} from "@/lib/county-map-links";
import { MAP_PDF_DOWNLOAD_URL, MAP_PDF_FILENAME, MAP_PDF_OPEN_URL } from "@/lib/map-pdf-url";
import { PROJECT_REPO_URL } from "@/lib/project-repo";

const externalLinkClass =
  "font-medium text-blue-700 underline decoration-blue-400 underline-offset-2 hover:text-blue-900";

const externalButtonProps = {
  target: "_blank" as const,
  rel: "noopener noreferrer" as const,
  variant: "secondary" as const,
};

export function PdfViewer() {
  return (
    <PageSection title="County map (PDF)" icon={<MapIcon className="size-6 text-blue-700" />}>
      <p className="text-sm text-zinc-600">
        This project hosts a{" "}
        <a href={PROJECT_REPO_URL} target="_blank" rel="noopener noreferrer" className={externalLinkClass}>
          rebalancing reference map
        </a>{" "}
        in the open-source repository for other counties to fork. Official Arapahoe County precinct maps are linked
        below.
      </p>

      <h3 className="mt-4 text-sm font-semibold text-zinc-900">VSPC rebalancing map (this project)</h3>
      <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        <ButtonLink href={MAP_PDF_OPEN_URL} target="_blank" rel="noopener noreferrer" variant="secondary">
          <ArrowTopRightOnSquareIcon className="size-4" />
          Open rebalancing map (PDF)
          <span className="sr-only"> (opens in a new tab)</span>
        </ButtonLink>
        <ButtonLink href={MAP_PDF_DOWNLOAD_URL} download={MAP_PDF_FILENAME} variant="secondary">
          <ArrowDownTrayIcon className="size-4" />
          Download rebalancing map (PDF)
        </ButtonLink>
      </div>

      <h3 className="mt-4 text-sm font-semibold text-zinc-900">Official county maps</h3>
      <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        <ButtonLink href={COUNTY_PRECINCT_MAP_PDF_URL} {...externalButtonProps}>
          <ArrowTopRightOnSquareIcon className="size-4" />
          County precinct map (PDF)
          <span className="sr-only"> (opens in a new tab, Arapahoe County)</span>
        </ButtonLink>
        <ButtonLink href={COUNTY_ELECTION_PRECINCTS_URL} {...externalButtonProps}>
          <ArrowTopRightOnSquareIcon className="size-4" />
          Individual precinct maps
          <span className="sr-only"> (opens in a new tab, Arapahoe County GIS)</span>
        </ButtonLink>
      </div>
    </PageSection>
  );
}
